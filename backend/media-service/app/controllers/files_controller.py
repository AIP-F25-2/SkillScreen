import os
from datetime import datetime
from flask import Blueprint, request, jsonify, send_from_directory
from ..services.storage_service import StorageService
from ..utils.filename import secure_part

files_bp = Blueprint("files", __name__)

@files_bp.route("/upload_general_file", methods=["POST"])
def upload_general_file():
    file = request.files.get("file")
    user_id = request.form.get("user_id")
    if not file or not user_id:
        return jsonify({"error": "Missing file or user_id"}), 400

    folder = StorageService.user_folder(user_id)
    original, ext = os.path.splitext(secure_part(file.filename))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = f"{original}_{timestamp}{ext}"
    file.save(os.path.join(folder, safe_name))

    return jsonify({"status": "file uploaded", "file_name": safe_name, "file_path": f"/{secure_part(user_id)}/{safe_name}"}), 200

@files_bp.route("/file/<user_id>/<filename>")
def serve_general_file(user_id, filename):
    user_id = secure_part(user_id)
    filename = secure_part(filename)
    folder = StorageService.user_folder(user_id)
    path = os.path.join(folder, filename)
    if not os.path.isfile(path):
        return jsonify({"error": "file not found"}), 404
    return send_from_directory(folder, filename, conditional=True)
