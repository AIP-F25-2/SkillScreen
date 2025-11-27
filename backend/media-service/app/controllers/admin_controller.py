from app.repositories.media_repository import MediaRepository
from db import UnitOfWork
import mimetypes
from flask import Blueprint, request, jsonify, redirect, current_app
from urllib.parse import urlsplit, urlunsplit, quote
from sqlalchemy import text
from app.services.storage_service import StorageService
from app.utils.filename import secure_part

admin_bp = Blueprint("admin", __name__)

def _build_blob_url(container_url: str, blob_path: str) -> str:
    """Build full Azure blob URL from container + blob path."""
    u = urlsplit(container_url)
    parts = [p for p in blob_path.split("/") if p]
    encoded_path = "/".join(quote(p, safe="~()*!.'") for p in parts)
    new_path = (u.path.rstrip("/") + "/" + encoded_path).replace("//", "/")
    return urlunsplit((u.scheme, u.netloc, new_path, u.query, u.fragment))


# =========================================================
# 🎥 VIDEOS
# =========================================================

@admin_bp.route("/videos", methods=["GET"])
def list_all_videos():
    """Return all video metadata and any blob names stored"""
    try:
        with UnitOfWork() as uow:
            repo = MediaRepository(uow)
            rows = repo.list_all_videos()  # New helper below
        files = StorageService.list_files()
        return jsonify({"videos": rows, "files": files}), 200
    except Exception as e:
        current_app.logger.exception("Failed to list videos")
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/videos/<interview_id>", methods=["GET"])
def list_interview_videos(interview_id):
    """List videos for one interview."""
    interview_id = secure_part(interview_id)
    vids = [f for f in StorageService.list_files(interview_id) if f.endswith(".mp4")]
    return jsonify({"interview_id": interview_id, "videos": vids}), 200


@admin_bp.route("/video/<interview_id>/<filename>", methods=["DELETE"])
def delete_video(interview_id, filename):
    """Delete both blob and DB record for a video."""
    interview_id = secure_part(interview_id)
    filename = secure_part(filename)
    deleted_from_storage = False
    deleted_from_db = False
    print(filename)
    # 1️⃣ Delete from Azure/local storage
    try:
        deleted_from_storage = StorageService.delete_file(interview_id, filename)
    except Exception:
        current_app.logger.warning(f"Storage deletion failed for {filename}", exc_info=True)

    # 2️⃣ Delete from DB
    try:
        with UnitOfWork() as uow:
            uow.session.execute(
                text("""
                    DELETE FROM media_files
                    WHERE interview_id = :iid
                      AND (blob_name = :fname OR storage_uri ILIKE :uri_like)
                """),
                {
                    "iid": interview_id,
                    "fname": filename,
                    "uri_like": f"%{filename}%",
                }
            )
            uow.session.commit()
            deleted_from_db = True
    except Exception:
        current_app.logger.warning(f"DB row deletion failed for {filename}", exc_info=True)

    if deleted_from_storage or deleted_from_db:
        return jsonify({
            "status": "deleted",
            "file": filename,
            "storage_deleted": deleted_from_storage,
            "db_deleted": deleted_from_db
        }), 200

    return jsonify({"error": "file not found"}), 404



@admin_bp.route("/videos/<interview_id>", methods=["DELETE"])
def delete_all_videos_for_interview(interview_id):
    """Delete all videos under one interview."""
    StorageService.delete_folder(f"videos/{secure_part(interview_id)}/")
    return jsonify({"status": "deleted", "interview_id": interview_id}), 200


@admin_bp.route("/video/<interview_id>/preview/<filename>", methods=["GET"])
def preview_video(interview_id, filename):
    """Redirect to Azure blob for quick preview."""
    interview_id = secure_part(interview_id)
    filename = secure_part(filename)
    container_url = current_app.config.get("AZURE_BLOB_CONTAINER_URL")
    blob_url = _build_blob_url(container_url, f"videos/{interview_id}/{filename}")
    return redirect(blob_url, code=302)


# =========================================================
# 📄 FILES (non-video assets)
# =========================================================

@admin_bp.route("/files/<interview_id>", methods=["GET"])
def list_interview_files(interview_id):
    """List non-video files under one interview folder."""
    interview_id = secure_part(interview_id)
    files = [
        f for f in StorageService.list_files(interview_id)
        if not (f.endswith(".mp4") or f.endswith(".webm"))
    ]
    return jsonify({"interview_id": interview_id, "files": files}), 200


@admin_bp.route("/file/<interview_id>/<filename>", methods=["DELETE"])
def delete_file(interview_id, filename):
    """Delete both the file in Azure and its DB record."""
    interview_id = secure_part(interview_id)
    filename = secure_part(filename)

    # 1️⃣ Delete from Azure
    ok = StorageService.delete_file(interview_id, filename)

    # 2️⃣ Delete from DB
    deleted_rows = 0
    if ok:
        with UnitOfWork() as uow:
            repo = MediaRepository(uow)
            deleted_rows = repo.delete_file_record(interview_id, f"videos/{interview_id}/{filename}")

    if ok:
        return jsonify({
            "status": "deleted",
            "file": filename,
            "db_deleted": bool(deleted_rows)
        }), 200

    return jsonify({"error": "file not found"}), 404



@admin_bp.route("/file/<interview_id>/preview/<filename>", methods=["GET"])
def preview_file(interview_id, filename):
    """Direct link preview for a generic file."""
    interview_id = secure_part(interview_id)
    filename = secure_part(filename)
    container_url = current_app.config.get("AZURE_BLOB_CONTAINER_URL")
    blob_url = _build_blob_url(container_url, f"videos/{interview_id}/{filename}")
    return redirect(blob_url, code=302)


# =========================================================
# 🔍 SEARCH
# =========================================================

@admin_bp.route("/search/interviews", methods=["GET"])
def search_interviews():
    q = (request.args.get("q") or "").lower()
    all_blobs = StorageService.list_files()  # Flat list of all files
    grouped = {}

    for blob in all_blobs:
        # Expect path like "videos/<interview_id>/filename.ext"
        parts = blob.split("/")
        if len(parts) < 3 or not parts[1]:
            continue
        interview_id = parts[1]
        filename = parts[-1]

        if q in filename.lower():
            grouped.setdefault(interview_id, []).append(filename)

    return jsonify({"query": q, "matched_interviews": grouped}), 200
