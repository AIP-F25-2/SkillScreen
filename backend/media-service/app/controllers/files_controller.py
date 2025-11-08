# app/controllers/files_controller.py

import os
import mimetypes
import tempfile
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, send_file

from app.services.storage_service import StorageService
from app.utils.filename import secure_part

from db import UnitOfWork
from app.repositories.media_repository import MediaRepository

files_bp = Blueprint("files", __name__)

# ------------------------------------------------------------------
# Upload any general file (stored under videos/<interview_id>/)
# ------------------------------------------------------------------
@files_bp.route("/files/upload", methods=["POST"])
def upload_general_file():
    file = request.files.get("file")
    interview_id = request.form.get("interview_id")

    if not file or not interview_id:
        return jsonify({"error": "Missing file or interview_id"}), 400

    original, ext = os.path.splitext(secure_part(file.filename or "file"))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = f"{original}_{timestamp}{ext}"

    guessed_ct, _ = mimetypes.guess_type(safe_name)
    content_type = guessed_ct or "application/octet-stream"

    # Store temporarily before pushing to storage backend
    try:
        with tempfile.NamedTemporaryFile(prefix="upload_", suffix=ext or "", delete=False) as tmp:
            file.stream.seek(0)
            tmp.write(file.stream.read())
            tmp_path = tmp.name

        StorageService.upload_from_path(
            secure_part(interview_id),
            tmp_path,
            safe_name,
            content_type=content_type,
        )
    finally:
        try:
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass

    # Build full Azure/local blob path
    db_blob_path = f"videos/{secure_part(interview_id)}/{safe_name}"

    # Persist DB metadata
    with UnitOfWork() as uow:
        repo = MediaRepository(uow)
        repo.insert_file(
            media_type="file",
            interview_id=str(interview_id),
            blob_name=db_blob_path,
            mime_type=content_type,
            status="uploaded",
            metadata={"source": "general-file-upload", "uploaded_at": datetime.now(timezone.utc).isoformat()},
        )

    return jsonify({
        "status": "file uploaded",
        "file_name": safe_name,
        "file_path": f"/file/{secure_part(interview_id)}/{safe_name}"
    }), 200


# ------------------------------------------------------------------
# Serve files from storage backend
# ------------------------------------------------------------------
@files_bp.route("/file/<interview_id>/<filename>")
def serve_general_file(interview_id, filename):
    interview_id = secure_part(interview_id)
    filename = secure_part(filename)

    guessed_ct, _ = mimetypes.guess_type(filename)
    mimetype = guessed_ct or "application/octet-stream"

    try:
        tmp_path = StorageService.download_to_temp(interview_id, filename)
    except Exception:
        return jsonify({"error": "file not found"}), 404

    return send_file(
        tmp_path,
        mimetype=mimetype,
        as_attachment=False,
        download_name=filename,
        conditional=True
    )
