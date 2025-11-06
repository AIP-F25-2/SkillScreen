# app/controllers/admin_controller.py
import mimetypes
from flask import Blueprint, request, jsonify, redirect, current_app
from ..services.storage_service import StorageService
from ..utils.filename import secure_part
from urllib.parse import urlsplit, urlunsplit, quote

admin_bp = Blueprint("admin", __name__)

def _build_blob_url(container_url: str, blob_name: str) -> str:
    u = urlsplit(container_url)
    parts = [p for p in blob_name.split("/") if p]
    encoded_path = "/".join(quote(p, safe="~()*!.'") for p in parts)
    new_path = (u.path.rstrip("/") + "/" + encoded_path).replace("//", "/")
    return urlunsplit((u.scheme, u.netloc, new_path, u.query, u.fragment))

@admin_bp.route("/videos", methods=["GET"])
def get_all_videos():
    out = {}
    for user in StorageService.list_users():
        vids = StorageService.list_files(user, include_exts=[".mp4"])
        if vids:
            out[user] = vids
    return jsonify(out), 200

@admin_bp.route("/videos/<user_id>", methods=["GET"])
def get_user_videos(user_id):
    user_id = secure_part(user_id)
    vids = StorageService.list_files(user_id, include_exts=[".mp4"]) or []
    return jsonify({"user": user_id, "videos": vids}), 200

@admin_bp.route("/video/<user_id>/<filename>", methods=["DELETE"])
def delete_video(user_id, filename):
    ok = StorageService.delete_file(user_id, filename)
    if ok:
        return jsonify({"status": "deleted", "file": secure_part(filename)}), 200
    return jsonify({"error": "file not found"}), 404

@admin_bp.route("/videos/<user_id>", methods=["DELETE"])
def delete_user_videos(user_id):
    deleted = StorageService.delete_all(user_id, include_exts=[".mp4"])
    return jsonify({"status": "deleted", "deleted_files": deleted}), 200

@admin_bp.route("/videos", methods=["DELETE"])
def delete_all_videos():
    out = {}
    for user in StorageService.list_users():
        out[user] = StorageService.delete_all(user, include_exts=[".mp4"])
    return jsonify({"status": "deleted all videos", "deleted_files": out}), 200

@admin_bp.route("/video/<user_id>/preview/<filename>", methods=["GET"])
def admin_preview_video(user_id, filename):
    user_id = secure_part(user_id); filename = secure_part(filename)
    container_url = current_app.config.get("AZURE_BLOB_CONTAINER_URL")
    blob_url = _build_blob_url(container_url, f"{user_id}/{filename}")
    return redirect(blob_url, code=302)

@admin_bp.route("/search/users", methods=["GET"])
def search_users():
    q = (request.args.get("q") or "").lower()
    matches = [u for u in StorageService.list_users() if q in u.lower()]
    return jsonify({"query": q, "matched_users": matches}), 200

@admin_bp.route("/search/videos", methods=["GET"])
def search_videos():
    q = (request.args.get("q") or "").lower()
    out = {}
    for u in StorageService.list_users():
        vids = [f for f in StorageService.list_files(u, include_exts=[".mp4"]) if q in f.lower()]
        if vids:
            out[u] = vids
    return jsonify({"query": q, "matched_videos": out}), 200

@admin_bp.route("/files", methods=["GET"])
def get_all_files():
    out = {}
    for u in StorageService.list_users():
        files = StorageService.list_files(u, exclude_exts=[".mp4", ".webm"])
        if files:
            out[u] = files
    return jsonify(out), 200

@admin_bp.route("/files/<user_id>", methods=["GET"])
def get_user_files(user_id):
    user_id = secure_part(user_id)
    files = StorageService.list_files(user_id, exclude_exts=[".mp4", ".webm"]) or []
    return jsonify({"user": user_id, "files": files}), 200

@admin_bp.route("/file/<user_id>/<filename>", methods=["DELETE"])
def delete_user_file(user_id, filename):
    ok = StorageService.delete_file(user_id, filename)
    if ok:
        return jsonify({"status": "deleted", "file": secure_part(filename)}), 200
    return jsonify({"error": "file not found"}), 404

