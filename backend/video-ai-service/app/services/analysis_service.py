from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List
from urllib.parse import urlparse

from fastapi import HTTPException, UploadFile
from app.core.logging import get_logger
from app.config import settings
from app.services.video_analyzer import VideoAnalyzer
from app.helpers.state_metrics import TrackingState
from app.services.models_loader import load_yolo, warmup, pick_first_existing

try:
    import cv2  # noqa: F401
except Exception:
    cv2 = None  # type: ignore

_LOG = get_logger("analysis_service")

# ---------------------------
# Module-level model cache
# ---------------------------
_face_model = None
_person_model = None
_object_model = None
_pose_model = None
_state = TrackingState(ema_alpha=0.25)

_VALID_EXTS = (".mp4", ".mov", ".mkv", ".avi", ".webm")


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


def _resolve_local_video_path(user_id: str, video_url: str) -> str:
    """
    Resolve a video path that already exists under:
      UPLOAD_FOLDER/<user_id>/<user_id>_<timestamp>.<ext>

    Accepts absolute path, '/<user>/<file>'-style path, or http(s) URL
    that points to a file already present under uploads/<user_id>/.
    """
    user_dir = os.path.join(settings.UPLOAD_FOLDER, user_id)
    os.makedirs(user_dir, exist_ok=True)

    parsed = urlparse(video_url)
    if parsed.scheme in ("http", "https"):
        basename = os.path.basename(parsed.path)
        candidate = os.path.join(user_dir, basename)
    else:
        p = video_url
        candidate = p if os.path.isabs(p) else os.path.join(settings.UPLOAD_FOLDER, p.lstrip("/"))
        # Force it into the user's directory if it's elsewhere
        abs_user = os.path.abspath(user_dir)
        abs_cand = os.path.abspath(candidate)
        try:
            common = os.path.commonpath([abs_cand, abs_user])
        except Exception:
            common = ""
        if not common or common != abs_user:
            candidate = os.path.join(user_dir, os.path.basename(candidate))

    if not os.path.exists(candidate):
        raise HTTPException(status_code=404, detail=f"Video not found at {candidate}")
    return candidate


def _build_upload_target(user_id: str, filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext not in _VALID_EXTS:
        raise HTTPException(415, f"Unsupported media type; allowed: {', '.join(_VALID_EXTS)}")
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    user_dir = os.path.join(settings.UPLOAD_FOLDER, user_id)
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join(user_dir, f"{user_id}_{ts}{ext}")


def _make_analyzer() -> VideoAnalyzer:
    return VideoAnalyzer(
        face_model=_face_model,
        person_model=_person_model,
        object_model=_object_model,
        pose_model=_pose_model if getattr(settings, "POSE_ENABLED", True) else None,
        state=_state,
    )


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


async def svc_analyze_upload(user_id: str, file: UploadFile) -> Dict[str, Any]:
    if cv2 is None:
        raise HTTPException(500, "OpenCV not available; install opencv-python-headless")

    _ensure_models()

    target_path = _build_upload_target(user_id, (file.filename or "").lower())
    data = await file.read()
    with open(target_path, "wb") as f:
        f.write(data)

    analyzer = _make_analyzer()
    try:
        return analyzer.analyze(target_path, user_id=user_id, source_url=None)
    except Exception as e:
        _LOG.exception("Video analysis failed")
        raise HTTPException(400, f"Video processing error: {e}")


def svc_analyze_url(user_id: str, video_url: str) -> Dict[str, Any]:
    if cv2 is None:
        raise HTTPException(500, "OpenCV not available; install opencv-python-headless")

    _ensure_models()

    local_path = _resolve_local_video_path(user_id, video_url)
    analyzer = _make_analyzer()
    try:
        return analyzer.analyze(local_path, user_id=user_id, source_url=str(video_url))
    except Exception as e:
        _LOG.exception("Video analysis failed")
        raise HTTPException(400, f"Video processing error: {e}")


def svc_list_reports(user_id: str) -> Dict[str, Any]:
    """Light listing of user artifacts: reports, annotated videos, thumbnails."""
    pdir = os.path.join(settings.PROCESSED_FOLDER, user_id)
    if not os.path.isdir(pdir):
        raise HTTPException(404, "User not found")

    import glob
    reports = sorted(glob.glob(os.path.join(pdir, "*_report.json")))
    thumbs_dir = os.path.join(pdir, "thumbs")
    thumbs = sorted(glob.glob(os.path.join(thumbs_dir, "*.jpg"))) if os.path.isdir(thumbs_dir) else []
    videos: List[str] = []
    for ext in _VALID_EXTS:
        videos.extend(sorted(glob.glob(os.path.join(pdir, f"*__annotated{ext}".replace("__", "_")))))
        videos.extend(sorted(glob.glob(os.path.join(pdir, f"*_annotated{ext}"))))

    return {
        "reports": [os.path.basename(p) for p in reports],
        "annotated_videos": [os.path.basename(v) for v in videos],
        "thumbnails": [os.path.basename(t) for t in thumbs],
        "root": pdir
    }


def svc_startup_warm() -> Dict[str, Any]:
    """For FastAPI startup hook — optional, same as ensure_models but logs model names."""
    _ensure_models()
    return {
        "face_model": True,
        "person_model": True,
        "object_model": _object_model is not None,
        "pose_model": _pose_model is not None,
    }