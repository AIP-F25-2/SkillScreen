import os, re, tempfile, shutil
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file, current_app

# Azure-backed storage service
from ..services.azure_storage_service import AzureStorageService as StorageService

from ..services.video_service import (
    init_manifest as vs_init_manifest,
    save_chunk as vs_save_chunk,
    get_missing_chunks as vs_get_missing_chunks,
    reset_session as vs_reset_session,
    finalize_concat_then_encode,
)

from ..utils.filename import secure_part
from sqlalchemy import select,text
from db import UnitOfWork
from app.repositories.media_repository import MediaRepository

upload_bp = Blueprint("upload", __name__)

def _server_chunk_name(idx_zero_based: int) -> str:
    return f"chunk-{idx_zero_based + 1:05d}.webm"

def _get_session_id(src: dict, default: str = "default") -> str:
    sid = src.get("session_id")
    return secure_part(sid) if sid else default


@upload_bp.route("/upload/init", methods=["POST"])
def upload_init():
    data = request.get_json() or {}
    user_id = data.get("user_id")
    total_chunks = data.get("total_chunks")
    session_id = _get_session_id(data)

    if not user_id or total_chunks is None:
        return jsonify({"error": "Missing user_id or total_chunks"}), 400

    # Manifest is user-scoped; safe to call each time.
    try:
        vs_init_manifest(
            user_id=str(user_id),
            session_id=session_id,              # kept for DB use downstream
            expected_total=int(total_chunks),
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    with UnitOfWork() as uow:
        repo = MediaRepository(uow)

        # Idempotent "get or create" for a recording row of this session.
        existing = repo.get_recording_status(user_id=str(user_id), session_id=session_id)
        if existing:
            # Backfill/raise expected_total if the new init provides a higher number.
            try:
                uow.session.execute(
                    """
                    UPDATE media
                       SET expected_total = COALESCE(
                               GREATEST(COALESCE(expected_total, 0), :tot),
                               :tot
                           ),
                           updated_at = NOW()
                     WHERE user_id = :uid
                       AND session_id::text = :sid
                       AND media_type = 'video'
                       AND status = 'recording'
                    """,
                    {"uid": str(user_id), "sid": session_id, "tot": int(total_chunks)}
                )
                uow.session.commit()
            except Exception:
                uow.session.rollback()

            return jsonify({
                "status": "initialized",
                "total_chunks": int(total_chunks),
                "session_id": session_id,
                "db_id": existing.get("id") if isinstance(existing, dict) else None,
            }), 200

        # Otherwise, create a fresh recording row
        video_id = repo.create_recording_video(
            user_id=str(user_id),
            session_id=session_id,
            expected_total=int(total_chunks),
        )

    return jsonify({
        "status": "initialized",
        "total_chunks": int(total_chunks),
        "session_id": session_id,
        "db_id": video_id,
    }), 200


@upload_bp.route("/upload_chunk", methods=["POST"])
def upload_chunk():
    file = request.files.get("file")
    user_id = request.form.get("user_id")
    chunk_index = request.form.get("chunk_index", type=int)
    total_chunks = request.form.get("total_chunks", type=int)  # optional (used to backfill)
    session_id = _get_session_id(request.form)

    if not file or not user_id or chunk_index is None:
        return jsonify({"error": "Missing file, user_id, or chunk_index"}), 400

    server_filename = _server_chunk_name(chunk_index)

    # 1) Save chunk (Azure + manifest.received)
    try:
        vs_save_chunk(
            user_id=str(user_id),
            idx_zero_based=int(chunk_index),
            fileobj=file,
            session_id=session_id,
            candidate_id=request.form.get("candidate_id"),
            interview_id=request.form.get("interview_id"),
            assigned_user=request.form.get("assigned_user"),
        )
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        current_app.logger.exception("upload_chunk failed")
        return jsonify({"error": str(e)}), 400

    # 2) EXTRA safety: idempotent merge in manifest (user-scoped)
    try:
        man = StorageService.load_manifest(str(user_id)) or {}
        rec = set(man.get("received") or [])
        rec.add(int(chunk_index))
        man["received"] = sorted(rec)
        if total_chunks is not None:
            prev = int(man.get("expected_total") or 0)
            man["expected_total"] = max(int(total_chunks), prev)
        StorageService.save_manifest(str(user_id), man)
    except Exception:
        current_app.logger.exception("manifest merge failed (non-fatal)")

    # 3) DB progress update (session-scoped)
    with UnitOfWork() as uow:
        repo = MediaRepository(uow)
        repo.mark_chunk_received(
            user_id=str(user_id),
            session_id=session_id,
            idx=chunk_index,
            expected_total=total_chunks,
        )

    return jsonify({
        "status": "chunk saved",
        "idx": chunk_index,
        "name": server_filename,
        "session_id": session_id
    }), 200


@upload_bp.route("/upload/missing", methods=["GET"])
def upload_missing():
    user_id = request.args.get("user_id")
    session_id = _get_session_id(request.args)
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    # Union manifest (user-scoped) + DB (session-scoped)
    expected_total = None
    received = set()
    try:
        man = StorageService.load_manifest(str(user_id)) or {}
        received |= set(man.get("received") or [])
        expected_total = man.get("expected_total")
    except Exception:
        man = {}

    with UnitOfWork() as uow:
        repo = MediaRepository(uow)
        status = repo.get_recording_status(user_id=str(user_id), session_id=session_id)
        if status:
            received |= set(status.get("received", []) or [])
            if expected_total is None:
                expected_total = status.get("expected_total")

    if not received:
        return jsonify({"missing": [], "expected_total": 0, "session_id": session_id}), 200

    if expected_total is None:
        expected_total = max(received) + 1

    missing = [i for i in range(int(expected_total)) if i not in received]
    return jsonify({"missing": missing, "expected_total": int(expected_total), "session_id": session_id}), 200


@upload_bp.route("/reset_chunks", methods=["POST"])
def reset_chunks():
    """
    Idempotent reset:
      - Accepts JSON, form-data, or querystring.
      - If chunks/merged/manifest are already gone, still returns 200.
      - Aborts the current 'recording' row for the given session in DB (if present).
    """
    # accept json, form, or query params
    data_json = None
    try:
        data_json = request.get_json(silent=True) or {}
    except Exception:
        data_json = {}

    data = {}
    data.update(request.args or {})
    data.update(request.form or {})
    data.update(data_json or {})

    user_id = data.get("user_id")
    session_id = _get_session_id(data)

    if not user_id:
        return jsonify({"error": "Missing user_id (send as JSON, form, or ?user_id=)"}), 400

    deleted = []
    storage_errors = []

    # Best-effort storage cleanup; never fail if files are already gone
    try:
        # Remove all chunk blobs and any merged artifact; keep manifest so UI can show 'aborted'
        vs_reset_session(str(user_id), wipe_merged=True, wipe_manifest=False)
    except FileNotFoundError:
        pass
    except Exception as e:
        current_app.logger.exception("reset_chunks: storage cleanup failed")
        storage_errors.append(str(e))

    # Mark the session aborted in DB (if a recording row exists)
    try:
        with UnitOfWork() as uow:
            repo = MediaRepository(uow)
            uow.session.execute(
                text("""
                    UPDATE media_files
                       SET status='aborted', updated_at=NOW()
                     WHERE user_id = :uid
                       AND media_type='video'
                       AND status='recording'
                       AND session_id::text = :sid
                """),
                {"uid": str(user_id), "sid": session_id}
            )
            uow.session.commit()
    except Exception as e:
        current_app.logger.exception("reset_chunks: db abort_recording failed")
        storage_errors.append(f"db: {e}")

    resp = {
        "status": "chunks reset",
        "deleted": deleted,
        "session_id": session_id,
    }
    if storage_errors:
        resp["warnings"] = storage_errors  # surfaced but not fatal

    return jsonify(resp), 200


@upload_bp.route("/finalize_upload", methods=["POST"])
def finalize_upload():
    data = request.get_json() or {}
    user_id = data.get("user_id")
    keep_merged = bool(data.get("keep_merged", False))
    keep_manifest = bool(data.get("keep_manifest", False))
    session_id = _get_session_id(data)

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    # 1) Build a UNION of manifest (user) + DB (session)
    expected_total = None
    received = set()
    try:
        man = StorageService.load_manifest(str(user_id)) or {}
        received |= set(man.get("received") or [])
        expected_total = man.get("expected_total")
    except Exception:
        man = {}

    with UnitOfWork() as uow:
        repo = MediaRepository(uow)
        status = repo.get_recording_status(user_id=str(user_id), session_id=session_id)
        if status:
            received |= set(status.get("received", []) or [])
            if expected_total is None:
                expected_total = status.get("expected_total")

    if not received:
        return jsonify({"error": "No .webm chunks found"}), 400

    if expected_total is None:
        expected_total = max(received) + 1

    # Compute missing from the union
    missing = [i for i in range(int(expected_total)) if i not in received]
    if missing:
        return jsonify({"error": "missing chunks", "missing": missing}), 409

    # 2) Stage locally so ffmpeg can read paths without Azure I/O hiccups
    workdir = tempfile.mkdtemp(prefix=f"merge-{secure_part(str(user_id))}-")
    try:
        for idx in range(int(expected_total)):
            fname = _server_chunk_name(idx)
            try:
                local_tmp = StorageService.download_to_temp(str(user_id), fname)
            except Exception as e:
                shutil.rmtree(workdir, ignore_errors=True)
                return jsonify({"error": f"failed to fetch {fname}", "detail": str(e)}), 400
            dest = Path(workdir) / fname
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(local_tmp, dest)

        # 3) Merge + encode (local-first inside the helper)
        try:
            final_mp4_name, merged_webm_name, used_chunks = finalize_concat_then_encode(
                workdir,
                str(user_id),
                keep_merged=keep_merged,
                keep_manifest=keep_manifest,
                session_id=session_id,  # pass through
            )
        except FileNotFoundError:
            return jsonify({"error": "No .webm chunks found"}), 400
        except RuntimeError as e:
            return jsonify({"error": "ffmpeg failed", "stderr": str(e)[:4000]}), 500

    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    # 4) DB finalize the same session row
    final_blob_path = f"{secure_part(str(user_id))}/{secure_part(final_mp4_name)}"
    with UnitOfWork() as uow:
        repo = MediaRepository(uow)
        video_id = repo.finalize_recording(
            user_id=str(user_id),
            session_id=session_id,
            final_file_name=final_mp4_name,
            final_blob_path=final_blob_path,
            merged_chunks=used_chunks,
            size_bytes=None,
            duration_ms=None,
        )

        # --- Cleanup: remove any transient “uploaded” rows for the same final blob ---
        try:
            uow.session.execute(
                text("""
                    DELETE FROM media_files
                     WHERE user_id = :uid
                       AND media_type = 'video'
                       AND status = 'uploaded'
                       AND blob_name = :blob
                       AND (session_id IS NULL OR session_id::text = :sid)
                       AND id <> :keep_id
                """),
                {
                    "uid": str(user_id),
                    "blob": final_blob_path,
                    "sid": session_id,
                    "keep_id": video_id,
                },
            )
            uow.session.commit()
        except Exception:
            pass

    # 5) Best-effort: write back contiguous received/expected_total to manifest (user-scoped)
    try:
        man = StorageService.load_manifest(str(user_id)) or {}
        man["received"] = list(range(int(expected_total)))
        man["expected_total"] = int(expected_total)
        man["status"] = "done"
        StorageService.save_manifest(str(user_id), man)
    except Exception:
        pass

    return jsonify({
        "status": "done",
        "merged_chunks": used_chunks,
        "webm": (f"/video/{secure_part(str(user_id))}/{merged_webm_name}" if keep_merged else None),
        "file": f"/video/{secure_part(str(user_id))}/{final_mp4_name}",
        "db_id": video_id,
    }), 200


@upload_bp.route("/video/<user_id>/<filename>")
def serve_video(user_id, filename):
    user_id = secure_part(user_id)
    filename = secure_part(filename)
    try:
        tmp_path = StorageService.download_to_temp(user_id, filename)
    except Exception:
        return jsonify({"error": "file not found"}), 404

    ext = os.path.splitext(filename)[1].lower()
    mimetype = "video/mp4" if ext == ".mp4" else ("video/webm" if ext == ".webm" else "application/octet-stream")
    return send_file(tmp_path, mimetype=mimetype, as_attachment=False, download_name=filename, conditional=True)


@upload_bp.route("/chunks/status", methods=["GET"])
def chunks_status():
    user_id = request.args.get("user_id")
    session_id = request.args.get("session_id") or request_args.get("sid") if (request_args := request.args) else None

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    with UnitOfWork() as uow:
        repo = MediaRepository(uow)
        if not session_id:
            latest = uow.session.execute(
                select(repo.c.session_id)
                .where(repo.c.user_id == str(user_id), repo.c.media_type == "video")
                .order_by(repo.c.id.desc())
                .limit(1)
            ).scalar_one_or_none()
            session_id = latest

        if not session_id:
            return jsonify({"expected_total": 0, "received": [], "missing": [], "status": "idle"}), 200

        status = repo.get_recording_status(user_id=str(user_id), session_id=session_id)
        if not status:
            return jsonify({"expected_total": 0, "received": [], "missing": [], "status": "idle"}), 200

        return jsonify({
            "session_id": session_id,
            **status
        }), 200
