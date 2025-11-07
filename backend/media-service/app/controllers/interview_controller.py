import os
from datetime import datetime

from flask import Blueprint, request, jsonify, current_app
from dotenv import load_dotenv
from azure.storage.blob import ContainerClient, ContentSettings

# DB
from sqlalchemy import select, update, desc
from db import UnitOfWork
from app.db.schema import media as media_table
from app.repositories.media_repository import MediaRepository

load_dotenv()  # load environment variables from .env

interview_bp = Blueprint("interview", __name__)

# =========================================================
# 🔧 Azure helpers
# =========================================================
def _container_client() -> ContainerClient:
    """
    Expect AZURE_BLOB_CONTAINER_URL to be a full container SAS URL, e.g.:
    https://<acct>.blob.core.windows.net/<container>?sv=...&sp=rwlac...&sig=...
    """
    url = os.getenv("AZURE_BLOB_CONTAINER_URL")
    if not url:
        raise RuntimeError("AZURE_BLOB_CONTAINER_URL not configured")
    return ContainerClient.from_container_url(url)

def _resume_blob_name(candidate_id: str) -> str:
    # Keep a tidy prefix layout in the container
    return f"resumes/{candidate_id}/{candidate_id}_resume.pdf"


# =========================================================
# 📄 RESUME & CANDIDATE MANAGEMENT (DB-backed in `media`)
# =========================================================

@interview_bp.route("/api/resumes/upload", methods=["POST"])
def upload_resume():
    """
    Upload a PDF resume for a candidate (stores in Azure) and persist a row in `media`:
      media_type="resume", candidate_id, assigned_user, extra={candidate_name, resume_url, uploaded_at}
    """
    file = request.files.get("file")
    candidate_name = request.form.get("candidate_name", "Unknown Candidate")
    assigned_user = request.form.get("assigned_user", "ashish")  # keep your default
    user_id = request.form.get("user_id") or assigned_user       # optional linkage

    if not file:
        return jsonify({"error": "Missing file"}), 400
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    # Generate candidate ID
    candidate_id = f"cand_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')[:17]}"

    # Upload to Azure
    try:
        cc = _container_client()
        blob_name = _resume_blob_name(candidate_id)
        bc = cc.get_blob_client(blob=blob_name)
        stream = getattr(file, "stream", file)
        bc.upload_blob(
            stream,
            overwrite=True,
            content_settings=ContentSettings(content_type="application/pdf"),
        )
        resume_url = bc.url  # SAS is preserved from container URL
    except Exception as e:
        current_app.logger.exception("Azure upload failed")
        return jsonify({"error": f"Azure upload failed: {e}"}), 500

    # Persist to DB
    with UnitOfWork() as uow:
        repo = MediaRepository(uow)
        media_id = repo.insert_file(
            user_id=user_id,
            media_type="resume",
            file_name=os.path.basename(blob_name),  # kept for backward compatibility
            file_path=blob_name,
            blob_name=blob_name,
            content_type="application/pdf",
            status="uploaded",
            candidate_id=candidate_id,
            assigned_user=assigned_user,
            extra={
                "candidate_name": candidate_name,
                "resume_url": resume_url,
                "uploaded_at": datetime.utcnow().isoformat(),
            },
        )
        # return the inserted row
        row = uow.session.execute(
            select(media_table).where(media_table.c.id == media_id)
        ).mappings().one()
        # uow.commit()

    return jsonify({
        "success": True,
        "data": dict(row),
        "meta": {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": candidate_id,
            "version": "1.0",
        },
    }), 200


@interview_bp.route("/api/candidates", methods=["GET"])
def get_all_candidates():
    """Return all resumes from media (media_type='resume')."""
    with UnitOfWork() as uow:
        rows = uow.session.execute(
            select(media_table)
            .where(media_table.c.media_type == "resume")
            .order_by(desc(media_table.c.created_at))
        ).mappings().all()

    return jsonify({
        "success": True,
        "data": {
            "candidates": [dict(r) for r in rows],
            "count": len(rows),
        },
        "meta": {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": "req_" + datetime.utcnow().strftime('%Y%m%d%H%M%S'),
            "version": "1.0",
        },
    }), 200


@interview_bp.route("/api/candidates/user/<user_id>", methods=["GET"])
def get_user_candidates(user_id):
    """Return resumes assigned to a specific user from media."""
    with UnitOfWork() as uow:
        rows = uow.session.execute(
            select(media_table)
            .where(
                media_table.c.media_type == "resume",
                media_table.c.assigned_user == user_id
            )
            .order_by(desc(media_table.c.created_at))
        ).mappings().all()

    return jsonify({
        "success": True,
        "data": {
            "candidates": [dict(r) for r in rows],
            "count": len(rows),
        },
        "meta": {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": "req_" + datetime.utcnow().strftime('%Y%m%d%H%M%S'),
            "version": "1.0",
        },
    }), 200


@interview_bp.route("/api/candidates/<candidate_id>", methods=["GET"])
def get_candidate(candidate_id):
    """Get a specific candidate by candidate_id from media (resume row)."""
    with UnitOfWork() as uow:
        row = uow.session.execute(
            select(media_table)
            .where(
                media_table.c.media_type == "resume",
                media_table.c.candidate_id == candidate_id
            )
            .limit(1)
        ).mappings().one_or_none()

    if not row:
        return jsonify({"error": "Candidate not found"}), 404

    return jsonify({
        "success": True,
        "data": dict(row),
        "meta": {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": candidate_id,
            "version": "1.0",
        },
    }), 200