@admin_bp.route("/files/<user_id>", methods=["DELETE"])
def delete_all_user_files(user_id):
    deleted = StorageService.delete_all(user_id, exclude_exts=[".mp4", ".webm"])
    return jsonify({"status": "deleted", "deleted_files": deleted}), 200

@admin_bp.route("/files", methods=["DELETE"])
def delete_all_general_files():
    out = {}
    for u in StorageService.list_users():
        out[u] = StorageService.delete_all(u, exclude_exts=[".mp4", ".webm"])
    return jsonify({"status": "deleted all general files", "deleted_files": out}), 200

@admin_bp.route("/search/files", methods=["GET"])
def search_files():
    q = (request.args.get("q") or "").lower()
    out = {}
    for u in StorageService.list_users():
        files = [
            f for f in StorageService.list_files(u, exclude_exts=[".mp4", ".webm"])
            if q in f.lower()
        ]
        if files:
            out[u] = files
    return jsonify({"query": q, "matched_files": out}), 200

@admin_bp.route("/file/<user_id>/preview/<filename>", methods=["GET"])
def admin_preview_file(user_id, filename):
    user_id = secure_part(user_id); filename = secure_part(filename)
    container_url = current_app.config.get("AZURE_BLOB_CONTAINER_URL")
    blob_url = _build_blob_url(container_url, f"{user_id}/{filename}")
    return redirect(blob_url, code=302)

@admin_bp.route("/user", methods=["POST"])
def create_user():
    data = request.get_json() or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
    from ..services.user_service import create_user as _create
    created = _create(user_id)
    if created:
        return jsonify({"status": "user created", "user_id": secure_part(user_id)}), 201
    return jsonify({"status": "user already exists"}), 200

@admin_bp.route("/users", methods=["GET"])
def get_all_users():
    return jsonify({"users": StorageService.list_users()}), 200

@admin_bp.route("/user/<user_id>", methods=["GET"])
def get_user(user_id):
    user_id = secure_part(user_id)
    users = set(StorageService.list_users())
    if user_id not in users:
        files = StorageService.list_files(user_id) or []
        if not files:
            return jsonify({"error": "user not found"}), 404
        vids = [f for f in files if f.lower().endswith(".mp4")]
        return jsonify({"user_id": user_id, "videos": vids}), 200

    vids = StorageService.list_files(user_id, include_exts=[".mp4"]) or []
    return jsonify({"user_id": user_id, "videos": vids}), 200

@admin_bp.route("/user/<user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.get_json() or {}
    new_user_id = data.get("new_user_id")
    if not new_user_id:
        return jsonify({"error": "Missing new_user_id"}), 400

    old_user = secure_part(user_id)
    new_user = secure_part(new_user_id)

    if new_user in set(StorageService.list_users()):
        return jsonify({"error": "new user_id already exists"}), 400

    files = StorageService.list_files(old_user) or []
    if not files:
        return jsonify({"error": "user not found or no files"}), 404

    moved, failed = [], []
    for fname in files:
        try:
            tmp_path = StorageService.download_to_temp(old_user, fname)
            ctype = mimetypes.guess_type(fname)[0] or "application/octet-stream"
            StorageService.upload_from_path(new_user, tmp_path, fname, content_type=ctype)
            StorageService.delete_file(old_user, fname)
            moved.append(fname)
        except Exception as e:
            failed.append({"file": fname, "error": str(e)})

    if moved and not failed:
        try:
            StorageService.delete_user(old_user)
        except Exception:
            pass

    return jsonify({
        "status": "user renamed",
        "old_user_id": old_user,
        "new_user_id": new_user,
        "moved_files": moved,
        "failed": failed
    }), 200

@admin_bp.route("/user/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    ok = StorageService.delete_user(user_id)
    if ok:
        return jsonify({"status": "user deleted", "user_id": secure_part(user_id)}), 200
    return jsonify({"error": "user not found"}), 404

@admin_bp.route("/users", methods=["DELETE"])
def delete_all_users():
    deleted = StorageService.delete_all_users()
    return jsonify({"status": "deleted all users", "deleted_users": deleted}), 200
