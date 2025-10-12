from __future__ import annotations

import os
import uuid
from shutil import copyfileobj
from urllib.parse import urlparse
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
import glob
from app.core.logging import get_logger
from app.services.models_loader import load_yolo, warmup
from app.helpers.state_metrics import TrackingState
from app.services.video_analyzer import VideoAnalyzer
from app.config import settings

try:
    import cv2
except Exception:
    cv2 = None

router = APIRouter()
_LOG = get_logger("analyze_controller")

_face_model = None
_person_model = None
_object_model = None       # (optional) phone/book/etc.
_pose_model = None         # (optional)
_state = TrackingState(ema_alpha=0.25)

class AnalyzeURLRequest(BaseModel):
    user_id: str
    video_url: str  # path or url; we resolve to local path under UPLOAD_FOLDER

def _ensure_models():
    global _face_model, _person_model, _object_model, _pose_model
    if _face_model is not None and _person_model is not None:
        return
    from app.services.models_loader import pick_first_existing

    face_w = pick_first_existing(settings.FACE_MODEL_CANDIDATES)
    if face_w is None:
        raise RuntimeError("No face model found. Place one of: " + ", ".join(settings.FACE_MODEL_CANDIDATES))
    _face_model = load_yolo(face_w, use_gpu=settings.USE_GPU, use_half=getattr(settings, "USE_HALF", False)); warmup(_face_model)

    person_w = pick_first_existing(settings.PERSON_MODEL_CANDIDATES)
    if person_w is None:
        raise RuntimeError("No person model found. Place one of: " + ", ".join(settings.PERSON_MODEL_CANDIDATES))
    _person_model = load_yolo(person_w, use_gpu=settings.USE_GPU, use_half=getattr(settings, "USE_HALF", False)); warmup(_person_model)

    obj_w = pick_first_existing(settings.OBJECT_MODEL_CANDIDATES)
    if obj_w:
        _object_model = load_yolo(obj_w, use_gpu=settings.USE_GPU, use_half=getattr(settings, "USE_HALF", False)); warmup(_object_model)

    pose_w = pick_first_existing(getattr(settings, "POSE_MODEL_CANDIDATES", []))
    if pose_w:
        _pose_model = load_yolo(pose_w, use_gpu=settings.USE_GPU, use_half=getattr(settings, "USE_HALF", False)); warmup(_pose_model)

def _resolve_local_video_path(user_id: str, video_url: str) -> str:
    """
    Resolve a video path that already exists under:
      UPLOAD_FOLDER/<user_id>/<user_id>_<timestamp>.<ext>
    """
    from urllib.parse import urlparse as _urlparse

    user_dir = os.path.join(settings.UPLOAD_FOLDER, user_id)
    os.makedirs(user_dir, exist_ok=True)

    parsed = _urlparse(video_url)
    if parsed.scheme in ("http", "https"):
        basename = os.path.basename(parsed.path)
        candidate = os.path.join(user_dir, basename)
    else:
        p = video_url
        candidate = p if os.path.isabs(p) else os.path.join(settings.UPLOAD_FOLDER, p)
        # ensure it ends up under user_dir
        if not os.path.commonpath([os.path.abspath(candidate), os.path.abspath(user_dir)]).startswith(os.path.abspath(user_dir)):
            candidate = os.path.join(user_dir, os.path.basename(candidate))

    if not os.path.exists(candidate):
        raise HTTPException(status_code=404, detail=f"Video not found at {candidate}")
    return candidate

@router.get("/status")
def status():
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

@router.post("/reset")
def reset():
    _state.reset()
    return {"ok": True, "msg": "State reset"}

