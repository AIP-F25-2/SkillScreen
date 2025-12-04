from __future__ import annotations

import json
import os
import shutil
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

from fastapi import HTTPException, UploadFile

from azure.core.exceptions import ResourceNotFoundError

from app.utils.config import settings
from app.core.logging import get_logger
from app.helpers.azure_blob import BlobReference, azure_blob
from app.helpers.state_metrics import TrackingState
from app.repositories.video_ai_repository import VideoAIRepository
from app.services.models_loader import load_yolo, pick_first_existing, warmup
from app.services.video_analyzer import VideoAnalyzer

try:
    import cv2  # noqa: F401
except Exception:  # pragma: no cover
    cv2 = None  # type: ignore

_LOG = get_logger("analysis_service")

_face_model = None
_person_model = None
_object_model = None
_pose_model = None
_state = TrackingState(ema_alpha=0.25)

_VALID_EXTS = (".mp4", ".mov", ".mkv", ".avi", ".webm")

_repo = VideoAIRepository()


def validate_media_reference(interview_id: str, session_id: str, media_id: Optional[str]) -> None:
    if not media_id:
        return
    _resolve_media_video_url(interview_id, session_id, media_id)


def build_accept_response(interview_id: str, session_id: str, media_file_id: Optional[str]) -> Dict[str, Any]:
    return {
        "status": "accepted",
        "message": "Vedio processing started in background",
        "media_file_id": media_file_id,
        "interview_id": interview_id,
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def _log_run(
    interview_id: str,
    session_id: str,
    status: str,
    result: Dict[str, Any],
) -> None:
    summary = result.get("summary") or {}
    media_file_id = result.get("media_file_id")
    if media_file_id and "media_file_id" not in summary:
        summary["media_file_id"] = media_file_id
    try:
        _repo.save_report(
            interview_id=interview_id,
            session_id=session_id,
            timestamp_label=result.get("report_timestamp"),
            status=status,
            report=result.get("report"),
            summary=summary,
            report_blob=result.get("report_blob"),
            video_blob=result.get("video_blob"),
            thumbnail_blobs=summary.get("thumbnail_blobs"),
            media_file_id=media_file_id,
            processing_time_seconds=result.get("processing_time_seconds"),
        )
    except Exception:
        _LOG.warning("Failed to persist video analysis log", exc_info=True)


# ---------------------------
# Internal helpers
# ---------------------------
def _ensure_models() -> None:
    """Lazy, idempotent model init (mirrors your previous logic)."""
    global _face_model, _person_model, _object_model, _pose_model
    if _face_model is not None and _person_model is not None:
        return

    face_w = pick_first_existing(settings.FACE_MODEL_CANDIDATES)
    if not face_w:
        raise HTTPException(500, "No face model found. Place one of: " + ", ".join(settings.FACE_MODEL_CANDIDATES))
    _LOG.info(f"Loading face model: {face_w}")
    _face_model = load_yolo(face_w, use_gpu=settings.USE_GPU, use_half=getattr(settings, "USE_HALF", False)); warmup(_face_model)

    person_w = pick_first_existing(settings.PERSON_MODEL_CANDIDATES)
    if not person_w:
        raise HTTPException(500, "No person model found. Place one of: " + ", ".join(settings.PERSON_MODEL_CANDIDATES))
    _LOG.info(f"Loading person model: {person_w}")
    _person_model = load_yolo(person_w, use_gpu=settings.USE_GPU, use_half=getattr(settings, "USE_HALF", False)); warmup(_person_model)

    obj_w = pick_first_existing(settings.OBJECT_MODEL_CANDIDATES)
    if obj_w:
        _LOG.info(f"Loading object model: {obj_w}")
        _object_model = load_yolo(obj_w, use_gpu=settings.USE_GPU, use_half=getattr(settings, "USE_HALF", False)); warmup(_object_model)

    pose_w = pick_first_existing(getattr(settings, "POSE_MODEL_CANDIDATES", []))
    if pose_w:
        _LOG.info(f"Loading pose model: {pose_w}")
        _pose_model = load_yolo(pose_w, use_gpu=settings.USE_GPU, use_half=getattr(settings, "USE_HALF", False)); warmup(_pose_model)


def _session_dirs(interview_id: str, session_id: str) -> Tuple[str, str]:
    upload_dir = os.path.join(settings.UPLOAD_FOLDER, interview_id, session_id)
    processed_dir = os.path.join(settings.PROCESSED_FOLDER, interview_id, session_id)
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    return upload_dir, processed_dir


def _resolve_local_video_path(interview_id: str, session_id: str, video_url: str) -> str:
    upload_dir, _ = _session_dirs(interview_id, session_id)
    parsed = urlparse(video_url)
    if parsed.scheme in ("http", "https"):
        candidate = os.path.join(upload_dir, os.path.basename(parsed.path))
    else:
        candidate = os.path.join(upload_dir, os.path.basename(video_url))
    if not os.path.exists(candidate):
        raise HTTPException(status_code=404, detail=f"Video not found at {candidate}")
    return candidate


def _resolve_video_source(interview_id: str, session_id: str, video_url: str) -> Tuple[str, Optional[BlobReference]]:
    if azure_blob.enabled:
        try:
            fetched = azure_blob.fetch_video(interview_id, session_id, video_url)
            if fetched:
                return fetched
        except ResourceNotFoundError:
            raise HTTPException(404, "Video blob not found; verify URL and SAS token")
        except Exception as exc:
            raise HTTPException(502, f"Azure blob download failed: {exc}")
    return _resolve_local_video_path(interview_id, session_id, video_url), None


def _match_media_file_by_blob(interview_id: str, session_id: str, blob_name: Optional[str]) -> Optional[str]:
    if not blob_name:
        return None
    try:
        return _repo.find_media_file_by_blob(interview_id, session_id, blob_name)
    except Exception:
        _LOG.warning(
            "Failed to resolve media file for blob=%s interview=%s session=%s",
            blob_name,
            interview_id,
            session_id,
            exc_info=True,
        )
        return None


def _coerce_metadata(raw: Any) -> Dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            return {}
    return {}


def _blob_name_to_url(blob_name: Optional[str]) -> Optional[str]:
    if not blob_name:
        return None
    blob_name = blob_name.strip()
    if not blob_name:
        return None
    if "://" in blob_name:
        return blob_name
    if not azure_blob.enabled:
        return None

    trimmed = blob_name.lstrip("/")
    container = azure_blob.videos_container
    blob_path = trimmed
    if "/" in trimmed:
        first, remainder = trimmed.split("/", 1)
        if remainder:
            if first == container:
                blob_path = remainder
            else:
                container = first
                blob_path = remainder
    ref = BlobReference(container=container, blob=blob_path)
    return azure_blob.public_url(ref)


def _resolve_media_video_url(interview_id: str, session_id: str, media_id: str) -> str:
    record = _repo.get_media_file(media_id)
    if not record:
        raise HTTPException(404, "Media file not found")

    record_interview = record.get("interview_id")
    if record_interview and str(record_interview) != interview_id:
        raise HTTPException(400, "Media file does not belong to the interview")

    record_session = record.get("session_id")
    if record_session and str(record_session) != session_id:
        raise HTTPException(400, "Media file does not belong to the session")

    file_type = (record.get("file_type") or "").lower()
    if file_type and file_type != "video":
        raise HTTPException(400, "Media file is not a video asset")

    metadata = _coerce_metadata(record.get("metadata"))
    url_candidates = [
        record.get("storage_uri"),
        metadata.get("storage_uri"),
        metadata.get("source_url"),
        metadata.get("video_url"),
    ]
    for candidate in url_candidates:
        if candidate:
            return candidate

    blob_name = record.get("blob_name")
    blob_url = _blob_name_to_url(blob_name)
    if blob_url:
        return blob_url

    raise HTTPException(400, "Media file does not have a usable storage_uri or blob_name")


def resolve_media_video_url(interview_id: str, session_id: str, media_id: str) -> str:
    """Public helper for other services (processed_service) to fetch media URLs."""
    return _resolve_media_video_url(interview_id, session_id, media_id)


def _build_upload_target(interview_id: str, session_id: str, filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext not in _VALID_EXTS:
        raise HTTPException(415, f"Unsupported media type; allowed: {', '.join(_VALID_EXTS)}")
    upload_dir, _ = _session_dirs(interview_id, session_id)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return os.path.join(upload_dir, f"{session_id}_{ts}{ext}")


def _make_analyzer() -> VideoAnalyzer:
    return VideoAnalyzer(
        face_model=_face_model,
        person_model=_person_model,
        object_model=_object_model,
        pose_model=_pose_model if getattr(settings, "POSE_ENABLED", True) else None,
        state=_state,
    )


def _upload_source_to_azure(interview_id: str, session_id: str, local_path: str) -> Optional[Dict[str, Optional[str]]]:
    if not azure_blob.enabled:
        return None
    ref = azure_blob.build_video_blob(interview_id, session_id, os.path.basename(local_path))
    url = azure_blob.upload_file(ref, local_path)
    return {"blob": ref.blob, "url": url or None}


def _sync_processed_outputs(interview_id: str, session_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
    if not azure_blob.enabled:
        return result
    report_data = result.get("report")
    video_path = result.get("video_path")
    thumbs_dir = os.path.join(settings.PROCESSED_FOLDER, interview_id, session_id, "thumbs")
    report_bytes = json.dumps(report_data, indent=2).encode("utf-8") if report_data else None
    uploaded = azure_blob.upload_processed_artifacts(interview_id, session_id, report_bytes, video_path, thumbs_dir)
    if uploaded.get("report_blob"):
        result["report_blob"] = uploaded["report_blob"]
        result["report_url"] = uploaded.get("report_url")
    if uploaded.get("video_blob"):
        result["video_blob"] = uploaded["video_blob"]
        result["video_url"] = uploaded.get("video_url")
    if uploaded.get("thumbnail_blobs"):
        result["thumbnail_blobs"] = uploaded["thumbnail_blobs"]
        if result.get("summary"):
            result["summary"]["thumbnail_blobs"] = uploaded["thumbnail_blobs"]
    if video_path and os.path.isfile(video_path):
        try:
            os.remove(video_path)
            result["video_path"] = None
        except Exception:
            pass
    if thumbs_dir and os.path.isdir(thumbs_dir):
        try:
            shutil.rmtree(thumbs_dir)
        except Exception:
            pass
    return result




# ---------------------------
# Service surface
# ---------------------------
def svc_status() -> Dict[str, Any]:
    return {
        "video_only": True,
        "face_model": _face_model is not None,
        "person_model": _person_model is not None,
        "object_model": _object_model is not None,
        "pose_model": _pose_model is not None,
        "state_initialized": True,
        "settings": {
            "uploads_dir": settings.UPLOAD_FOLDER,
            "processed_dir": settings.PROCESSED_FOLDER,
            "target_fps": settings.TARGET_FPS,
        }
    }


def svc_reset() -> Dict[str, Any]:
    _state.reset()
    return {"ok": True, "msg": "State reset"}


async def svc_analyze_upload(interview_id: str, session_id: str, file: UploadFile) -> Dict[str, Any]:
    if cv2 is None:
        raise HTTPException(500, "OpenCV not available; install opencv-python-headless")

    _ensure_models()

    _LOG.info("Analyze upload requested interview=%s session=%s filename=%s", interview_id, session_id, file.filename)

    target_path = _build_upload_target(interview_id, session_id, (file.filename or "").lower())
    data = await file.read()
    with open(target_path, "wb") as f:
        f.write(data)

    src_meta = _upload_source_to_azure(interview_id, session_id, target_path)
    if src_meta:
        _LOG.info("Uploaded source to Azure blob=%s", src_meta.get("blob"))
    media_file_id = None
    if src_meta and src_meta.get("blob"):
        media_file_id = _match_media_file_by_blob(interview_id, session_id, src_meta.get("blob"))

    analyzer = _make_analyzer()
    started_at = time.perf_counter()
    try:
        result = analyzer.analyze(
            target_path,
            interview_id=interview_id,
            session_id=session_id,
            source_url=(src_meta.get("url") if src_meta else None)
        )
        processing_time_seconds = time.perf_counter() - started_at
    except Exception as e:
        _LOG.exception("Video analysis failed")
        elapsed = time.perf_counter() - started_at
        src_url = src_meta.get("url") if src_meta else None
        failure_result = {
            "summary": {"error": str(e), "source_url": src_url, "processing_time_seconds": round(elapsed, 3)},
            "processing_time_seconds": round(elapsed, 3),
            "media_file_id": media_file_id,
        }
        _log_run(interview_id, session_id, "failed", failure_result)
        raise HTTPException(400, f"Video processing error: {e}")

    result = _sync_processed_outputs(interview_id, session_id, result)
    if src_meta:
        result["source_url"] = src_meta.get("url") or src_meta.get("blob")
    summary = result.get("summary") or {}
    summary["interview_id"] = interview_id
    summary["session_id"] = session_id
    summary["processing_time_seconds"] = round(processing_time_seconds, 3)
    if media_file_id:
        summary["media_file_id"] = media_file_id
        result["media_file_id"] = media_file_id
    result["summary"] = summary
    result["processing_time_seconds"] = round(processing_time_seconds, 3)
    _log_run(interview_id, session_id, "completed", result)
    return result


def svc_analyze_url(
    interview_id: str,
    session_id: str,
    video_url: Optional[str] = None,
    media_id: Optional[str] = None,
) -> Dict[str, Any]:
    if cv2 is None:
        raise HTTPException(500, "OpenCV not available; install opencv-python-headless")

    if not video_url and not media_id:
        raise HTTPException(400, "Provide either video_url or media_id")

    _ensure_models()

    effective_url = video_url
    media_file_id = media_id
    if media_id:
        effective_url = _resolve_media_video_url(interview_id, session_id, media_id)

    _LOG.info(
        "Analyze URL requested interview=%s session=%s url=%s media_id=%s",
        interview_id,
        session_id,
        effective_url,
        media_id,
    )
    local_path, blob_ref = _resolve_video_source(interview_id, session_id, effective_url)
    cleanup_local = bool(blob_ref)
    if not media_file_id and blob_ref:
        media_file_id = _match_media_file_by_blob(interview_id, session_id, blob_ref.blob)
    analyzer = _make_analyzer()
    started_at = time.perf_counter()
    try:
        source_url = azure_blob.public_url(blob_ref) if blob_ref else str(effective_url)
        result = analyzer.analyze(
            local_path,
            interview_id=interview_id,
            session_id=session_id,
            source_url=source_url
        )
        processing_time_seconds = time.perf_counter() - started_at
    except Exception as e:
        _LOG.exception("Video analysis failed")
        elapsed = time.perf_counter() - started_at
        failure_result = {
            "summary": {"error": str(e), "source_url": source_url, "processing_time_seconds": round(elapsed, 3)},
            "processing_time_seconds": round(elapsed, 3),
            "media_file_id": media_file_id,
        }
        _log_run(interview_id, session_id, "failed", failure_result)
        raise HTTPException(400, f"Video processing error: {e}")
    finally:
        if cleanup_local and os.path.exists(local_path):
            try:
                os.remove(local_path)
            except Exception:
                pass

    result = _sync_processed_outputs(interview_id, session_id, result)
    if blob_ref:
        result["source_url"] = azure_blob.public_url(blob_ref) or str(effective_url)
    summary = result.get("summary") or {}
    summary["interview_id"] = interview_id
    summary["session_id"] = session_id
    summary["processing_time_seconds"] = round(processing_time_seconds, 3)
    if media_file_id:
        summary["media_file_id"] = media_file_id
        result["media_file_id"] = media_file_id
    result["summary"] = summary
    result["processing_time_seconds"] = round(processing_time_seconds, 3)
    _log_run(interview_id, session_id, "completed", result)
    return result


def svc_list_reports(interview_id: str) -> Dict[str, Any]:
    rows = _repo.list_runs(interview_id)
    return {"interview_id": interview_id, "sessions": rows}


def svc_startup_warm() -> Dict[str, Any]:
    """For FastAPI startup hook — optional, same as ensure_models but logs model names."""
    _ensure_models()
    return {
        "face_model": True,
        "person_model": True,
        "object_model": _object_model is not None,
        "pose_model": _pose_model is not None,
    }
