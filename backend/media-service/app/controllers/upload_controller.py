import os, tempfile, hashlib, time
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, send_file, current_app
from sqlalchemy import text, select
from app.services.storage_service import StorageService
from app.repositories.media_repository import MediaRepository
from db import UnitOfWork
from app.db.schema import media
from app.utils.filename import secure_part
from typing import Optional
from app.utils.ids import require_uuid_str
import app.utils.constants as CONSTANTS
upload_bp = Blueprint("upload", __name__)
storage_service = StorageService()


def _server_chunk_name(idx_zero_based: int) -> str:
    return f"chunk-{idx_zero_based + 1:05d}.webm"


def _get_session_id(src: dict, *, required: bool = True) -> Optional[str]:
    sid = src.get("session_id") if hasattr(src, "get") else None
    if not sid:
        if required:
            raise ValueError("session_id is required")
        return None
    return require_uuid_str(str(sid), "session_id")


# ---------------------------------------------------------------------------
#  /upload/init  → initialize upload row in DB
# ---------------------------------------------------------------------------
@upload_bp.route("/upload/init", methods=["POST"])
def upload_init():
    data = request.get_json() or {}
    interview_id = data.get("interview_id")
    total_chunks = data.get("total_chunks")
    try:
        session_id = _get_session_id(data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if not interview_id or total_chunks is None:
        return jsonify({"error": "Missing interview_id or total_chunks"}), 400

    with UnitOfWork() as uow:
        repo = MediaRepository(uow)
        # Abort any previous unfinished uploads for this session
        uow.session.execute(
            text("""
                UPDATE media_files
                   SET status='aborted', updated_at=NOW()
                 WHERE interview_id = :iid
                   AND session_id = CAST(:sid AS uuid)
                   AND status != 'completed'
            """),
            {"iid": interview_id, "sid": session_id}
        )

        # Create a fresh upload entry
        media_id = repo.create_recording_video(
            interview_id=interview_id,
            session_id=session_id,
            expected_total=int(total_chunks)
        )
        uow.session.commit()

    return jsonify({
        "status": "initialized",
        "total_chunks": int(total_chunks),
        "session_id": session_id,
        "db_id": str(media_id)
    }), 200


# ---------------------------------------------------------------------------
#  /upload_chunk  → receive and store each chunk
# ---------------------------------------------------------------------------
@upload_bp.route("/upload_chunk", methods=["POST"])
def upload_chunk():
    file = request.files.get("file")
    interview_id = request.form.get("interview_id")
    chunk_index = request.form.get("chunk_index", type=int)
    total_chunks = request.form.get("total_chunks", type=int)
    try:
        session_id = _get_session_id(request.form)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if not file or not interview_id or chunk_index is None:
        return jsonify({"error": "Missing file, interview_id, or chunk_index"}), 400


    data = f"{interview_id}{session_id}{time.time()}".encode()
    short_hash = hashlib.sha256(data).hexdigest()[:8]  # longer but safe
    blob_name = f"{interview_id}_{short_hash}_recording.webm"
    server_filename = _server_chunk_name(chunk_index)

    try:
        # Save chunk
        storage_service.save_chunk(
            interview_id=interview_id,
            blob_name=blob_name,
            chunk_index=chunk_index,
            data=file.read()
        )

        with UnitOfWork() as uow:
            repo = MediaRepository(uow)
            # Get active "uploading" record
            status = repo.get_latest_active_record(interview_id, session_id)
            if not status:
                repo.create_recording_video(interview_id, session_id, expected_total=total_chunks)
                uow.session.commit()
                status = repo.get_latest_active_record(interview_id, session_id)

            record_id = status.get("id")
            repo.mark_chunk_received_by_id(record_id, chunk_index, total_chunks)
            status = repo.get_latest_active_record(interview_id, session_id)
            uow.session.commit()

        received = set(status.get("received_indices") or [])
        expected_total = status.get("expected_total") or total_chunks

        # Merge when all chunks received
        if expected_total and len(received) == expected_total:
            current_app.logger.info(
                "All chunks received and merging started.",
                extra={
                    "expected_total": expected_total,
                    "interview_id": str(interview_id),
                    "session_id": str(session_id),
                },
            )
            final_path, final_uri = storage_service.merge_chunks(interview_id, blob_name, expected_total)

            checksum = size = None
            if final_path and os.path.exists(final_path):
                size = os.path.getsize(final_path)
                
                with open(final_path, "rb") as f:
                    file_data = f.read()
                    checksum = hashlib.sha256(file_data).hexdigest()

            with UnitOfWork() as uow2:
                repo2 = MediaRepository(uow2)
                repo2.finalize_upload_by_id(
                    record_id=record_id,
                    storage_uri=final_uri,
                    file_size=size,
                    checksum=checksum,
                    blob_name=blob_name.replace(".webm", ".mp4"),
                    file_type="video",
                    mime_type=CONSTANTS.VIDEO_WEBM_FORMAT
                )
                uow2.session.commit()

            return jsonify({
                "status": "completed",
                "storage_uri": final_uri,
                "file_size": size,
                "checksum": checksum,
            }), 200

    except Exception as e:
        current_app.logger.exception("upload_chunk failed")
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "status": "chunk saved",
        "idx": chunk_index,
        "name": server_filename,
        "session_id": session_id
    }), 200


