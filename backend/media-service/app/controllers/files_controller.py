# app/controllers/files_controller.py
import os
import mimetypes
import tempfile
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from ..services.storage_service import StorageService
from ..utils.filename import secure_part

# ✨ DB wiring
from db import UnitOfWork
from app.repositories.media_repository import MediaRepository

files_bp = Blueprint("files", __name__)

@files_bp.route("/files/upload", methods=["POST"])
def upload_general_file():
    file = request.files.get("file")
    user_id = request.form.get("user_id")
    if not file or not user_id:
        return jsonify({"error": "Missing file or user_id"}), 400

    original, ext = os.path.splitext(secure_part(file.filename or "file"))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = f"{original}_{timestamp}{ext}"

    guessed_ct, _ = mimetypes.guess_type(safe_name)
    content_type = guessed_ct or "application/octet-stream"

    try:
        with tempfile.NamedTemporaryFile(prefix="upload_", suffix=ext or "", delete=False) as tmp:
            file.stream.seek(0)
            tmp.write(file.stream.read())
            tmp_path = tmp.name

        StorageService.upload_from_path(
            secure_part(user_id),
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

    db_blob_path = f"{secure_part(user_id)}/{safe_name}"
    with UnitOfWork() as uow:
        repo = MediaRepository(uow)
        repo.insert_file(
            user_id=str(user_id),
            file_name=safe_name,
            blob_path=db_blob_path,
            content_type=content_type,
            size_bytes=None,
            extra={"source": "admin-ui"},
        )

    return jsonify({
        "status": "file uploaded",
        "file_name": safe_name,
        "file_path": f"/file/{secure_part(user_id)}/{safe_name}"
    }), 200


@files_bp.route("/file/<user_id>/<filename>")
def serve_general_file(user_id, filename):
    user_id = secure_part(user_id)
    filename = secure_part(filename)

    guessed_ct, _ = mimetypes.guess_type(filename)
    mimetype = guessed_ct or "application/octet-stream"

    try:
        tmp_path = StorageService.download_to_temp(user_id, filename)
    except Exception:
        return jsonify({"error": "file not found"}), 404

    return send_file(
        tmp_path,
        mimetype=mimetype,
        as_attachment=False,
        download_name=filename,
        conditional=True
    )
