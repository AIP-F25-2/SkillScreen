# app.services.pipeline.cheating_pipeline.py

from __future__ import annotations
from typing import Dict, Any, List
import numpy as np

from app.core.logging import get_logger
from app.config import settings
from app.helpers.segment_rules import flags_to_segments, SegmenterConfig
from app.services.models_loader import load_yolo, warmup
from app.services.detectors import detect_faces, detect_persons, detect_objects
from app.services.analysis import (
    face_signature, cosine_distance, liveness_micro_motion,
    gaze_center_score, lighting_ok, motion_score, engagement_score
)
from app.services.pose_helper import extract_keypoints

try:
    import cv2  # type: ignore
except Exception:
    cv2 = None

_LOG = get_logger("cheating_pipeline")

PROHIBITED_COCO = { 67: "cell phone", 63: "laptop", 73: "book" }

def analyze_video(input_path: str) -> Dict[str, Any]:
    if cv2 is None:
        return {"ok": False, "reason": "opencv_missing"}

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        return {"ok": False, "reason": "open_failed"}

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0

    face_model = load_yolo(settings.face_model_path, device=0 if settings.use_gpu else None)
    person_model = load_yolo(settings.person_model_path, device=0 if settings.use_gpu else None)
    obj_model = load_yolo(settings.obj_model_path, device=0 if settings.use_gpu else None)
    for m in (face_model, person_model, obj_model):
        warmup(m)

    prev_gray = None
    frame_idx = 0
    frame_skip = settings.initial_frame_skip

    flags_multi_face: List[bool] = []
    flags_multi_person: List[bool] = []
    flags_no_face: List[bool] = []
    flags_prohibited: List[bool] = []
    flags_liveness_low: List[bool] = []

    attn_vals: List[float] = []
    motion_vals: List[float] = []
    live_vals: List[float] = []

    primary_sig = None
    prev_sig = None
    identity_drift_vals: List[float] = []

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_idx += 1
        if frame_idx % frame_skip != 0:
            continue

        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = detect_faces(face_model, frame, max_faces=settings.max_faces)
        persons = detect_persons(person_model, frame, max_people=10)
        objects = detect_objects(obj_model, frame, class_ids=PROHIBITED_COCO.keys(), topk=30)

        multi_face = len(faces) > 1
        multi_person = len(persons) > 1
        no_face = len(faces) == 0
        has_prohibited = len(objects) > 0

        flags_multi_face.append(multi_face)
        flags_multi_person.append(multi_person)
        flags_no_face.append(no_face)
        flags_prohibited.append(has_prohibited)

        m = motion_score(prev_gray, gray)
        prev_gray = gray
        motion_vals.append(m)

        if faces:
            faces_sorted = sorted(faces, key=lambda f: f["conf"], reverse=True)
            f0 = faces_sorted[0]
            sig = face_signature(frame, f0["bbox"])
            if primary_sig is None:
                primary_sig = sig.copy()
            drift = cosine_distance(primary_sig, sig)
            identity_drift_vals.append(drift)

            live = liveness_micro_motion(prev_sig, sig)
            live_vals.append(live)
            prev_sig = sig
            flags_liveness_low.append(live < 0.05)

            attn = gaze_center_score(w, h, f0["bbox"], tol=settings.attn_center_tol)
            attn_vals.append(attn)
        else:
            identity_drift_vals.append(0.0)
            live_vals.append(0.0)
            attn_vals.append(0.0)
            flags_liveness_low.append(False)

        conf_avg = float(np.mean([f["conf"] for f in faces])) if faces else 0.0
        if m < 0.05 and conf_avg >= 0.6:
            frame_skip = min(settings.max_frame_skip, frame_skip + 1)
        else:
            frame_skip = max(settings.min_frame_skip, frame_skip - 1)

    cap.release()

    cfg = SegmenterConfig(min_segment_sec=settings.min_segment_sec, join_gap_sec=settings.join_gap_sec)
    seg_multi_face = flags_to_segments(flags_multi_face, fps, cfg)
    seg_multi_person = flags_to_segments(flags_multi_person, fps, cfg)
    seg_no_face = flags_to_segments(flags_no_face, fps, cfg)
    seg_prohibited = flags_to_segments(flags_prohibited, fps, cfg)
    seg_low_live = flags_to_segments(flags_liveness_low, fps, cfg)

    suspicious_seconds = sum(s["end"] - s["start"] for s in seg_multi_face + seg_multi_person + seg_prohibited)
    cheating_suspected = bool(seg_multi_face or seg_multi_person or seg_prohibited)

    attn = float(np.mean(attn_vals)) if attn_vals else 0.0
    motion_avg = float(np.mean(motion_vals)) if motion_vals else 0.0
    live_avg = float(np.mean(live_vals)) if live_vals else 0.0

    engage = engagement_score(attn, motion_avg, live_avg)

    id_drift_avg = float(np.mean(identity_drift_vals)) if identity_drift_vals else 0.0
    identity_consistent = id_drift_avg <= settings.identity_drift_thresh

    out = {
        "ok": True,
        "fps": fps,
        "frames_seen": frame_idx,
        "duration_sec": frame_idx / fps if fps > 0 else None,
        "events": {
            "MULTIPLE_FACES": seg_multi_face,
            "MULTIPLE_PERSONS": seg_multi_person,
            "NO_PRIMARY_FACE": seg_no_face,
            "PROHIBITED_ITEMS": seg_prohibited,
            "LOW_LIVENESS": seg_low_live
        },
        "metrics": {
            "attention": round(attn, 3),
            "motion_avg": round(motion_avg, 3),
            "liveness_avg": round(live_avg, 3),
            "engagement": round(engage, 3),
            "identity_drift_avg": round(id_drift_avg, 3),
            "identity_consistent": bool(identity_consistent)
        },
        "summary": {
            "cheating_suspected": bool(cheating_suspected),
            "suspicious_seconds": suspicious_seconds,
            "notes": "Cheating suspected on multiple faces/persons or prohibited items. Identity & liveness included."
        }
    }
    return out