# app/controllers/upload_controller.py
import os, re
from flask import Blueprint, request, jsonify, send_from_directory
from ..services.storage_service import StorageService
from ..services.video_service import (
    init_manifest,
    save_chunk,
    get_missing_chunks,
    reset_chunks as svc_reset_chunks,
    finalize_concat_then_encode,
)
from ..utils.filename import secure_part

upload_bp = Blueprint("upload", __name__)

def _server_chunk_name(idx_zero_based: int) -> str:
    return f"chunk-{idx_zero_based + 1:05d}.webm"

@upload_bp.route("/upload/init", methods=["POST"])
def upload_init():
    data = request.get_json() or {}
    user_id = data.get("user_id")
    total_chunks = data.get("total_chunks")
    if not user_id or total_chunks is None:
        return jsonify({"error": "Missing user_id or total_chunks"}), 400
    folder = StorageService.user_folder(user_id)
    try:
        init_manifest(folder, int(total_chunks))
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"status": "initialized", "total_chunks": int(total_chunks)}), 200

@upload_bp.route("/upload_chunk", methods=["POST"])
def upload_chunk():
    file = request.files.get("file")
    user_id = request.form.get("user_id")
    chunk_index = request.form.get("chunk_index", type=int)
    total_chunks = request.form.get("total_chunks", type=int)

    if not file or not user_id:
        return jsonify({"error": "Missing file or user_id"}), 400

    folder = StorageService.user_folder(user_id)
    server_filename = _server_chunk_name(chunk_index) if chunk_index is not None else file.filename

    try:
        save_chunk(folder, server_filename, file)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400

    man = StorageService.load_manifest(user_id)
    if chunk_index is not None and chunk_index not in man["received"]:
        man["received"].append(chunk_index)
        man["received"].sort()
    if total_chunks is not None:
        man["expected_total"] = max(total_chunks, man.get("expected_total") or 0)
    StorageService.save_manifest(user_id, man)

    return jsonify({"status": "chunk saved", "idx": chunk_index, "name": server_filename}), 200

@upload_bp.route("/upload/missing", methods=["GET"])
def upload_missing():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
    folder = StorageService.user_folder(user_id)
    missing = get_missing_chunks(folder)
    return jsonify({"missing": missing}), 200

@upload_bp.route("/reset_chunks", methods=["POST"])
def reset_chunks():
    data = request.get_json() or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
    folder = StorageService.user_folder(user_id)
    deleted = svc_reset_chunks(folder)
    return jsonify({"status": "chunks reset", "deleted": deleted}), 200

@upload_bp.route("/finalize_upload", methods=["POST"])
def finalize_upload():
    data = request.get_json() or {}
    user_id = data.get("user_id")
    keep_merged = bool(data.get("keep_merged", False))
    keep_manifest = bool(data.get("keep_manifest", False))
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    man = StorageService.load_manifest(user_id)
    received = sorted(set(man.get("received", [])))
    expected_total = man.get("expected_total")

    if expected_total is None and received:
        expected_total = max(received) + 1
        man["expected_total"] = expected_total
        StorageService.save_manifest(user_id, man)

    missing = []
    if expected_total:
        for i in range(expected_total):
            if i not in received:
                missing.append(i)
    if missing:
        return jsonify({"error": "missing chunks", "missing": missing}), 409

    folder = StorageService.user_folder(user_id)
    try:
        merged_mp4, merged_webm, used_chunks = finalize_concat_then_encode(
            folder, user_id, keep_merged=keep_merged, keep_manifest=keep_manifest
        )
    except FileNotFoundError:
        return jsonify({"error": "No .webm chunks found"}), 400
    except RuntimeError as e:
        return jsonify({"error": "ffmpeg failed", "stderr": str(e)[:4000]}), 500

    return jsonify({
        "status": "done",
        "merged_chunks": used_chunks,
        "webm": (f"/video/{secure_part(user_id)}/{merged_webm}" if keep_merged else None),
        "file": f"/video/{secure_part(user_id)}/{merged_mp4}"
    }), 200

@upload_bp.route("/video/<user_id>/<filename>")
def serve_video(user_id, filename):
    user_id = secure_part(user_id)
    filename = secure_part(filename)
    folder = StorageService.user_folder(user_id)
    path = os.path.join(folder, filename)
    if not os.path.isfile(path):
        return jsonify({"error": "file not found"}), 404
    return send_from_directory(folder, filename, conditional=True)

@upload_bp.route("/chunks/status", methods=["GET"])
def chunks_status():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    man = StorageService.load_manifest(user_id)
    received = sorted(set(man.get("received", [])))
    exp = man.get("expected_total")

    if exp is None:
        files = [f for f in os.listdir(StorageService.user_folder(user_id)) if f.endswith(".webm")]
        hi = -1
        for f in files:
            m = re.search(r"chunk-(\d+)\.webm$", f, re.IGNORECASE)
            if m:
                hi = max(hi, int(m.group(1)))
        if hi >= 1:
            exp = hi

    missing = []
    if exp is not None:
        missing = [i for i in range(0, exp) if i not in received]

    return jsonify({"received": received, "expected_total": exp, "missing": missing}), 200