@router.post("/analyze-video")
async def analyze_video(
    user_id: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Upload + analyze: saves to UPLOAD_FOLDER/<user_id>/<user_id>_<timestamp>.<ext>
    and writes outputs to PROCESSED_FOLDER/<user_id>/ with naming:
      <user_id>_<timestamp>_annotated.<ext>, <user_id>_report.json
    """
    if cv2 is None:
        raise HTTPException(status_code=500, detail="OpenCV not available; install opencv-python-headless")

    name = (file.filename or "").lower()
    valid_exts = (".mp4", ".mov", ".mkv", ".avi", ".webm")
    if not name.endswith(valid_exts):
        raise HTTPException(status_code=415, detail=f"Unsupported media type; allowed: {', '.join(valid_exts)}")

    _ensure_models()

    # Build target upload path: UPLOAD_FOLDER/<user_id>/<user_id>_<timestamp>.<ext>
    ext = os.path.splitext(name)[1].lower()
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    user_dir = os.path.join(settings.UPLOAD_FOLDER, user_id)
    os.makedirs(user_dir, exist_ok=True)
    upload_path = os.path.join(user_dir, f"{user_id}_{ts}{ext}")

    # Save uploaded bytes directly to the target path
    data = await file.read()
    with open(upload_path, "wb") as f:
        f.write(data)

    analyzer = VideoAnalyzer(
        face_model=_face_model,
        person_model=_person_model,
        object_model=_object_model,
        pose_model=_pose_model if settings.POSE_ENABLED else None,
        state=_state,
    )
    try:
        result = analyzer.analyze(upload_path, user_id=user_id, source_url=None)
    except Exception as e:
        _LOG.exception("Video analysis failed")
        raise HTTPException(status_code=400, detail=f"Video processing error: {e}")

    return result

@router.post("/analyze-url")
def analyze_url(req: AnalyzeURLRequest):
    """
    Analyze a video already present under UPLOAD_FOLDER/<user_id>/<user_id>_<timestamp>.<ext>.
    """
    if cv2 is None:
        raise HTTPException(status_code=500, detail="OpenCV not available; install opencv-python-headless")

    _ensure_models()

    local_path = _resolve_local_video_path(req.user_id, req.video_url)
    analyzer = VideoAnalyzer(
        face_model=_face_model,
        person_model=_person_model,
        object_model=_object_model,
        state=_state,
    )
    try:
        result = analyzer.analyze(local_path, user_id=req.user_id, source_url=str(req.video_url))
    except Exception as e:
        _LOG.exception("Video analysis failed")
        raise HTTPException(status_code=400, detail=f"Video processing error: {e}")

    return result

@router.on_event("startup")
def _startup():
    from app.services.models_loader import pick_first_existing
    global _face_model, _person_model, _object_model, _pose_model

    face_w = pick_first_existing(settings.FACE_MODEL_CANDIDATES)
    if face_w is None:
        raise RuntimeError("No face model found. Place one of: " + ", ".join(settings.FACE_MODEL_CANDIDATES))
    _face_model = load_yolo(face_w, use_gpu=settings.USE_GPU, use_half=getattr(settings, "USE_HALF", False)); warmup(_face_model)

    person_w = pick_first_existing(settings.PERSON_MODEL_CANDIDATES)
    if person_w is None:
        raise RuntimeError("No person model found. Place one of: " + ", ".join(settings.PERSON_MODEL_CANDIDATES))
    _person_model = load_yolo(person_w, use_gpu=settings.USE_GPU, use_half=getattr(settings, "USE_HALF", False)); warmup(_person_model)

    obj_w = pick_first_existing(settings.OBJECT_MODEL_CANDIDATES)
    if obj_w:
        _object_model = load_yolo(obj_w, use_gpu=settings.USE_GPU, use_half=getattr(settings, "USE_HALF", False)); warmup(_object_model)

    pose_w = pick_first_existing(getattr(settings, "POSE_MODEL_CANDIDATES", []))
    if pose_w:
        _pose_model = load_yolo(pose_w, use_gpu=settings.USE_GPU, use_half=getattr(settings, "USE_HALF", False)); warmup(_pose_model)

    _LOG.info({
        "face_model": os.path.basename(face_w),
        "person_model": os.path.basename(person_w),
        "object_model": os.path.basename(obj_w) if obj_w else None,
        "pose_model": os.path.basename(pose_w) if pose_w else None,
    })


# app/controllers/analyze_controller.py
@router.get("/reports/{user_id}")
def list_reports(user_id: str):
    import glob
    pdir = os.path.join(settings.PROCESSED_FOLDER, user_id)
    if not os.path.isdir(pdir):
        raise HTTPException(404, "user not found")
    reports = glob.glob(os.path.join(pdir, "*_report.json"))
    thumbs = []
    tdir = os.path.join(pdir, "thumbs")
    if os.path.isdir(tdir):
        thumbs = [os.path.join("/processed", user_id, "thumbs", os.path.basename(x)) for x in glob.glob(os.path.join(tdir,"*.jpg"))]
    return {"reports":[os.path.basename(r) for r in reports], "thumbnails": thumbs}


@router.get("/reports/{user_id}")
def list_reports(user_id: str):
    pdir = os.path.join(settings.PROCESSED_FOLDER, user_id)
    if not os.path.isdir(pdir):
        raise HTTPException(404, "User not found")
    reports = sorted(glob.glob(os.path.join(pdir, "*_report.json")))
    thumbs_dir = os.path.join(pdir, "thumbs")
    thumbs = sorted(glob.glob(os.path.join(thumbs_dir, "*.jpg"))) if os.path.isdir(thumbs_dir) else []
    videos = sorted(glob.glob(os.path.join(pdir, "*_annotated.*")))
    return {
        "reports": [os.path.basename(p) for p in reports],
        "annotated_videos": [os.path.basename(v) for v in videos],
        "thumbnails": [os.path.basename(t) for t in thumbs],
        "root": pdir
    }