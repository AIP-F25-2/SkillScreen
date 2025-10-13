from __future__ import annotations

import os
import glob
import json
from typing import List, Optional, Dict, Any, Tuple

from fastapi import HTTPException

from app.core.logging import get_logger
from app.config import settings
from app.services.video_analyzer import VideoAnalyzer
from app.helpers.state_metrics import TrackingState
from app.services.models_loader import load_yolo, warmup, pick_first_existing
import re
_LOG = get_logger("processed_service")

# ---------- Helpers ----------

VIDEO_EXTS = (".mp4", ".mov", ".mkv", ".avi", ".webm")

def _escape_glob(s: str) -> str:
    return s.replace("[", "[[]").replace("]", "[]]")

def _user_dirs(user_id: str) -> Tuple[str, str]:
    up = os.path.join(settings.UPLOAD_FOLDER, user_id)
    pr = os.path.join(settings.PROCESSED_FOLDER, user_id)
    return up, pr

def _safe_json_load(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read JSON: {e}")

def _write_json(path: str, data: Dict[str, Any]) -> None:
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write JSON: {e}")

def _parse_ts_from_name(name: str, user_id: str) -> Optional[str]:
    base = os.path.basename(name)
    if not base.startswith(f"{user_id}_"):
        return None
    core = base[len(user_id) + 1 :]
    if core.endswith("_annotated.mp4") or any(core.endswith(f"_annotated{e}") for e in VIDEO_EXTS):
        core = core.replace("_annotated", "")
        ts, _ = os.path.splitext(core)
        return ts
    ts, _ = os.path.splitext(core)
    return ts or None

def _find_report(user_id: str, timestamp: str) -> Optional[str]:
    pr = os.path.join(settings.PROCESSED_FOLDER, user_id)
    cand1 = os.path.join(pr, f"{user_id}_{timestamp}_report.json")
    if os.path.isfile(cand1):
        return cand1
    # legacy
    cand2 = os.path.join(pr, f"{user_id}_report.json")
    if os.path.isfile(cand2):
        return cand2
    return None

def _find_annotated_video(user_id: str, timestamp: str) -> Optional[str]:
    pr = os.path.join(settings.PROCESSED_FOLDER, user_id)
    # try exact matches first
    for ext in VIDEO_EXTS:
        p = os.path.join(pr, f"{user_id}_{timestamp}_annotated{ext}")
        if os.path.isfile(p):
            return p
    # fallback: glob any extension
    import glob as _glob
    for p in _glob.glob(os.path.join(pr, f"{user_id}_{timestamp}_annotated.*")):
        if os.path.isfile(p):
            return p
    # also try dash/underscore variant
    ts_alt = timestamp.replace("_", "-")
    for p in _glob.glob(os.path.join(pr, f"{user_id}_{ts_alt}_annotated.*")):
        if os.path.isfile(p):
            return p
    return None

def _list_sessions(user_id: str) -> List[Dict[str, Any]]:
    pr = os.path.join(settings.PROCESSED_FOLDER, user_id)
    if not os.path.isdir(pr):
        return []
    items = []
    for ext in VIDEO_EXTS:
        for vp in glob.glob(os.path.join(pr, f"{user_id}_*{_escape_glob('_annotated')}{ext}")):
            ts = _parse_ts_from_name(vp, user_id) or ""
            rp = _find_report(user_id, ts)
            items.append({"timestamp": ts, "video_path": vp, "report_path": rp})
    for rp in glob.glob(os.path.join(pr, f"{user_id}_*_report.json")):
        ts = rp.replace(os.path.join(pr, f"{user_id}_"), "").replace("_report.json", "")
        if not any(s["timestamp"] == ts for s in items):
            vp = _find_annotated_video(user_id, ts)
            items.append({"timestamp": ts, "video_path": vp, "report_path": rp})
    legacy = os.path.join(pr, f"{user_id}_report.json")
    if os.path.isfile(legacy) and not any(s["report_path"] == legacy for s in items):
        items.append({"timestamp": None, "video_path": None, "report_path": legacy})
    return sorted(items, key=lambda x: (x["timestamp"] or ""))

# ---------- Model cache & init ----------

_face_model = None
_person_model = None
_object_model = None
_pose_model = None
_state = TrackingState(ema_alpha=0.25)

def ensure_models():
    """Lazy model init: usable from controllers & tests."""
    global _face_model, _person_model, _object_model, _pose_model
    if _face_model and _person_model:
        return

    face_w = pick_first_existing(settings.FACE_MODEL_CANDIDATES)
    if not face_w:
        raise HTTPException(500, "Face model not found.")
    _face_model = load_yolo(face_w, use_gpu=settings.USE_GPU, use_half=getattr(settings, "USE_HALF", False)); warmup(_face_model)

    person_w = pick_first_existing(settings.PERSON_MODEL_CANDIDATES)
    if not person_w:
        raise HTTPException(500, "Person model not found.")
    _person_model = load_yolo(person_w, use_gpu=settings.USE_GPU, use_half=getattr(settings, "USE_HALF", False)); warmup(_person_model)

    obj_w = pick_first_existing(getattr(settings, "OBJECT_MODEL_CANDIDATES", []))
    if obj_w:
        _object_model = load_yolo(obj_w, use_gpu=settings.USE_GPU, use_half=getattr(settings, "USE_HALF", False)); warmup(_object_model)

    pose_w = pick_first_existing(getattr(settings, "POSE_MODEL_CANDIDATES", []))
    if pose_w:
        _pose_model = load_yolo(pose_w, use_gpu=settings.USE_GPU, use_half=getattr(settings, "USE_HALF", False)); warmup(_pose_model)

# ---------- Service API (used by controller) ----------

def svc_list_sessions(user_id: str) -> Dict[str, Any]:
    return {"user_id": user_id, "sessions": _list_sessions(user_id)}

def svc_get_report(user_id: str, timestamp: str) -> Dict[str, Any]:
    rp = _find_report(user_id, timestamp)
    if not rp:
        raise HTTPException(404, "Report not found")
    return _safe_json_load(rp)

def svc_get_video_path(user_id: str, timestamp: str) -> str:
    vp = _find_annotated_video(user_id, timestamp)
    if not vp:
        raise HTTPException(404, "Annotated video not found")
    return vp

def svc_list_thumbnails(user_id: str, timestamp: str) -> Dict[str, Any]:
    pr = os.path.join(settings.PROCESSED_FOLDER, user_id)
    thumbs_dir = os.path.join(pr, "thumbs")
    files = sorted(glob.glob(os.path.join(thumbs_dir, "*.jpg"))) if os.path.isdir(thumbs_dir) else []
    return {"user_id": user_id, "timestamp": timestamp, "thumbnails": [os.path.basename(f) for f in files]}

def svc_list_reports(user_id: str, include_summary: bool = True) -> Dict[str, Any]:
    sessions = _list_sessions(user_id)
    out = []
    for s in sessions:
        rp = s.get("report_path")
        if not rp or not os.path.isfile(rp):
            continue
        data = _safe_json_load(rp)
        head = {
            "user_id": data.get("user_id"),
            "timestamp": data.get("timestamp"),
            "report_path": rp,
            "video_path": s.get("video_path"),
        }
        if include_summary:
            rr = data.get("rollup", {})
            perf = data.get("performance", {})
            head["rollup"] = {k: rr.get(k) for k in [
                "num_segments", "avg_attention_ema", "avg_engagement",
                "face_presence", "multi_person_ratio", "prohibited_ratio",
                "lighting_mean", "cheating_probability"
            ] if k in rr}
            head["performance"] = {
                "score": perf.get("score"),
                "grade": perf.get("grade"),
                "subscores": perf.get("subscores"),
            }
        out.append(head)
    return {"user_id": user_id, "reports": out}

def svc_create_process(user_id: str, video_url: str) -> Dict[str, Any]:
    ensure_models()

    # Resolve path
    src = video_url
    if not os.path.isabs(src):
        if src.startswith("/"):
            src = os.path.join(settings.UPLOAD_FOLDER, src.lstrip("/"))
        else:
            src = os.path.join(settings.UPLOAD_FOLDER, user_id, src)

    if not os.path.isfile(src):
        raise HTTPException(404, f"Source video not found: {src}")

    analyzer = VideoAnalyzer(
        face_model=_face_model,
        person_model=_person_model,
        object_model=_object_model,
        pose_model=_pose_model,
        state=_state,
    )
    try:
        result = analyzer.analyze(src_video_path=src, user_id=user_id, source_url=video_url)
    except Exception as e:
        _LOG.exception("Processing failed")
        raise HTTPException(400, f"Processing error: {e}")

    return result

def svc_update_metadata(user_id: str, timestamp: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    rp = _find_report(user_id, timestamp)
    if not rp:
        raise HTTPException(404, "Report not found")
    data = _safe_json_load(rp)
    review = data.get("review", {})

    if "reviewer_notes" in patch and patch["reviewer_notes"] is not None:
        review["notes"] = patch["reviewer_notes"]
    if "decision" in patch and patch["decision"] is not None:
        review["decision"] = patch["decision"]
    if "tags" in patch and patch["tags"] is not None:
        review["tags"] = patch["tags"]
    if "extra" in patch and patch["extra"] is not None:
        review.setdefault("extra", {}).update(patch["extra"])

    data["review"] = review
    _write_json(rp, data)
    return {"ok": True, "report_path": rp, "review": review}

def svc_delete_session(user_id: str, timestamp: str, purge_thumbnails: bool = True) -> Dict[str, Any]:
    pr = os.path.join(settings.PROCESSED_FOLDER, user_id)
    vp = _find_annotated_video(user_id, timestamp)
    rp = _find_report(user_id, timestamp)

    deleted = []
    for p in (vp, rp):
        if p and os.path.isfile(p):
            try:
                os.remove(p)
                deleted.append(p)
            except Exception as e:
                raise HTTPException(500, f"Failed to delete {p}: {e}")

    if purge_thumbnails:
        thumbs_dir = os.path.join(pr, "thumbs")
        if os.path.isdir(thumbs_dir):
            for f in glob.glob(os.path.join(thumbs_dir, "*.jpg")):
                try:
                    os.remove(f)
                except Exception:
                    pass

    return {"ok": True, "deleted": deleted}

def svc_reprocess_session(user_id: str, timestamp: str) -> Dict[str, Any]:
    ensure_models()

    rp = _find_report(user_id, timestamp)
    if not rp:
        raise HTTPException(404, "Report not found")
    report = _safe_json_load(rp)

    source_url = report.get("source_url") or report.get("source_video")
    if not source_url:
        raise HTTPException(400, "Report missing source reference")

    src = source_url
    if not os.path.isabs(src):
        if src.startswith("/"):
            src = os.path.join(settings.UPLOAD_FOLDER, src.lstrip("/"))
        else:
            src = os.path.join(settings.UPLOAD_FOLDER, user_id, src)

    if not os.path.isfile(src):
        raise HTTPException(404, f"Original source video not found: {src}")

    analyzer = VideoAnalyzer(
        face_model=_face_model,
        person_model=_person_model,
        object_model=_object_model,
        pose_model=_pose_model,
        state=_state,
    )
    try:
        result = analyzer.analyze(src_video_path=src, user_id=user_id, source_url=report.get("source_url"))
    except Exception as e:
        _LOG.exception("Reprocessing failed")
        raise HTTPException(400, f"Reprocessing error: {e}")

    return result


# --- helper: derive timestamp from a video filename like "<user>_<ts>.<ext>" ---
_TS_RE = re.compile(r"^(?P<uid>[^_/]+)_(?P<ts>\d{8}[_-]?\d{6})")

def _extract_ts_from_basename(user_id: str, basename: str) -> Optional[str]:
    """
    Accepts: '1_20251007_153437.mp4' or '1_20251007-153437.mov'
    Returns just the timestamp '20251007_153437' (normalizes '-' to '_').
    """
    base_no_ext, _ = os.path.splitext(basename)
    m = _TS_RE.match(base_no_ext)
    if not m:
        return None
    if m.group("uid") != user_id:
        return None
    ts = m.group("ts").replace("-", "_")
    return ts

def _delete_file_if_exists(path: Optional[str], deleted: list) -> None:
    _LOG.info("Deleting file path: " + str(path))
    if path and os.path.isfile(path):
        os.remove(path)
        deleted.append(path)

# ---------------------------
# NEW: delete by processed filename
# ---------------------------
def svc_delete_by_name(user_id: str, name: str, purge_thumbnails: bool = True, delete_upload: bool = False) -> Dict[str, Any]:
    """
    Delete artifacts in processed/<user_id>/ by giving an exact filename found there.
    - If 'name' is a report like '<uid>_<ts>_report.json', the matching annotated video (any ext) is removed too.
    - If 'name' is an annotated video '<uid>_<ts>_annotated.<ext>', the matching report is removed too.
    - If delete_upload=True, the original upload in uploads/<user_id>/ is also deleted (if resolvable).
    """
    pr = os.path.join(settings.PROCESSED_FOLDER, user_id)
    if not os.path.isdir(pr):
        raise HTTPException(404, f"user '{user_id}' has no processed directory")

    target_path = os.path.join(pr, name)
    if not os.path.isfile(target_path):
        raise HTTPException(404, f"file not found in processed: {name}")

    ts = None
    if name.endswith("_report.json"):
        ts = name.replace(f"{user_id}_", "", 1).replace("_report.json", "")
    elif "_annotated." in name:
        ts = _extract_ts_from_basename(user_id, name)

    deleted: List[str] = []
    # Remove the target file
    _delete_file_if_exists(target_path, deleted)
    # Remove counterpart (report <-> video) if timestamp is found
    if ts:
        # report (both underscore & dash forms)
        for t in (ts, ts.replace("_", "-")):
            rp = os.path.join(pr, f"{user_id}_{t}_report.json")
            _delete_file_if_exists(rp, deleted)
        # annotated video (robust finder)
        vp = _find_annotated_video(user_id, ts)
        _delete_file_if_exists(vp, deleted)
        # thumbnails purge (optional)
        if purge_thumbnails:
            thumbs_dir = os.path.join(pr, "thumbs")
            if os.path.isdir(thumbs_dir):
                for f in glob.glob(os.path.join(thumbs_dir, "*.jpg")):
                    try: os.remove(f)
                    except Exception: pass

        # optionally delete upload source
        if delete_upload:
            up, _ = _user_dirs(user_id)
            # try both underscore and dash variants
            cand_uploads = []
            for ext in (".mp4", ".mov", ".mkv", ".avi", ".webm"):
                cand_uploads.append(os.path.join(up, f"{user_id}_{ts}{ext}"))
                cand_uploads.append(os.path.join(up, f"{user_id}_{ts.replace('_','-')}{ext}"))
            for p in cand_uploads:
                _delete_file_if_exists(p, deleted)

    return {"ok": True, "deleted": deleted}

# ---------------------------
# NEW: delete by URL (or bare filename)
# ---------------------------
def svc_delete_by_url(user_id: str, video_url: str, purge_thumbnails: bool = True, delete_upload: bool = False) -> Dict[str, Any]:
    base = os.path.basename(video_url.strip())
    ts = _extract_ts_from_basename(user_id, base)
    if not ts:
        raise HTTPException(400, f"could not parse timestamp from '{video_url}' (expected '<user>_<YYYYMMDD>_<HHMMSS>.ext')")

    pr = os.path.join(settings.PROCESSED_FOLDER, user_id)
    if not os.path.isdir(pr):
        raise HTTPException(404, f"user '{user_id}' has no processed directory")

    attempted = []
    deleted: List[str] = []

    # delete report (try underscore & dash variants)
    for t in (ts, ts.replace("_", "-")):
        rp = os.path.join(pr, f"{user_id}_{t}_report.json")
        attempted.append(rp)
        _delete_file_if_exists(rp, deleted)

    # delete annotated video (any extension, robust finder)
    vp = _find_annotated_video(user_id, ts)
    if vp:
        attempted.append(vp)
        _delete_file_if_exists(vp, deleted)
    else:
        attempted.append(os.path.join(pr, f"{user_id}_{ts}_annotated.*"))

    # purge thumbnails
    if purge_thumbnails:
        thumbs_dir = os.path.join(pr, "thumbs")
        if os.path.isdir(thumbs_dir):
            import glob as _glob
            for f in _glob.glob(os.path.join(thumbs_dir, "*.jpg")):
                try: os.remove(f)
                except Exception: pass

    # optionally delete upload
    if delete_upload:
        up, _ = _user_dirs(user_id)
        for ext in VIDEO_EXTS:
            for t in (ts, ts.replace("_", "-")):
                cand = os.path.join(up, f"{user_id}_{t}{ext}")
                attempted.append(cand)
                _delete_file_if_exists(cand, deleted)

    return {"ok": True, "deleted": deleted, "attempted": attempted}
