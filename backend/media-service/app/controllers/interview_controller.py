import os
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, current_app
from dotenv import load_dotenv

from app.services.storage_service import StorageService
from db import UnitOfWork
from app.db.schema import media as media_table
from app.repositories.media_repository import MediaRepository
from sqlalchemy import select, update, desc
import app.utils.constants as CONSTANTS

load_dotenv()

interview_bp = Blueprint("interview", __name__)


# =========================================================
# 📄 RESUME & CANDIDATE MANAGEMENT (DB-backed)
# =========================================================

@interview_bp.route("/api/resumes/upload", methods=["POST"])
def upload_resume():
    """
    Upload a candidate's PDF resume into Azure/local storage,
    and persist metadata in media_files table.
    """
    file = request.files.get("file")
    candidate_name = request.form.get("candidate_name", "Unknown Candidate")
    assigned_user = request.form.get("assigned_user", "ashish")
    if not file:
        return jsonify({"error": "Missing file"}), 400
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    candidate_id = f"cand_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')[:17]}"
    safe_name = f"{candidate_id}_resume.pdf"

    try:
        with StorageService as storage:
            resume_uri = storage.upload_from_path(
                candidate_id,
                file.stream.name if hasattr(file, "stream") else file,
                safe_name,
                "application/pdf",
            )
    except Exception as e:
        current_app.logger.exception("Resume upload failed")
        return jsonify({"error": f"Upload failed: {e}"}), 500

    with UnitOfWork() as uow:
        repo = MediaRepository(uow)
        media_id = repo.insert_file(
            media_type="resume",
            interview_id=None,
            blob_name=f"resumes/{safe_name}",
            mime_type="application/pdf",
            status="uploaded",
            metadata={
                "candidate_name": candidate_name,
                "resume_url": resume_uri,
                "assigned_user": assigned_user,
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        row = uow.session.execute(
            select(media_table).where(media_table.c.id == media_id)
        ).mappings().one()

    return jsonify({
        "success": True,
        "data": dict(row),
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": candidate_id,
            "version": "1.0",
        },
    }), 200


@interview_bp.route("/api/candidates", methods=["GET"])
def get_all_candidates():
    """Return all candidate resumes."""
    with UnitOfWork() as uow:
        rows = uow.session.execute(
            select(media_table)
            .where(media_table.c.file_type == "resume")
            .order_by(desc(media_table.c.created_at))
        ).mappings().all()

    return jsonify({
        "success": True,
        "data": {"candidates": [dict(r) for r in rows], "count": len(rows)},
        "meta": {"timestamp": datetime.now(timezone.utc).isoformat()},
    }), 200


@interview_bp.route("/api/candidates/<candidate_id>", methods=["GET"])
def get_candidate(candidate_id):
    """Return a single candidate by ID."""
    with UnitOfWork() as uow:
        row = uow.session.execute(
            select(media_table)
            .where(media_table.c.file_type == "resume",
                   media_table.c.metadata["resume_url"].astext.like(f"%{candidate_id}%"))
            .limit(1)
        ).mappings().one_or_none()

    if not row:
        return jsonify({"error": "Candidate not found"}), 404

    return jsonify({
        "success": True,
        "data": dict(row),
        "meta": {"timestamp": datetime.now(timezone.utc).isoformat()},
    }), 200


# =========================================================
# 🧑‍💼 INTERVIEW MANAGEMENT
# =========================================================

@interview_bp.route("/api/candidates/<candidate_id>/schedule", methods=["POST"])
def schedule_candidate(candidate_id):
    """
    Schedule an interview for a candidate.
    """
    payload = request.get_json() or {}
    assigned_user = payload.get("assigned_user", "ashish")
    candidate_name = payload.get("candidate_name", "Unknown Candidate")

    interview_id = f"interview_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')[:20]}"

    with UnitOfWork() as uow:
        repo = MediaRepository(uow)
        new_id = repo.insert_file(
            media_type="interview",
            interview_id=interview_id,
            blob_name=None,
            mime_type=None,
            status="scheduled",
            metadata={
                "candidate_name": candidate_name,
                "candidate_id": candidate_id,
                "assigned_user": assigned_user,
                "scheduled_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        row = uow.session.execute(
            select(media_table).where(media_table.c.id == new_id)
        ).mappings().one()

    return jsonify({
        "success": True,
        "data": dict(row),
        "meta": {"timestamp": datetime.now(timezone.utc).isoformat()},
    }), 200


@interview_bp.route("/api/interviews", methods=["GET"])
def get_all_interviews():
    """Return all interviews."""
    with UnitOfWork() as uow:
        rows = uow.session.execute(
            select(media_table)
            .where(media_table.c.file_type == "interview")
            .order_by(desc(media_table.c.created_at))
        ).mappings().all()

    return jsonify({
        "success": True,
        "data": {"interviews": [dict(r) for r in rows], "count": len(rows)},
        "meta": {"timestamp": datetime.now(timezone.utc).isoformat()},
    }), 200


@interview_bp.route("/api/interviews/<interview_id>", methods=["GET"])
def get_interview(interview_id):
    """Get one interview."""
    with UnitOfWork() as uow:
        row = uow.session.execute(
            select(media_table)
            .where(media_table.c.file_type == "interview",
                   media_table.c.interview_id == interview_id)
            .limit(1)
        ).mappings().one_or_none()

    if not row:
        return jsonify({"error": CONSTANTS.ERROR_INTERVIEW_NOT_FOUND}), 404

    row_dict = dict(row)
    
    # Extract transcript and analysis from metadata if present
    metadata = row_dict.get("metadata", {}) or {}
    if isinstance(metadata, dict):
        # Move transcript and analysis to top level for frontend compatibility
        if "transcript" in metadata:
            row_dict["transcript"] = metadata["transcript"]
        if "analysis" in metadata:
            row_dict["analysis"] = metadata["analysis"]
        # Also include candidate info if present
        if "candidate_name" in metadata:
            row_dict["candidate_name"] = metadata["candidate_name"]
        if "candidate_email" in metadata:
            row_dict["candidate_email"] = metadata["candidate_email"]

    return jsonify({"success": True, "data": row_dict}), 200


@interview_bp.route("/api/interviews/<interview_id>/status", methods=["PATCH"])
def update_interview_status(interview_id):
    """Update status of interview."""
    data = request.get_json() or {}
    new_status = data.get("status")
    if not new_status:
        return jsonify({"error": "Missing status"}), 400

    with UnitOfWork() as uow:
        res = uow.session.execute(
            update(media_table)
            .where(media_table.c.file_type == "interview",
                   media_table.c.interview_id == interview_id)
            .values(status=new_status, updated_at=datetime.now(timezone.utc))
            .returning(media_table)
        ).mappings().one_or_none()

    if not res:
        return jsonify({"error": CONSTANTS.ERROR_INTERVIEW_NOT_FOUND}), 404

    return jsonify({"success": True, "data": dict(res)}), 200


@interview_bp.route("/api/interviews/<interview_id>/transcript", methods=["POST"])
def update_transcript(interview_id):
    """Update or insert transcript JSON."""
    payload = request.get_json() or {}

    with UnitOfWork() as uow:
        cur = uow.session.execute(
            select(media_table.c.id, media_table.c.metadata)
            .where(media_table.c.file_type == "interview",
                   media_table.c.interview_id == interview_id)
            .limit(1)
        ).mappings().one_or_none()

        if not cur:
            return jsonify({"error": CONSTANTS.ERROR_INTERVIEW_NOT_FOUND}), 404

        metadata = dict(cur["metadata"] or {})
        metadata["transcript"] = payload
        metadata["updated_at"] = datetime.now(timezone.utc).isoformat()

        row = uow.session.execute(
            update(media_table)
            .where(media_table.c.id == cur["id"])
            .values(metadata=metadata, updated_at=datetime.now(timezone.utc))
            .returning(media_table)
        ).mappings().one()

    return jsonify({"success": True, "data": dict(row)}), 200
