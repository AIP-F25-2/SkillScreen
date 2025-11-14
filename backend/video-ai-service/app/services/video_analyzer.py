from __future__ import annotations

import os
import json
import uuid
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime,timezone
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
from app.utils.config import settings

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


@dataclass
class PoseResult:
    enabled: bool = False
    yaw: float = 0.0
    pitch: float = 0.0
    torso: float = 0.0
    near_hand: bool = False
    eye_open: float = 1.0


@dataclass
class RunContext:
    cap: Any
    writer: Optional[Any]
    width: int
    height: int
    fps: float
    stride: int
    run_ts: str
    run_label: str
    out_video: str
    user_proc_dir: str
    interview_id: str
    session_id: str
    source_url: Optional[str]
    thumbs_dir: str
    gaze_tol: float
    consec_need: int
    pose_thresholds: Tuple[float, float, float]
    blink_gap: int
    blink_enabled: bool
    pose_available: bool
    objects_enabled: bool
    thumbnails_enabled: bool
    draw_annotations: bool
    events: List[Dict[str, Any]] = field(default_factory=list)
    frame_idx: int = 0
    analyzed_frames: int = 0
    prohibited_frames: int = 0
    segments_prohibited: List[Dict[str, Any]] = field(default_factory=list)
    run_len: int = 0
    run_start_t: Optional[float] = None
    last_t: Optional[float] = None
    thumb_counts: Dict[str, int] = field(default_factory=dict)
    look_away_frames: int = 0
    nod_frames: int = 0
    slouch_frames: int = 0
    hand_face_frames: int = 0
    blink_frames: int = 0
    last_blink_fr: int = -999
    pose_runs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    pose_segments: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)

    def close(self) -> None:
        self.cap.release()
        if self.writer is not None:
            self.writer.release()


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

    def _session_dirs(self, interview_id: str, session_id: str) -> Tuple[str, str]:
        upload_dir = os.path.join(settings.UPLOAD_FOLDER, interview_id, session_id)
        processed_dir = os.path.join(settings.PROCESSED_FOLDER, interview_id, session_id)
        os.makedirs(upload_dir, exist_ok=True)
        os.makedirs(processed_dir, exist_ok=True)
        return upload_dir, processed_dir

    def save_upload(self, filename: str, data: bytes, interview_id: str, session_id: str) -> str:
        upload_dir, _ = self._session_dirs(interview_id, session_id)
        uid = uuid.uuid4().hex
        path = os.path.join(upload_dir, f"{session_id}_{uid}_{os.path.basename(filename)}")
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

    def analyze(self, src_video_path: str, interview_id: str, session_id: str, source_url: Optional[str] = None) -> Dict[str, Any]:
        self._ensure_opencv()
        ctx = self._prepare_run_context(src_video_path, interview_id, session_id, source_url)
        self.state.reset()

        try:
            for frame_bgr in self._frame_stream(ctx.cap):
                self._handle_frame(frame_bgr, ctx)
        finally:
            ctx.close()

        segments = self._finalize_segments(ctx)
        summary, perf = self._build_summary_data(ctx, segments)
        thumbs = self._collect_thumbnails(ctx)
        report, result_summary = self._build_report_payload(ctx, segments, summary, perf, thumbs, src_video_path)

        return {
            "ok": True,
            "report": report,
            "report_timestamp": ctx.run_label,
            "video_path": ctx.out_video if ctx.draw_annotations else None,
            "summary": result_summary,
        }

    def _ensure_opencv(self) -> None:
        if cv2 is None:
            raise RuntimeError("OpenCV not available in runtime")

    def _prepare_run_context(self, src_video_path: str, interview_id: str, session_id: str, source_url: Optional[str]) -> RunContext:
        _, user_proc_dir = self._session_dirs(interview_id, session_id)
        _, in_ext = os.path.splitext(src_video_path)
        if not in_ext:
            in_ext = ".mp4"

        cap = cv2.VideoCapture(src_video_path)
        if not cap.isOpened():
            raise ValueError("Failed to open video stream")

        in_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 0
        in_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 0
        in_fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0) or 25.0
        if in_w <= 0 or in_h <= 0:
            cap.release()
            raise ValueError(f"Invalid video dimensions: {in_w}x{in_h}")

        stride = 1 if getattr(settings, "ANALYZE_FULL_FPS", False) else max(1, int(round(in_fps / max(0.1, settings.TARGET_FPS))))
        run_ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        run_label = f"{session_id}_{run_ts}"
        out_video = os.path.join(user_proc_dir, f"{run_label}_annotated{in_ext}")
        writer = cv2.VideoWriter(out_video, self._fourcc(), in_fps, (in_w, in_h)) if settings.DRAW_ANNOTATIONS else None

        ctx = RunContext(
            cap=cap,
            writer=writer,
            width=in_w,
            height=in_h,
            fps=in_fps,
            stride=stride,
            run_ts=run_ts,
            run_label=run_label,
            out_video=out_video,
            user_proc_dir=user_proc_dir,
            interview_id=interview_id,
            session_id=session_id,
            source_url=source_url,
            thumbs_dir=os.path.join(user_proc_dir, "thumbs"),
            gaze_tol=float(getattr(settings, "GAZE_CENTER_TOL", 0.20)),
            consec_need=int(getattr(settings, "PROHIBITED_CONSECUTIVE_FRAMES", 3)),
            pose_thresholds=(
                float(getattr(settings, "HEAD_YAW_DEG_THRESH", 25.0)),
                float(getattr(settings, "HEAD_PITCH_DEG_THRESH", 20.0)),
                float(getattr(settings, "SLOUCH_TORSO_ANGLE_DEG", 35.0)),
            ),
            blink_gap=int(getattr(settings, "BLINK_MIN_GAP_FR", 3)),
            blink_enabled=bool(getattr(settings, "BLINK_ENABLED", True)),
            pose_available=bool(self.pose_model and extract_keypoints and getattr(settings, "POSE_ENABLED", True)),
            objects_enabled=bool(_HAS_OBJECTS and self.object_model is not None),
            thumbnails_enabled=bool(getattr(settings, "EMIT_THUMBNAILS", True)),
            draw_annotations=bool(settings.DRAW_ANNOTATIONS),
        )

        ctx.pose_segments = {
            "look_away": [],
            "nod": [],
            "slouch": [],
            "hand_face": [],
        }
        ctx.pose_runs = self._init_pose_runs(ctx.consec_need, ctx.pose_segments)
        return ctx

    def _init_pose_runs(self, consec_need: int, pose_segments: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
        mapping = {
            "look_away": "look_away",
            "nod": "head_nod",
            "slouch": "slouch",
            "hand_face": "hand_near_face",
        }
        runs: Dict[str, Dict[str, Any]] = {}
        for key, label in mapping.items():
            runs[key] = {
                "name": label,
                "need": consec_need,
                "arr": {"len": 0, "start": None, "last": None},
                "out": pose_segments[key],
            }
        return runs

    def _frame_stream(self, cap) -> Any:
        while True:
            ok, frame_bgr = cap.read()
            if not ok:
                break
            yield frame_bgr

    def _handle_frame(self, frame_bgr, ctx: RunContext) -> None:
        frame_out = frame_bgr
        current_idx = ctx.frame_idx
        t_sec = current_idx / ctx.fps if ctx.fps else 0.0
        if current_idx % ctx.stride == 0:
            frame_out = self._process_analyzable_frame(frame_bgr, t_sec, ctx)
        if ctx.writer is not None:
            ctx.writer.write(frame_out)
        ctx.frame_idx += 1

    def _process_analyzable_frame(self, frame_bgr, t_sec: float, ctx: RunContext):
        faces, persons = self._detect_faces_persons(frame_bgr)
        face_bbox = faces[0]["bbox"] if faces else None
        emo_tmp = self._infer_emotion(frame_bgr, face_bbox)
        objects = self._detect_objects(frame_bgr) if ctx.objects_enabled else None
        if len(faces) > 1 or len(persons) > 1:
            tag = "multi_face" if len(faces) > 1 else "multi_person"
            self._save_thumb(frame_bgr, ctx.thumbs_dir, tag, t_sec, ctx.thumb_counts)
        pose = self._extract_pose(frame_bgr, face_bbox, ctx.pose_available)
        blink_event = self._update_pose_stats(frame_bgr, pose, t_sec, ctx)
        self._update_prohibited_state(objects, t_sec, ctx)
        metrics = self._compute_metrics(frame_bgr, face_bbox, emo_tmp, pose, blink_event, ctx)
        self._append_event(ctx, t_sec, faces, persons, objects, metrics)
        if ctx.writer is not None:
            return self._annotate(frame_bgr, faces or [], persons or [], objects or [])
        return frame_bgr

    def _detect_faces_persons(self, frame_bgr) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        faces = detect_faces(self.face_model, frame_bgr, max_faces=None)
        persons = detect_persons(self.person_model, frame_bgr, max_people=10)
        return faces or [], persons or []

    def _infer_emotion(self, frame_bgr, face_bbox: Optional[List[float]]) -> Dict[str, Any]:
        if not (getattr(settings, "EMOTION_ENABLED", True) and face_bbox):
            return {}
        try:
            from app.services.emotion_helper import infer_emotion, top_emotion
            emo_dist = infer_emotion(frame_bgr, face_bbox)
            if not emo_dist:
                return {}
            emo_tmp: Dict[str, Any] = {"emotion": emo_dist}
            te = top_emotion(emo_dist, min_conf=getattr(settings, "EMOTION_MIN_CONF", 0.35))
            if te:
                emo_tmp["emotion_top"] = {"label": te[0], "conf": te[1]}
            return emo_tmp
        except Exception:
            return {}

    def _detect_objects(self, frame_bgr) -> Optional[List[Dict[str, Any]]]:
        try:
            class_ids = getattr(settings, "PROHIBITED_CLASS_IDS", [67, 73, 63])
            min_conf = float(getattr(settings, "PROHIBITED_MIN_CONF", 0.4))
            raw_objs = detect_objects(self.object_model, frame_bgr, class_ids=class_ids, topk=20)
            return [o for o in (raw_objs or []) if o.get("conf", 0.0) >= min_conf] or None
        except Exception:
            return None

    def _extract_pose(self, frame_bgr, face_bbox: Optional[List[float]], pose_available: bool) -> PoseResult:
        if not pose_available:
            return PoseResult()

        kps = self._pose_keypoints(frame_bgr)
        if kps is None:
            return PoseResult()

        yaw, pitch = self._head_angles(kps)
        torso = self._torso_tilt(kps)
        near_hand = self._hand_face_flag(face_bbox, frame_bgr, kps)
        eye_open = self._eye_open_value(kps)
        return PoseResult(True, yaw, pitch, torso, near_hand, eye_open)

    def _pose_keypoints(self, frame_bgr) -> Optional[Any]:
        try:
            pose = extract_keypoints(self.pose_model, frame_bgr)
        except Exception:
            return None
        if not pose or "kps" not in pose:
            return None
        return pose["kps"]

    def _head_angles(self, kps) -> Tuple[float, float]:
        if not head_pose_proxy:
            return 0.0, 0.0
        try:
            hp = head_pose_proxy(kps)
            return float(hp.get("yaw_deg", 0.0)), float(hp.get("pitch_deg", 0.0))
        except Exception:
            return 0.0, 0.0

    def _torso_tilt(self, kps) -> float:
        if not torso_tilt_deg:
            return 0.0
        try:
            return float(torso_tilt_deg(kps))
        except Exception:
            return 0.0

    def _hand_face_flag(self, face_bbox: Optional[List[float]], frame_bgr, kps) -> bool:
        if face_bbox is None or hand_near_face is None:
            return False
        h, w = frame_bgr.shape[:2]
        try:
            return bool(hand_near_face(
                face_bbox, kps, (w, h),
                iou_thresh=float(getattr(settings, "HAND_NEAR_FACE_IOU", 0.03))
            ))
        except Exception:
            return False

    def _eye_open_value(self, kps) -> float:
        if eye_closure_proxy is None or not getattr(settings, "BLINK_ENABLED", True):
            return 1.0
        try:
            return float(eye_closure_proxy(kps))
        except Exception:
            return 1.0

    def _update_pose_stats(self, frame_bgr, pose: PoseResult, t_sec: float, ctx: RunContext) -> bool:
        if not pose.enabled:
            return False

        yaw_thr, pitch_thr, torso_thr = ctx.pose_thresholds
        if abs(pose.yaw) >= yaw_thr:
            ctx.look_away_frames += 1
            self._save_thumb(frame_bgr, ctx.thumbs_dir, "lookaway", t_sec, ctx.thumb_counts)
        if abs(pose.pitch) >= pitch_thr:
            ctx.nod_frames += 1
            self._save_thumb(frame_bgr, ctx.thumbs_dir, "nod", t_sec, ctx.thumb_counts)
        if pose.torso >= torso_thr:
            ctx.slouch_frames += 1
            self._save_thumb(frame_bgr, ctx.thumbs_dir, "slouch", t_sec, ctx.thumb_counts)
        if pose.near_hand:
            ctx.hand_face_frames += 1
            self._save_thumb(frame_bgr, ctx.thumbs_dir, "handface", t_sec, ctx.thumb_counts)

        self._run_emit(abs(pose.yaw) >= yaw_thr, t_sec, ctx.pose_runs["look_away"])
        self._run_emit(abs(pose.pitch) >= pitch_thr, t_sec, ctx.pose_runs["nod"])
        self._run_emit(pose.torso >= torso_thr, t_sec, ctx.pose_runs["slouch"])
        self._run_emit(pose.near_hand, t_sec, ctx.pose_runs["hand_face"])

        blink_event = False
        if ctx.blink_enabled:
            closed_now = (pose.eye_open < 0.25)
            prev_closed = bool(self.state.__dict__.get("_prev_eye_closed", False))
            if closed_now and not prev_closed and (ctx.frame_idx - ctx.last_blink_fr) >= ctx.blink_gap:
                blink_event = True
                ctx.blink_frames += 1
                ctx.last_blink_fr = ctx.frame_idx
                self._save_thumb(frame_bgr, ctx.thumbs_dir, "blink", t_sec, ctx.thumb_counts)
            else:
                blink_event = False
            self.state.__dict__["_prev_eye_closed"] = closed_now
        return blink_event

    @staticmethod
    def _run_emit(flag: bool, t_sec: float, run: Dict[str, Any]) -> None:
        arr = run["arr"]
        if flag:
            if arr["len"] == 0:
                arr.update(start=t_sec)
            arr["len"] += 1
            arr["last"] = t_sec
            return
        if arr["len"] > 0 and arr["len"] >= run["need"] and arr["start"] is not None and arr["last"] is not None:
            run["out"].append({"type": run["name"], "start": arr["start"], "end": arr["last"]})
        arr.update(len=0, start=None, last=None)

    def _update_prohibited_state(self, objects: Optional[List[Dict[str, Any]]], t_sec: float, ctx: RunContext) -> None:
        has_prohibited = bool(objects)
        if has_prohibited:
            ctx.prohibited_frames += 1
            ctx.run_len += 1
            if ctx.run_len == 1:
                ctx.run_start_t = t_sec
            ctx.last_t = t_sec
            return
        self._close_prohibited_if_needed(ctx)

    def _close_prohibited_if_needed(self, ctx: RunContext) -> None:
        if ctx.run_len >= ctx.consec_need and ctx.run_start_t is not None and ctx.last_t is not None:
            ctx.segments_prohibited.append({"type": "prohibited_item", "start": ctx.run_start_t, "end": ctx.last_t})
        ctx.run_len = 0
        ctx.run_start_t = None
        ctx.last_t = None

    def _compute_metrics(
        self,
        frame_bgr,
        face_bbox: Optional[List[float]],
        emo_tmp: Dict[str, Any],
        pose: PoseResult,
        blink_event: bool,
        ctx: RunContext,
    ) -> Dict[str, Any]:
        metrics = self.state.update(frame_bgr, bbox=face_bbox, gaze_tol=ctx.gaze_tol)
        if emo_tmp:
            metrics.update(emo_tmp)
        if pose.enabled:
            metrics.update({
                "head_yaw_deg": pose.yaw,
                "head_pitch_deg": pose.pitch,
                "torso_tilt_deg": pose.torso,
                "hand_near_face": bool(pose.near_hand),
                "eye_open_proxy": float(pose.eye_open),
            })
            if ctx.blink_enabled:
                metrics["blink_event"] = blink_event
        if "lighting" not in metrics:
            gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
            metrics["lighting"] = float(np.clip(np.mean(gray) / 255.0, 0.0, 1.0))
        return metrics

    def _append_event(
        self,
        ctx: RunContext,
        t_sec: float,
        faces: List[Dict[str, Any]],
        persons: List[Dict[str, Any]],
        objects: Optional[List[Dict[str, Any]]],
        metrics: Dict[str, Any],
    ) -> None:
        ctx.events.append({
            "t": round(t_sec, 3),
            "faces": faces,
            "persons": persons,
            "objects": objects or [],
            "metrics": metrics,
        })
        ctx.analyzed_frames += 1

    def _finalize_segments(self, ctx: RunContext) -> List[Dict[str, Any]]:
        self._close_prohibited_if_needed(ctx)
        self._close_pose_runs(ctx)
        segments = build_segments(ctx.events)
        for segs in ctx.pose_segments.values():
            if segs:
                segments.extend(segs)
        if ctx.segments_prohibited:
            segments.extend(ctx.segments_prohibited)
        segments.sort(key=lambda s: s.get("start", 0.0))
        return segments

    def _close_pose_runs(self, ctx: RunContext) -> None:
        for run in ctx.pose_runs.values():
            arr = run["arr"]
            if arr["len"] >= run["need"] and arr["start"] is not None and arr["last"] is not None:
                run["out"].append({"type": run["name"], "start": arr["start"], "end": arr["last"]})

    def _build_summary_data(self, ctx: RunContext, segments: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        summary = rollup(ctx.events, segments)
        perf = _compute_performance(summary)
        summary["performance"] = perf
        self._inject_emotion_ratios(summary, ctx.events)
        summary["prohibited_ratio"] = self._safe_ratio(ctx.prohibited_frames, ctx.analyzed_frames)
        summary["look_away_ratio"] = self._safe_ratio(ctx.look_away_frames, ctx.analyzed_frames)
        summary["nod_ratio"] = self._safe_ratio(ctx.nod_frames, ctx.analyzed_frames)
        summary["slouch_ratio"] = self._safe_ratio(ctx.slouch_frames, ctx.analyzed_frames)
        summary["hand_near_face_ratio"] = self._safe_ratio(ctx.hand_face_frames, ctx.analyzed_frames)
        summary["blink_ratio"] = self._safe_ratio(ctx.blink_frames, ctx.analyzed_frames)

        if getattr(settings, "CHEAT_FUSION_ENABLED", True):
            weights = getattr(settings, "CHEAT_FUSION_WEIGHTS", {
                "prohibited_ratio": 0.50,
                "look_away_ratio":  0.15,
                "multi_person_ratio": 0.15,
                "hand_near_face_ratio": 0.10,
                "slouch_ratio":     0.05,
                "blink_ratio":      0.05,
            })
            score = 0.0
            for key, alpha in weights.items():
                val = float(summary.get(key, 0.0))
                if key == "blink_ratio":
                    val = max(0.0, 1.0 - val)
                score += float(alpha) * val
            summary["cheating_probability"] = round(float(np.clip(score, 0.0, 1.0)), 3)

        return summary, perf

    def _inject_emotion_ratios(self, summary: Dict[str, Any], events: List[Dict[str, Any]]) -> None:
        emo_frames = 0
        emo_counts: Dict[str, int] = {}
        for event in events:
            emo = event.get("metrics", {}).get("emotion_top")
            if not emo:
                continue
            emo_frames += 1
            label = emo.get("label")
            if label:
                emo_counts[label] = emo_counts.get(label, 0) + 1
        if emo_frames == 0:
            return
        for label, count in emo_counts.items():
            summary[f"emotion_{label}_ratio"] = round(count / emo_frames, 4)
        summary["emotion_frames"] = emo_frames

    @staticmethod
    def _safe_ratio(count: int, denom: int) -> float:
        return round(count / denom, 4) if denom > 0 else 0.0

    def _collect_thumbnails(self, ctx: RunContext) -> List[str]:
        if not ctx.thumbnails_enabled or not os.path.isdir(ctx.thumbs_dir):
            return []
        try:
            rel_root = os.path.join("processed", ctx.interview_id, ctx.session_id, "thumbs")
            return [
                os.path.join(rel_root, name)
                for name in sorted(os.listdir(ctx.thumbs_dir))
                if name.lower().endswith(".jpg")
            ]
        except Exception:
            return []

    def _build_report_payload(
        self,
        ctx: RunContext,
        segments: List[Dict[str, Any]],
        summary: Dict[str, Any],
        perf: Dict[str, Any],
        thumbs: List[str],
        src_video_path: str,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        report = {
            "id": uuid.uuid4().hex,
            "interview_id": ctx.interview_id,
            "session_id": ctx.session_id,
            "timestamp": ctx.run_ts,
            "source_url": ctx.source_url,
            "source_video": os.path.basename(src_video_path),
            "output_video": os.path.basename(ctx.out_video) if ctx.draw_annotations else None,
            "resolution": {"w": ctx.width, "h": ctx.height},
            "input_fps": ctx.fps,
            "sample_stride": ctx.stride,
            "analyzed_fps_est": ctx.fps / ctx.stride,
            "num_frames": ctx.frame_idx,
            "num_frames_analyzed": ctx.analyzed_frames,
            "events": ctx.events,
            "segments": segments,
            "rollup": {"num_segments": len(segments), **summary},
            "performance": perf,
            "thumbnails_dir": (os.path.join(ctx.user_proc_dir, "thumbs") if ctx.thumbnails_enabled else None),
        }

        result_summary = {
            "interview_id": ctx.interview_id,
            "session_id": ctx.session_id,
            "timestamp": ctx.run_ts,
            "source_url": ctx.source_url,
            "num_segments": len(segments), **summary,
            "frames_total": ctx.frame_idx,
            "frames_analyzed": ctx.analyzed_frames,
            "thumbnail_blobs": thumbs,
        }

        return report, result_summary

    # helper for thumbnails
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
