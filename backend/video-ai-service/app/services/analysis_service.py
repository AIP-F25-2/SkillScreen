from __future__ import annotations

import json
import os
import shutil
from datetime import datetime,timezone
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

from fastapi import HTTPException, UploadFile

from azure.core.exceptions import ResourceNotFoundError

from app.config import settings
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


def _log_run(
    interview_id: str,
    session_id: str,
    status: str,
    result: Dict[str, Any],
) -> None:
    blobs = {
        "source_blob": result.get("source_blob"),
        "report_blob": result.get("report_blob"),
        "video_blob": result.get("video_blob"),
    }
    summary = result.get("summary") or {}
    try:
        _repo.save_report(
            interview_id=interview_id,
            session_id=session_id,
            timestamp_label=result.get("report_timestamp"),
            status=status,
            report=result.get("report"),
            summary=summary,
            blobs=blobs,
            source_url=result.get("summary", {}).get("source_url"),
            thumbnail_blobs=summary.get("thumbnail_blobs"),
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

    analyzer = _make_analyzer()
    try:
        result = analyzer.analyze(
            target_path,
            interview_id=interview_id,
            session_id=session_id,
            source_url=(src_meta.get("url") if src_meta else None)
        )
    except Exception as e:
        _LOG.exception("Video analysis failed")
        failure_result = {
            "source_blob": src_meta.get("blob") if src_meta else None,
            "summary": {"error": str(e), "source_url": src_meta.get("url")},
        }
        _log_run(interview_id, session_id, "failed", failure_result)
        raise HTTPException(400, f"Video processing error: {e}")

    result = _sync_processed_outputs(interview_id, session_id, result)
    if src_meta:
        result["source_blob"] = src_meta.get("blob")
        result["source_url"] = src_meta.get("url") or src_meta.get("blob")
    summary = result.get("summary") or {}
    summary["interview_id"] = interview_id
    summary["session_id"] = session_id
    result["summary"] = summary
    _log_run(interview_id, session_id, "completed", result)
    return result


def svc_analyze_url(interview_id: str, session_id: str, video_url: str) -> Dict[str, Any]:
    if cv2 is None:
        raise HTTPException(500, "OpenCV not available; install opencv-python-headless")

    _ensure_models()

    _LOG.info("Analyze URL requested interview=%s session=%s url=%s", interview_id, session_id, video_url)
    local_path, blob_ref = _resolve_video_source(interview_id, session_id, video_url)
    cleanup_local = bool(blob_ref)
    analyzer = _make_analyzer()
    try:
        source_url = azure_blob.public_url(blob_ref) if blob_ref else str(video_url)
        result = analyzer.analyze(
            local_path,
            interview_id=interview_id,
            session_id=session_id,
            source_url=source_url
        )
    except Exception as e:
        _LOG.exception("Video analysis failed")
        failure_result = {
            "source_blob": blob_ref.blob if blob_ref else None,
            "summary": {"error": str(e), "source_url": source_url},
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
        result["source_blob"] = blob_ref.blob
        result["source_url"] = azure_blob.public_url(blob_ref) or str(video_url)
    summary = result.get("summary") or {}
    summary["interview_id"] = interview_id
    summary["session_id"] = session_id
    result["summary"] = summary
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