@interview_bp.route("/api/candidates/<candidate_id>/schedule", methods=["POST"])
def schedule_candidate(candidate_id):
    """
    Create an interview row in media:
      media_type="interview", interview_id, candidate_id, assigned_user, status="scheduled"
    """
    payload = request.get_json() or {}
    assigned_user = payload.get("assigned_user", "ashish")

    # Fetch candidate to carry over name, etc.
    with UnitOfWork() as uow:
        cand = uow.session.execute(
            select(media_table)
            .where(
                media_table.c.media_type == "resume",
                media_table.c.candidate_id == candidate_id
            )
            .limit(1)
        ).mappings().one_or_none()

        if not cand:
            return jsonify({"error": "Candidate not found"}), 404

        candidate_name = (cand.get("extra") or {}).get("candidate_name") or "Unknown Candidate"

        interview_id = f"interview_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')[:20]}"

        repo = MediaRepository(uow)
        new_id = repo.insert_file(
            user_id=cand.get("user_id"),
            file_name="",  # kept for backward compatibility
            blob_path="",
            content_type=None,
            status="scheduled",
            candidate_id=candidate_id,
            interview_id=interview_id,
            assigned_user=assigned_user,
            extra={
                "candidate_name": candidate_name,
                "scheduled_at": datetime.utcnow().isoformat(),
                "created_at": datetime.utcnow().isoformat(),
            },
        )

        row = uow.session.execute(
            select(media_table).where(media_table.c.id == new_id)
        ).mappings().one()
        # uow.commit()

    return jsonify({
        "success": True,
        "data": dict(row),
        "meta": {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": interview_id,
            "version": "1.0",
        },
    }), 200


@interview_bp.route("/api/interviews", methods=["GET"])
def get_all_interviews():
    """Return all interviews from media (media_type='interview')."""
    with UnitOfWork() as uow:
        rows = uow.session.execute(
            select(media_table)
            .where(media_table.c.media_type == "interview")
            .order_by(desc(media_table.c.created_at))
        ).mappings().all()

    return jsonify({
        "success": True,
        "data": {
            "interviews": [dict(r) for r in rows],
            "count": len(rows),
        },
        "meta": {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": "req_" + datetime.utcnow().strftime('%Y%m%d%H%M%S'),
            "version": "1.0",
        },
    }), 200


@interview_bp.route("/api/interviews/<interview_id>", methods=["GET"])
def get_interview_details(interview_id):
    """Get a specific interview by interview_id from media."""
    with UnitOfWork() as uow:
        row = uow.session.execute(
            select(media_table)
            .where(
                media_table.c.media_type == "interview",
                media_table.c.interview_id == interview_id
            )
            .limit(1)
        ).mappings().one_or_none()

    if not row:
        return jsonify({"error": "Interview not found"}), 404

    return jsonify({
        "success": True,
        "data": dict(row),
        "meta": {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": interview_id,
            "version": "1.0",
        },
    }), 200


@interview_bp.route("/api/interviews/<interview_id>/status", methods=["PATCH"])
def update_interview_status(interview_id):
    """Update interview status in media."""
    data = request.get_json() or {}
    status = data.get("status")
    if not status:
        return jsonify({"error": "Missing status"}), 400

    with UnitOfWork() as uow:
        res = uow.session.execute(
            update(media_table)
            .where(
                media_table.c.media_type == "interview",
                media_table.c.interview_id == interview_id
            )
            .values(status=status, updated_at=datetime.utcnow())
            .returning(media_table)
        )
        row = res.mappings().one_or_none()
        if not row:
            return jsonify({"error": "Interview not found"}), 404
        # uow.commit()

    return jsonify({
        "success": True,
        "data": dict(row),
        "meta": {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": interview_id,
            "version": "1.0",
        },
    }), 200


@interview_bp.route("/api/interviews/<interview_id>/transcript", methods=["POST"])
def update_interview_transcript(interview_id):
    """Merge/update transcript into the interview's extra JSON."""
    payload = request.get_json() or {}

    with UnitOfWork() as uow:
        cur = uow.session.execute(
            select(media_table.c.id, media_table.c.extra)
            .where(
                media_table.c.media_type == "interview",
                media_table.c.interview_id == interview_id
            )
            .limit(1)
        ).mappings().one_or_none()

        if not cur:
            return jsonify({"error": "Interview not found"}), 404

        extra = dict(cur["extra"] or {})
        extra["transcript"] = payload
        extra["updated_at"] = datetime.utcnow().isoformat()

        res = uow.session.execute(
            update(media_table)
            .where(media_table.c.id == cur["id"])
            .values(extra=extra, updated_at=datetime.utcnow())
            .returning(media_table)
        )
        row = res.mappings().one()
        # uow.commit()

    return jsonify({
        "success": True,
        "data": dict(row),
        "meta": {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": interview_id,
            "version": "1.0",
        },
    }), 200


@interview_bp.route("/api/interviews/user/<user_id>", methods=["GET"])
def get_user_interviews(user_id):
    """List interviews assigned to a user (from media.assigned_user)."""
    with UnitOfWork() as uow:
        rows = uow.session.execute(
            select(media_table)
            .where(
                media_table.c.media_type == "interview",
                media_table.c.assigned_user == user_id
            )
            .order_by(desc(media_table.c.created_at))
        ).mappings().all()

    return jsonify({
        "success": True,
        "data": {
            "interviews": [dict(r) for r in rows],
            "count": len(rows),
        },
        "meta": {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": "req_" + datetime.utcnow().strftime('%Y%m%d%H%M%S'),
            "version": "1.0",
        },
    }), 200