# ---------------------------------------------------------------------------
#  /reset_chunks  → abort current recording and clean up
# ---------------------------------------------------------------------------
@upload_bp.route("/reset_chunks", methods=["POST"])
def reset_chunks():
    data = request.get_json(silent=True) or {}
    interview_id = data.get("interview_id")
    try:
        session_id = _get_session_id(data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if not interview_id:
        return jsonify({"error": CONSTANTS.ERROR_MISSING_INTERVIEW_ID}), 400

    try:
        storage_service.delete_folder(f"videos/{interview_id}/chunks")
    except Exception:
        current_app.logger.warning("reset_chunks: storage cleanup failed", exc_info=True)

    with UnitOfWork() as uow:
        repo = MediaRepository(uow)
        # Abort all old unfinished uploads
        uow.session.execute(
            text("""
                UPDATE media_files
                   SET status='aborted', updated_at=NOW()
                 WHERE interview_id = :iid
                   AND session_id = CAST(:sid AS uuid)
                   AND status != 'completed'
            """),
            {"iid": interview_id, "sid": session_id}
        )
        # Create new active upload record
        repo.create_recording_video(interview_id, session_id, expected_total=None)
        uow.session.commit()

    return jsonify({"status": "reset complete", "session_id": session_id}), 200


# ---------------------------------------------------------------------------
#  /finalize_upload  → manual merge trigger
# ---------------------------------------------------------------------------
@upload_bp.route("/finalize_upload", methods=["POST"])
def finalize_upload():
    data = request.get_json() or {}
    interview_id = data.get("interview_id")
    try:
        session_id = _get_session_id(data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    if not interview_id:
        return jsonify({"error": CONSTANTS.ERROR_MISSING_INTERVIEW_ID}), 400

    with UnitOfWork() as uow:
        repo = MediaRepository(uow)
        status = repo.get_latest_active_record(interview_id, session_id)

    if not status:
        return jsonify({"error": "No active upload found"}), 400

    received = set(status.get("received_indices") or [])
    expected_total = status.get("expected_total") or len(received)
    missing = [i for i in range(expected_total) if i not in received]
    if missing:
        return jsonify({"error": "Missing chunks", "missing": missing}), 409

    record_id = status.get("id")
    data = f"{interview_id}{session_id}{time.time()}".encode()
    short_hash = hashlib.sha256(data).hexdigest()[:8]  # slightly longer but secure
    blob_name = f"{interview_id}_{short_hash}_recording.webm"


    try:
        final_path, final_uri = storage_service.merge_chunks(interview_id, blob_name, expected_total)
    except Exception as e:
        current_app.logger.exception("Merge failed during finalize_upload")
        return jsonify({"error": f"Merge failed: {str(e)}"}), 500

    checksum = size = None
    if final_path and os.path.exists(final_path):
        try:
            size = os.path.getsize(final_path)
            with open(final_path, "rb") as f:
                checksum = hashlib.sha256(f.read()).hexdigest()  # ✅ Secure replacement
        except Exception as e:
            current_app.logger.warning(f"Checksum failed: {e}")


    with UnitOfWork() as uow2:
        repo2 = MediaRepository(uow2)
        repo2.finalize_upload_by_id(
            record_id=record_id,
            storage_uri=final_uri,
            file_size=size,
            checksum=checksum,
            blob_name=blob_name.replace(".webm", "_merged.mp4"),
            file_type="video",
            mime_type=CONSTANTS.VIDEO_WEBM_FORMAT
        )
        uow2.session.commit()

    return jsonify({
        "status": "completed",
        "storage_uri": final_uri,
        "file_size": size,
        "checksum": checksum
    }), 200


# ---------------------------------------------------------------------------
#  Serve & status endpoints
# ---------------------------------------------------------------------------
@upload_bp.route("/video/<interview_id>/<session_id>", methods=["GET"])
def serve_video_by_session(interview_id, session_id):
    """Retrieve video response for a specific question (session) in an interview."""
    interview_id = secure_part(interview_id)
    try:
        session_id = require_uuid_str(str(session_id), "session_id")
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        with UnitOfWork() as uow:
            result = uow.session.execute(
                text("""
                    SELECT blob_name FROM media_files
                    WHERE interview_id = :iid
                    AND session_id = CAST(:sid AS uuid)
                    AND file_type = 'video_response'
                    LIMIT 1
                """),
                {"iid": interview_id, "sid": session_id}
            ).mappings().first()

        if not result:
            return jsonify({"error": "video not found"}), 404

        blob_name = result.get("blob_name")
        tmp_path = storage_service.download_to_temp(interview_id, blob_name)
    except Exception as e:
        current_app.logger.exception("serve_video_by_session failed")
        return jsonify({"error": "file not found"}), 404

    ext = os.path.splitext(blob_name)[1].lower()
    mimetype = "video/mp4" if ext == ".mp4" else CONSTANTS.VIDEO_WEBM_FORMAT
    return send_file(tmp_path, mimetype=mimetype, as_attachment=False, download_name=blob_name, conditional=True)


@upload_bp.route("/video/<interview_id>/<filename>")
def serve_video(interview_id, filename):
    interview_id = secure_part(interview_id)
    filename = secure_part(filename)
    try:
        tmp_path = storage_service.download_to_temp(interview_id, filename)
    except Exception:
        return jsonify({"error": "file not found"}), 404
    ext = os.path.splitext(filename)[1].lower()
    mimetype = "video/mp4" if ext == ".mp4" else CONSTANTS.VIDEO_WEBM_FORMAT
    return send_file(tmp_path, mimetype=mimetype, as_attachment=False, download_name=filename, conditional=True)


@upload_bp.route("/chunks/status", methods=["GET"])
def chunks_status():
    interview_id = request.args.get("interview_id")
    raw_session = request.args.get("session_id") or request.args.get("sid")
    session_id = None
    if raw_session:
        try:
            session_id = _get_session_id({"session_id": raw_session})
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
    if not interview_id:
        return jsonify({"error": CONSTANTS.ERROR_MISSING_INTERVIEW_ID}), 400

    with UnitOfWork() as uow:
        repo = MediaRepository(uow)
        if not session_id:
            latest = uow.session.execute(
                select(media.c.session_id)
                .where(media.c.interview_id == interview_id)
                .order_by(media.c.created_at.desc())
                .limit(1)
            ).scalar_one_or_none()
            session_id = str(latest) if latest else None
        if not session_id:
            return jsonify({"expected_total": 0, "received": [], "missing": [], "status": "idle"}), 200
        status = repo.get_latest_active_record(interview_id, session_id)
        if not status:
            return jsonify({"expected_total": 0, "received": [], "missing": [], "status": "idle"}), 200
        received = set(status.get("received_indices") or [])
        expected_total = status.get("expected_total") or 0
        missing = [i for i in range(expected_total) if i not in received]
        return jsonify({
            "session_id": session_id,
            "expected_total": expected_total,
            "received_indices": list(received),
            "missing": missing,
            "status": status.get("status", "uploading")
        }), 200


# ---------------------------------------------------------------------------
#  /upload/video  → Direct video upload (single file, no chunking)
# ---------------------------------------------------------------------------
@upload_bp.route("/upload/video", methods=["POST"])
def upload_video():
    """
    Direct upload of candidate video response.

    Request:
    - interview_id (form): UUID of interview
    - session_id (form): UUID of session/question
    - file (file): Video file (webm, mp4, etc.)

    Returns:
    - storage_uri: URL to access video
    - file_id: ID in media_files table
    - file_size: Size in bytes
    """
    interview_id = request.form.get("interview_id")
    raw_session = request.form.get("session_id")
    file = request.files.get("file")

    # Validate inputs
    if not interview_id:
        return jsonify({"error": "Missing interview_id"}), 400
    if not raw_session:
        return jsonify({"error": "Missing session_id"}), 400
    if not file or not file.filename:
        return jsonify({"error": "Missing video file"}), 400

    # Validate session_id is UUID
    try:
        session_id = _get_session_id({"session_id": raw_session})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        # Read file data
        file_data = file.read()
        file_size = len(file_data)

        # Calculate checksum
        checksum = hashlib.sha256(file_data).hexdigest()

        # Generate filename
        timestamp = time.time()
        data_for_hash = f"{interview_id}{session_id}{timestamp}".encode()
        short_hash = hashlib.sha256(data_for_hash).hexdigest()[:8]

        # Get original extension
        orig_name = secure_part(file.filename)
        ext = os.path.splitext(orig_name)[1] or ".webm"
        blob_name = f"{interview_id}_{short_hash}_response{ext}"

        # Save to temporary file first
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(file_data)
            tmp_path = tmp.name

        try:
            # Save to storage
            current_app.logger.info(f"Uploading video: {blob_name} (size: {file_size} bytes)")
            storage_uri = storage_service.upload_from_path(
                interview_id=interview_id,
                local_path=tmp_path,
                dest_filename=blob_name,
                content_type=file.content_type or "video/webm"
            )
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        # Save metadata to database
        with UnitOfWork() as uow:
            repo = MediaRepository(uow)
            # Store session-based URI for easier retrieval
            session_uri = f"/video/{interview_id}/{session_id}"
            media_id = repo.insert_file(
                media_type="video_response",
                interview_id=interview_id,
                session_id=session_id,
                blob_name=blob_name,
                storage_uri=session_uri,
                mime_type=file.content_type or "video/webm",
                status="completed",
                metadata={
                    "uploaded_at": datetime.now(timezone.utc).isoformat(),
                    "filename": blob_name,
                    "checksum": checksum
                }
            )
            row = uow.session.execute(
                select(media).where(media.c.id == media_id)
            ).mappings().one()

        return jsonify({
            "success": True,
            "data": {
                "file_id": str(row["id"]),
                "interview_id": interview_id,
                "session_id": session_id,
                "storage_uri": session_uri,
                "file_size": file_size,
                "checksum": checksum,
                "blob_name": blob_name,
                "status": "completed"
            }
        }), 200

    except Exception as e:
        current_app.logger.exception("Video upload failed")
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500
