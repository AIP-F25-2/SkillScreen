# app/controllers/admin_controller.py
import os
from flask import Blueprint, request, jsonify, current_app, redirect
from ..services.storage_service import StorageService
from ..utils.filename import secure_part

admin_bp = Blueprint("admin", __name__)

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
    vids = StorageService.list_files(user_id, include_exts=[".mp4"]) or []
    return jsonify({"user": secure_part(user_id), "videos": vids}), 200

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
    return redirect(f"/video/{secure_part(user_id)}/{secure_part(filename)}", code=302)

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
    files = StorageService.list_files(user_id, exclude_exts=[".mp4", ".webm"]) or []
    return jsonify({"user": secure_part(user_id), "files": files}), 200

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

# 🔎 NEW: search general files across all users
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

# 👀 NEW: preview any general file (redirects to /file/<user_id>/<filename>)
@admin_bp.route("/file/<user_id>/preview/<filename>", methods=["GET"])
def admin_preview_file(user_id, filename):
    return redirect(f"/file/{secure_part(user_id)}/{secure_part(filename)}", code=302)

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
    from os.path import isdir
    folder = StorageService.user_folder(user_id)
    if isdir(folder):
        vids = StorageService.list_files(user_id, include_exts=[".mp4"]) or []
        return jsonify({"user_id": secure_part(user_id), "videos": vids}), 200
    return jsonify({"error": "user not found"}), 404

@admin_bp.route("/user/<user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.get_json() or {}
    new_user_id = data.get("new_user_id")
    if not new_user_id:
        return jsonify({"error": "Missing new_user_id"}), 400

    base = current_app.config["UPLOAD_FOLDER"]
    old_folder = os.path.join(base, secure_part(user_id))
    new_folder = os.path.join(base, secure_part(new_user_id))

    if not os.path.exists(old_folder):
        return jsonify({"error": "user not found"}), 404
    if os.path.exists(new_folder):
        return jsonify({"error": "new user_id already exists"}), 400

    os.rename(old_folder, new_folder)
    return jsonify({
        "status": "user renamed",
        "old_user_id": secure_part(user_id),
        "new_user_id": secure_part(new_user_id)
    }), 200

# 🗑️ NEW: delete a single user and ALL their data
@admin_bp.route("/user/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    ok = StorageService.delete_user(user_id)
    if ok:
        return jsonify({"status": "user deleted", "user_id": secure_part(user_id)}), 200
    return jsonify({"error": "user not found"}), 404

# 🗑️ NEW: delete ALL users and ALL their data
@admin_bp.route("/users", methods=["DELETE"])
def delete_all_users():
    deleted = StorageService.delete_all_users()
    return jsonify({"status": "deleted all users", "deleted_users": deleted}), 200
