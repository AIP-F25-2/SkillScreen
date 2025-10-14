from __future__ import annotations

import os
import json
import uuid
from typing import Dict, Any, List, Optional, Tuple

import numpy as np

from app.core.logging import get_logger
from app.services.detectors import detect_faces, detect_persons
try:
    from app.services.detectors import detect_objects
    _HAS_OBJECTS = True
except Exception:
    _HAS_OBJECTS = False

# Pose helpers (optional)
try:
    from app.services.pose_helper import (
        extract_keypoints,
        head_pose_proxy,
        torso_tilt_deg,
        hand_near_face,
        eye_closure_proxy,   # NEW: blink proxy
    )
except Exception:
    extract_keypoints = head_pose_proxy = torso_tilt_deg = hand_near_face = eye_closure_proxy = None  # type: ignore

from app.helpers.state_metrics import TrackingState
from app.helpers.segment_rules import build_segments, rollup
from app.config import settings

try:
    import cv2
except Exception:
    cv2 = None

_LOG = get_logger("video_analyzer")

def _clamp01(x: float) -> float:
    return float(max(0.0, min(1.0, x)))

def _score_to_grade(score_0_100: float, bands: dict) -> str:
    if score_0_100 >= bands.get("A", 85): return "A"
    if score_0_100 >= bands.get("B", 70): return "B"
    if score_0_100 >= bands.get("C", 55): return "C"
    return "D"

def _compute_performance(summary: dict) -> dict:
    """
    Turn analytics into a candidate-facing performance summary.
    Uses only existing keys if present. Returns subscores (0..100),
    total (0..100), grade, strengths, concerns, recommendations.
    """
    # ---- Config ----
    W = getattr(settings, "PERFORMANCE_WEIGHTS", {
        "attention": 0.27, "engagement": 0.22, "professionalism": 0.18,
        "presence": 0.15, "integrity": 0.10, "confidence": 0.08,
    })
    T = getattr(settings, "PERF_THRESHOLDS", {
        "lighting_ok_low": 0.35, "look_away_hi": 0.35, "slouch_hi": 0.25, "hand_face_hi": 0.20,
        "prohibited_hi": 0.01, "multi_person_hi": 0.02, "blink_lo": 0.02, "ttff_penalty_s": 3.0
    })
    BANDS = getattr(settings, "PERF_GRADE_BANDS", {"A": 85, "B": 70, "C": 55})

    # ---- Inputs (safe defaults) ----
    attn_ema   = float(summary.get("avg_attention_ema", 0.0))
    engage     = float(summary.get("avg_engagement",    0.0))
    lighting   = float(summary.get("lighting_mean",     0.5))
    look_away  = float(summary.get("look_away_ratio",   0.0))
    slouch     = float(summary.get("slouch_ratio",      0.0))
    handface   = float(summary.get("hand_near_face_ratio", 0.0))
    presence   = float(summary.get("face_presence",     0.0))
    ttff       = float(summary.get("time_to_first_face_sec", 0.0))
    integrity_p= float(summary.get("cheating_probability",  0.0))  # 0=safe .. 1=cheating
    multi_pers = float(summary.get("multi_person_ratio",    0.0))
    prohibited = float(summary.get("prohibited_ratio",      0.0))
    blink_r    = float(summary.get("blink_ratio",           0.03))  # normal-ish default
    emo_top    = summary.get("emotion_top", {})
    emo_label  = emo_top.get("label") if isinstance(emo_top, dict) else None

    # ---- Subscores (0..1) ----
    # Attention: strong camera focus, penalize look-away
    attention_sub = _clamp01(attn_ema * (1.0 - 0.5 * _clamp01(look_away / max(1e-6, T["look_away_hi"]))))

    # Engagement: directly from your engagement metric
    engagement_sub = _clamp01(engage)

    # Professionalism: lighting + posture + hands
    lighting_ok = 1.0 if lighting >= T["lighting_ok_low"] else _clamp01(lighting / T["lighting_ok_low"])
    slouch_ok   = _clamp01(1.0 - slouch / max(1e-6, T["slouch_hi"]))
    hand_ok     = _clamp01(1.0 - handface / max(1e-6, T["hand_face_hi"]))
    professionalism_sub = _clamp01(0.5 * lighting_ok + 0.3 * slouch_ok + 0.2 * hand_ok)

    # Presence: consistent visibility + prompt start
    import numpy as np
    ttff_pen = _clamp01(np.exp(-ttff / max(1e-6, T["ttff_penalty_s"])))  # 1.0 when ttff ~ 0s
    presence_sub = _clamp01(0.7 * presence + 0.3 * ttff_pen)

    # Integrity: few cheating indicators, single-person presence
    integrity_core = _clamp01(1.0 - integrity_p)
    np_pen = _clamp01(1.0 - min(1.0, multi_pers / max(1e-6, T["multi_person_hi"])))
    pr_pen = _clamp01(1.0 - min(1.0, prohibited / max(1e-6, T["prohibited_hi"])))
    integrity_sub = _clamp01(0.6 * integrity_core + 0.25 * np_pen + 0.15 * pr_pen)

    # Confidence: composure from gaze, posture, hands, emotion, blink
    conf_from_gaze = attn_ema
    conf_from_posture = _clamp01(1.0 - slouch / max(1e-6, T["slouch_hi"]))
    conf_from_hand = _clamp01(1.0 - handface / max(1e-6, T["hand_face_hi"]))
    conf_from_emotion = 0.7 if emo_label in ("neutral", "happy", "calm") else 0.4
    conf_from_blink = 1.0 if blink_r >= T["blink_lo"] else 0.6  # extremely low blink => tension
    confidence_sub = _clamp01(
        0.35 * conf_from_gaze +
        0.25 * conf_from_posture +
        0.20 * conf_from_hand +
        0.10 * conf_from_emotion +
        0.10 * conf_from_blink
    )

    # ---- Aggregate to 0..100 ----
    to_pct = lambda x: int(round(100.0 * _clamp01(x)))
    subs = {
        "Attention":       to_pct(attention_sub),
        "Engagement":      to_pct(engagement_sub),
        "Professionalism": to_pct(professionalism_sub),
        "Presence":        to_pct(presence_sub),
        "Integrity":       to_pct(integrity_sub),
        "Confidence":      to_pct(confidence_sub),
    }
    total_0_1 = (
        W["attention"]       * attention_sub +
        W["engagement"]      * engagement_sub +
        W["professionalism"] * professionalism_sub +
        W["presence"]        * presence_sub +
        W["integrity"]       * integrity_sub +
        W["confidence"]      * confidence_sub
    )
    total = to_pct(total_0_1)
    grade = _score_to_grade(total, BANDS)

    # ---- Narrative ----
    strengths, concerns, recs = [], [], []

    # Strengths
    if subs["Attention"] >= 80:       strengths.append("Maintained strong eye contact with the camera.")
    if subs["Engagement"] >= 80:      strengths.append("Demonstrated consistent, natural engagement.")
    if subs["Professionalism"] >= 80: strengths.append("Good environment and professional posture.")
    if subs["Presence"] >= 80:        strengths.append("Face consistently visible; prompt start.")
    if subs["Integrity"] >= 85:       strengths.append("No integrity concerns detected.")
    if subs["Confidence"] >= 80:      strengths.append("Showed calm and confident body language.")

    # Concerns
    if look_away >= T["look_away_hi"]:  concerns.append("Frequent looking away from the screen.")
    if slouch >= T["slouch_hi"]:        concerns.append("Noticeable slouching throughout the interview.")
    if handface >= T["hand_face_hi"]:   concerns.append("Hands frequently near face (possible distraction).")
    if lighting < T["lighting_ok_low"]: concerns.append("Low or uneven lighting.")
    if prohibited > 0.0:                concerns.append("Prohibited item(s) detected on camera.")
    if multi_pers >= T["multi_person_hi"]: concerns.append("Multiple person presence detected in frame.")
    if blink_r <= T["blink_lo"]:        concerns.append("Unusually low blink rate.")
    if subs["Confidence"] < 60:         concerns.append("Body language suggests low confidence.")

    # Recommendations
    if look_away >= T["look_away_hi"]:  recs.append("Keep your eyes near the camera; glance at notes sparingly.")
    if slouch >= T["slouch_hi"]:        recs.append("Sit upright; keep shoulders relaxed and level.")
    if handface >= T["hand_face_hi"]:   recs.append("Keep hands visible and away from face to avoid distractions.")
    if lighting < T["lighting_ok_low"]: recs.append("Improve lighting: face a window or use a soft light source.")
    if prohibited > 0.0:                recs.append("Remove phones/books/laptops not required for the interview.")
    if multi_pers >= T["multi_person_hi"]: recs.append("Ensure you’re alone in a quiet room during the interview.")
    if blink_r <= T["blink_lo"]:        recs.append("Relax your gaze; occasional natural blinking is expected.")
    if subs["Confidence"] < 60:         recs.append("Adopt an open posture, keep your chin level, and steady your gaze.")

    return {
        "score": total,               # 0..100
        "grade": grade,               # A/B/C/D
        "subscores": subs,            # each 0..100 (includes Confidence)
        "strengths": strengths,       # list[str]
        "concerns": concerns,         # list[str]
        "recommendations": recs       # list[str]
    }


class VideoAnalyzer:
    def __init__(self, face_model, person_model, state: TrackingState, object_model=None, pose_model=None):
        self.face_model = face_model
        self.person_model = person_model
        self.object_model = object_model
        self.pose_model = pose_model   # optional
        self.state = state

        os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(settings.PROCESSED_FOLDER, exist_ok=True)

    @staticmethod
    def _fourcc():
        return cv2.VideoWriter_fourcc(*"mp4v")

    def save_upload(self, filename: str, data: bytes) -> str:
        uid = uuid.uuid4().hex
        path = os.path.join(settings.UPLOAD_FOLDER, f"{uid}_{os.path.basename(filename)}")
        with open(path, "wb") as f:
            f.write(data)
        return path

    def _annotate(self, frame_bgr, faces, persons, objects=None):
        if not settings.DRAW_ANNOTATIONS or cv2 is None:
            return frame_bgr
        out = frame_bgr.copy()
        for f in faces or []:
            x1, y1, x2, y2 = [int(v) for v in f["bbox"]]
            cv2.rectangle(out, (x1, y1), (x2, y2), (0, 255, 0), 2)
            if "conf" in f:
                cv2.putText(out, f"face {f['conf']:.2f}", (x1, max(0, y1 - 6)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1, cv2.LINE_AA)
        for p in persons or []:
            x1, y1, x2, y2 = [int(v) for v in p["bbox"]]
            cv2.rectangle(out, (x1, y1), (x2, y2), (255, 140, 0), 2)
            if "conf" in p:
                cv2.putText(out, f"person {p['conf']:.2f}", (x1, max(0, y1 - 6)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 140, 0), 1, cv2.LINE_AA)
        if objects:
            for o in objects:
                x1, y1, x2, y2 = [int(v) for v in o["bbox"]]
                cv2.rectangle(out, (x1, y1), (x2, y2), (200, 200, 255), 2)
                label = str(o.get("name", "obj"))
                conf = o.get("conf")
                txt = f"{label} {conf:.2f}" if conf is not None else label
                cv2.putText(out, txt, (x1, max(0, y1 - 6)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 255), 1, cv2.LINE_AA)
        return out

    @staticmethod
    def _parse_user_ts_from_name(user_id: Optional[str], src_path: str) -> Tuple[Optional[str], Optional[str], str]:
        """
        From a path like UPLOAD_FOLDER/<user>/<user>_<timestamp>.<ext>
        return (user_id, timestamp, ext). If user_id is provided param, trust it; else infer from filename prefix.
        """
        base = os.path.basename(src_path)
        name, ext = os.path.splitext(base)
        inferred_user = user_id
        ts = None
        if inferred_user:
            prefix = f"{inferred_user}_"
            if name.startswith(prefix):
                ts = name[len(prefix):] or None
        else:
            if "_" in name:
                parts = name.split("_", 1)
                inferred_user = parts[0] or None
                ts = parts[1] or None
        return inferred_user, ts, ext or ".mp4"

    def analyze(self, src_video_path: str, user_id: Optional[str] = None, source_url: Optional[str] = None) -> Dict[str, Any]:
        if cv2 is None:
            raise RuntimeError("OpenCV not available in runtime")

        # Derive user & timestamp for output naming/placement
        user_id, ts, in_ext = self._parse_user_ts_from_name(user_id, src_video_path)
        user_proc_dir = os.path.join(settings.PROCESSED_FOLDER, user_id) if user_id else settings.PROCESSED_FOLDER
        os.makedirs(user_proc_dir, exist_ok=True)

        cap = cv2.VideoCapture(src_video_path)
        if not cap.isOpened():
            raise ValueError("Failed to open video stream")

        in_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 0
        in_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 0
        in_fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0) or 25.0
        if in_w <= 0 or in_h <= 0:
            cap.release()
            raise ValueError(f"Invalid video dimensions: {in_w}x{in_h}")

        stride = max(1, int(round(in_fps / max(0.1, settings.TARGET_FPS))))

        # Outputs
        if not ts:
            ts = uuid.uuid4().hex[:8]
        out_video_name = (f"{user_id}_{ts}_annotated{in_ext}") if user_id else f"{ts}_annotated{in_ext}"
        out_json_name = (f"{user_id}_{ts}_report.json") if user_id else f"{ts}_report.json"

        out_video = os.path.join(user_proc_dir, out_video_name)
        writer = cv2.VideoWriter(out_video, self._fourcc(), in_fps, (in_w, in_h)) if settings.DRAW_ANNOTATIONS else None

        self.state.reset()

        events: List[Dict[str, Any]] = []
        frame_idx = 0
        analyzed_frames = 0
        prohibited_frames = 0

        segments_prohibited: List[Dict[str, Any]] = []
        run_len = 0
        run_start_t: Optional[float] = None
        last_t: Optional[float] = None
        consec_need = int(getattr(settings, "PROHIBITED_CONSECUTIVE_FRAMES", 3))

        # Thumbnails (optional)
        thumbs_dir = os.path.join(user_proc_dir, "thumbs")
        thumb_counts: Dict[str, int] = {}

        # Pose-based counters/segments (optional)
        look_away_frames = 0
        nod_frames = 0
        slouch_frames = 0
        hand_face_frames = 0
        seg_lookaway: List[Dict[str, Any]] = []
        seg_nod: List[Dict[str, Any]] = []
        seg_slouch: List[Dict[str, Any]] = []
        seg_handface: List[Dict[str, Any]] = []

        # Blink (optional)
        blink_frames = 0
        last_blink_fr = -999

        def _run_emit(flag: bool, t_sec: float, run):
            name, arr = run["name"], run["arr"]
            if flag:
                if arr["len"] == 0:
                    arr.update(start=t_sec)
                arr["len"] += 1
                arr["last"] = t_sec
            elif arr["len"] > 0:
                if arr["len"] >= run["need"]:
                    run["out"].append({"type": name, "start": arr["start"], "end": arr["last"]})
                arr.update(len=0, start=None, last=None)

        yaw_thr = float(getattr(settings, "HEAD_YAW_DEG_THRESH", 25.0))
        pitch_thr = float(getattr(settings, "HEAD_PITCH_DEG_THRESH", 20.0))
        torso_thr = float(getattr(settings, "SLOUCH_TORSO_ANGLE_DEG", 35.0))
        consec_pose_need = consec_need

        runs = {
            "look_away": {"name": "look_away", "need": consec_pose_need, "arr": {"len": 0, "start": None, "last": None}, "out": seg_lookaway},
            "nod":       {"name": "head_nod",  "need": consec_pose_need, "arr": {"len": 0, "start": None, "last": None}, "out": seg_nod},
            "slouch":    {"name": "slouch",    "need": consec_pose_need, "arr": {"len": 0, "start": None, "last": None}, "out": seg_slouch},
            "hand_face": {"name": "hand_near_face", "need": consec_pose_need, "arr": {"len": 0, "start": None, "last": None}, "out": seg_handface},
        }

        try:
            while True:
                ok, frame_bgr = cap.read()
                if not ok:
                    break

                t_sec = frame_idx / in_fps
                analyze_this = (frame_idx % stride == 0)

                faces: Optional[List[Dict[str, Any]]] = None
                persons: Optional[List[Dict[str, Any]]] = None
                objects: Optional[List[Dict[str, Any]]] = None
                metrics: Optional[Dict[str, Any]] = None

                if analyze_this:
                    faces = detect_faces(self.face_model, frame_bgr, max_faces=None)
                    persons = detect_persons(self.person_model, frame_bgr, max_people=10)

                    face_bbox = faces[0]["bbox"] if faces else None

                    # --- EMOTION (optional): capture into a temp dict first to avoid touching metrics before init ---
                    emo_tmp: Dict[str, Any] = {}
                    if getattr(settings, "EMOTION_ENABLED", True) and face_bbox is not None:
                        try:
                            from app.services.emotion_helper import infer_emotion, top_emotion
                            emo_dist = infer_emotion(frame_bgr, face_bbox)
                            if emo_dist:
                                emo_tmp["emotion"] = emo_dist  # full distribution
                                te = top_emotion(emo_dist, min_conf=getattr(settings, "EMOTION_MIN_CONF", 0.35))
                                if te:
                                    emo_tmp["emotion_top"] = {"label": te[0], "conf": te[1]}
                        except Exception:
                            pass

                    # Objects (existing)
                    if _HAS_OBJECTS and self.object_model is not None:
                        try:
                            class_ids = getattr(settings, "PROHIBITED_CLASS_IDS", [67, 73, 63])
                            min_conf = float(getattr(settings, "PROHIBITED_MIN_CONF", 0.4))
                            raw_objs = detect_objects(self.object_model, frame_bgr, class_ids=class_ids, topk=20)
                            cand_objs = [o for o in (raw_objs or []) if (o.get("conf", 0.0) >= min_conf)]
                            objects = cand_objs
                        except Exception:
                            objects = None

                    # --- Pose (optional) ---
                    yaw = pitch = torso = 0.0
                    near_hand = False
                    eye_open = 1.0
                    use_pose = (
                        self.pose_model is not None and
                        extract_keypoints is not None and
                        getattr(settings, "POSE_ENABLED", True)
                    )
                    if use_pose:
                        try:
                            pose = extract_keypoints(self.pose_model, frame_bgr)
                        except Exception:
                            pose = None
                        if pose and "kps" in pose:
                            kps = pose["kps"]
                            try:
                                hp = head_pose_proxy(kps) if head_pose_proxy else {"yaw_deg": 0.0, "pitch_deg": 0.0}
                                yaw, pitch = float(hp.get("yaw_deg", 0.0)), float(hp.get("pitch_deg", 0.0))
                            except Exception:
                                yaw, pitch = 0.0, 0.0
                            try:
                                torso = float(torso_tilt_deg(kps)) if torso_tilt_deg else 0.0
                            except Exception:
                                torso = 0.0
                            # Hand near face
                            if face_bbox is not None and hand_near_face is not None:
                                h, w = frame_bgr.shape[:2]
                                try:
                                    near_hand = bool(hand_near_face(
                                        face_bbox, kps, (w, h),
                                        iou_thresh=float(getattr(settings, "HAND_NEAR_FACE_IOU", 0.03))
                                    ))
                                except Exception:
                                    near_hand = False
                            # Blink proxy
                            if eye_closure_proxy is not None and getattr(settings, "BLINK_ENABLED", True):
                                try:
                                    eye_open = float(eye_closure_proxy(kps))  # 0..1
                                except Exception:
                                    eye_open = 1.0

                    # Pose counters (added-only)
                    if abs(yaw) >= yaw_thr:
                        look_away_frames += 1
                        self._save_thumb(frame_bgr, thumbs_dir, "lookaway", t_sec, thumb_counts)
                    if abs(pitch) >= pitch_thr:
                        nod_frames += 1
                        self._save_thumb(frame_bgr, thumbs_dir, "nod", t_sec, thumb_counts)
                    if torso >= torso_thr:
                        slouch_frames += 1
                        self._save_thumb(frame_bgr, thumbs_dir, "slouch", t_sec, thumb_counts)
                    if near_hand:
                        hand_face_frames += 1
                        self._save_thumb(frame_bgr, thumbs_dir, "handface", t_sec, thumb_counts)

                    # Pose segments
                    _run_emit(abs(yaw) >= yaw_thr, t_sec, runs["look_away"])
                    _run_emit(abs(pitch) >= pitch_thr, t_sec, runs["nod"])
                    _run_emit(torso >= torso_thr, t_sec, runs["slouch"])
                    _run_emit(near_hand, t_sec, runs["hand_face"])

                    # --- Prohibited (existing) ---
                    has_prohibited = bool(objects)
                    if has_prohibited:
                        prohibited_frames += 1
                        run_len += 1
                        if run_len == 1:
                            run_start_t = t_sec
                        last_t = t_sec
                    else:
                        if run_len >= consec_need and run_start_t is not None and last_t is not None:
                            segments_prohibited.append({"type": "prohibited_item", "start": run_start_t, "end": last_t})
                        run_len = 0
                        run_start_t = None
                        last_t = None

                    # --- Metrics (existing) ---
                    gaze_tol = float(getattr(settings, "GAZE_CENTER_TOL", 0.20))
                    metrics = self.state.update(frame_bgr, bbox=face_bbox, gaze_tol=gaze_tol)

                    # attach emotion if computed earlier
                    if emo_tmp:
                        metrics.update(emo_tmp)

                    # attach pose fields (added-only)
                    if use_pose:
                        metrics.update({
                            "head_yaw_deg": yaw,
                            "head_pitch_deg": pitch,
                            "torso_tilt_deg": torso,
                            "hand_near_face": bool(near_hand),
                            "eye_open_proxy": float(eye_open),
                        })

                        # Blink event (edge with small memory in state; does not alter other logic)
                        if getattr(settings, "BLINK_ENABLED", True):
                            closed_now = (eye_open < 0.25)
                            prev_closed = bool(self.state.__dict__.get("_prev_eye_closed", False))
                            if closed_now and not prev_closed and (frame_idx - last_blink_fr) >= int(getattr(settings, "BLINK_MIN_GAP_FR", 3)):
                                metrics["blink_event"] = True
                                blink_frames += 1
                                last_blink_fr = frame_idx
                                self._save_thumb(frame_bgr, thumbs_dir, "blink", t_sec, thumb_counts)
                            else:
                                metrics["blink_event"] = False
                            self.state.__dict__["_prev_eye_closed"] = closed_now

                    if "lighting" not in metrics:
                        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
                        metrics["lighting"] = float(np.clip(np.mean(gray) / 255.0, 0.0, 1.0))

                    events.append({
                        "t": round(t_sec, 3),
                        "faces": faces or [],
                        "persons": persons or [],
                        "objects": objects or [],
                        "metrics": metrics,
                    })
                    analyzed_frames += 1

                    if writer is not None:
                        frame_bgr = self._annotate(frame_bgr, faces or [], persons or [], objects or [])

                if writer is not None:
                    writer.write(frame_bgr)

                frame_idx += 1

        finally:
            cap.release()
            if writer is not None:
                writer.release()

        # close prohibited run if active
        if run_len >= consec_need and run_start_t is not None and last_t is not None:
            segments_prohibited.append({"type": "prohibited_item", "start": run_start_t, "end": last_t})

        # close pose runs if active
        for key in ("look_away", "nod", "slouch", "hand_face"):
            r = runs[key]["arr"]
            if r["len"] >= runs[key]["need"] and r["start"] is not None and r["last"] is not None:
                runs[key]["out"].append({"type": runs[key]["name"], "start": r["start"], "end": r["last"]})

        # existing segments + add pose & prohibited segments
        segments = build_segments(events)
        for extra in (seg_lookaway, seg_nod, seg_slouch, seg_handface, segments_prohibited):
            if extra:
                segments.extend(extra)
        segments.sort(key=lambda s: s.get("start", 0.0))

        summary = rollup(events, segments)

        # --- Candidate Performance (derived, read-only) ---
        perf = _compute_performance(summary)
        summary["performance"] = perf  # include in returned summary

        # Emotion ratios (only if present)
        emo_counts = {}
        emo_frames = 0
        for e in events:
            em = e.get("metrics", {}).get("emotion_top")
            if not em:
                continue
            emo_frames += 1
            lbl = em.get("label")
            if lbl:
                emo_counts[lbl] = emo_counts.get(lbl, 0) + 1
        if emo_frames > 0:
            for k, v in emo_counts.items():
                summary[f"emotion_{k}_ratio"] = round(v / emo_frames, 4)
            summary["emotion_frames"] = emo_frames

        # Existing ratios
        summary["prohibited_ratio"] = round(prohibited_frames / analyzed_frames, 4) if analyzed_frames > 0 else 0.0

        # Pose-derived ratios (added-only)
        summary["look_away_ratio"] = round(look_away_frames / analyzed_frames, 4) if analyzed_frames > 0 else 0.0
        summary["nod_ratio"] = round(nod_frames / analyzed_frames, 4) if analyzed_frames > 0 else 0.0
        summary["slouch_ratio"] = round(slouch_frames / analyzed_frames, 4) if analyzed_frames > 0 else 0.0
        summary["hand_near_face_ratio"] = round(hand_face_frames / analyzed_frames, 4) if analyzed_frames > 0 else 0.0
        summary["blink_ratio"] = round(blink_frames / analyzed_frames, 4) if analyzed_frames > 0 else 0.0

        # Cheating probability fusion (added-only)
        if getattr(settings, "CHEAT_FUSION_ENABLED", True):
            w = getattr(settings, "CHEAT_FUSION_WEIGHTS", {
                "prohibited_ratio": 0.50,
                "look_away_ratio":  0.15,
                "multi_person_ratio": 0.15,
                "hand_near_face_ratio": 0.10,
                "slouch_ratio":     0.05,
                "blink_ratio":      0.05,  # lower blink => more suspicious; invert below
            })
            score = 0.0
            for k, alpha in w.items():
                v = float(summary.get(k, 0.0))
                if k == "blink_ratio":
                    v = max(0.0, 1.0 - v)  # invert: fewer blinks => higher risk
                score += float(alpha) * v
            summary["cheating_probability"] = round(float(np.clip(score, 0.0, 1.0)), 3)

        report = {
            "id": uuid.uuid4().hex,
            "user_id": user_id,
            "timestamp": ts,
            "source_url": source_url,
            "source_video": os.path.basename(src_video_path),
            "output_video": os.path.basename(out_video) if settings.DRAW_ANNOTATIONS else None,
            "resolution": {"w": in_w, "h": in_h},
            "input_fps": in_fps,
            "sample_stride": stride,
            "analyzed_fps_est": in_fps / stride,
            "num_frames": frame_idx,
            "num_frames_analyzed": analyzed_frames,
            "events": events,
            "segments": segments,
            "rollup": {"num_segments": len(segments), **summary},
             "performance": perf, 
            "thumbnails_dir": (os.path.join(user_proc_dir, "thumbs") if getattr(settings, "EMIT_THUMBNAILS", True) else None),
        }

        out_json = os.path.join(user_proc_dir, out_json_name)
        with open(out_json, "w") as f:
            json.dump(report, f, indent=2)

        return {
            "ok": True,
            "report_path": out_json,
            "video_path": out_video if settings.DRAW_ANNOTATIONS else None,
            "summary": {
                "user_id": user_id,
                "timestamp": ts,
                "source_url": source_url,
                "num_segments": len(segments), **summary,
                "frames_total": frame_idx, "frames_analyzed": analyzed_frames
            }
        }

    # helper for thumbnails
    def _save_thumb(self, frame_bgr, out_dir: str, tag: str, t_sec: float, count: Dict[str,int]) -> Optional[str]:
        if not getattr(settings, "EMIT_THUMBNAILS", True) or cv2 is None:
            return None
        total = sum(count.values())
        if total >= int(getattr(settings, "MAX_THUMBNAILS_PER_RUN", 12)):
            return None
        os.makedirs(out_dir, exist_ok=True)
        idx = count.get(tag, 0) + 1
        count[tag] = idx
        fname = f"thumb_{tag}_{int(t_sec*1000)}.jpg"
        fpath = os.path.join(out_dir, fname)
        cv2.imwrite(fpath, frame_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), int(getattr(settings, "THUMBNAIL_JPEG_QUALITY", 85))])
        return fpath