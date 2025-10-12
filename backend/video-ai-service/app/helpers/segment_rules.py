# app/helpers/segment_rules.py
from __future__ import annotations
from typing import List, Dict, Any, Optional
import numpy as np
from app.config import settings

def _within_gap(prev_t: Optional[float], t: float) -> bool:
    if prev_t is None:
        return True
    return (t - prev_t) <= settings.JOIN_GAP_SEC

def _close_if_long(seg: Optional[Dict[str, Any]], out: List[Dict[str, Any]]) -> None:
    if not seg:
        return
    dur = seg["end"] - seg["start"]
    if dur >= settings.MIN_SEGMENT_SEC:
        out.append(seg)

def build_segments(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert sampled per-frame events -> labeled temporal segments.
    Labels:
      - no_face
      - multi_person
      - prohibited_item (phone/book/etc.)
      - offscreen_gaze
      - stillness_liveness
      - low_attention
      - low_light
    """
    if not events:
        return []

    segs: List[Dict[str, Any]] = []
    cur = {k: None for k in [
        "no_face", "multi_person", "prohibited_item",
        "offscreen_gaze", "stillness_liveness", "low_attention", "low_light"
    ]}

    last_t: Optional[float] = None
    offscreen_run = 0.0
    stillness_run = 0.0

    def open_seg(label: str, t: float, meta: Optional[Dict[str, Any]] = None):
        if cur[label] is None:
            cur[label] = {"type": label, "start": t, "end": t}
            if meta:
                cur[label].update(meta)

    def extend_or_close(label: str, t: float, contiguous: bool):
        s = cur[label]
        if s is None:
            return
        if contiguous:
            s["end"] = t
        else:
            _close_if_long(s, segs)
            cur[label] = None

    for e in events:
        t = float(e["t"])
        faces = e.get("faces") or []
        persons = e.get("persons") or []
        objects = e.get("objects") or []
        m = e.get("metrics") or {}

        # metric fallbacks (your sample doesn't have offscreen_prob; default 0)
        att_ema = float(m.get("attention_ema", 0.0))
        mot_ema = float(m.get("motion_ema", 0.0))
        off_p   = float(m.get("offscreen_prob", 0.0))
        lighting = float(m.get("lighting", 1.0))
        has_face = len(faces) > 0

        dt = 0.0 if last_t is None else max(0.0, t - last_t)
        contiguous = _within_gap(last_t, t)

        # Conditions
        cond_no_face = not has_face
        cond_multi_person = len(persons) > settings.PERSON_MAX
        cond_low_attention = has_face and (att_ema < settings.ATTENTION_TH)
        cond_low_light = lighting <= settings.LIGHT_TH

        # Offscreen (if you don't compute offscreen_prob, you can derive from attention if desired)
        if has_face and off_p >= settings.OFFSCREEN_TH:
            offscreen_run += dt
        else:
            offscreen_run = 0.0
        cond_offscreen = offscreen_run >= settings.OFFSCREEN_MIN_SEC

        # Stillness (loop/spoof risk)
        if has_face and mot_ema <= settings.STILLNESS_MOTION_TH:
            stillness_run += dt
        else:
            stillness_run = 0.0
        cond_stillness = stillness_run >= settings.STILLNESS_MIN_SEC

        # Prohibited items
        any_prohibited = False
        which_item: Optional[str] = None
        if objects:
            for o in objects:
                name = str(o.get("name", "")).lower()
                if name in settings.PROHIBITED_CLASSES:
                    any_prohibited = True
                    which_item = name
                    break

        # Open/extend/close for each label
        for label, is_on, meta in [
            ("no_face", cond_no_face, None),
            ("multi_person", cond_multi_person, {"max_people": len(persons)} if cond_multi_person else None),
            ("prohibited_item", any_prohibited, {"item": which_item} if any_prohibited else None),
            ("offscreen_gaze", cond_offscreen, None),
            ("stillness_liveness", cond_stillness, None),
            ("low_attention", cond_low_attention, None),
            ("low_light", cond_low_light, None),
        ]:
            if is_on:
                if cur[label] is None:
                    open_seg(label, t, meta)
                else:
                    extend_or_close(label, t, contiguous=True)
            else:
                extend_or_close(label, t, contiguous=False)

        last_t = t

    # Close any open segment
    for label in list(cur.keys()):
        _close_if_long(cur[label], segs)
        cur[label] = None

    return segs


def rollup(events: List[Dict[str, Any]], segments: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not events:
        return {
            "face_presence": 0.0,
            "avg_engagement": 0.0,
            "offscreen_fraction": 0.0,
            "time_to_first_face_sec": None,
            "multi_person_ratio": 0.0,
            "avg_attention_ema": 0.0,
            "avg_motion_ema": 0.0,
            "avg_face_conf": None,
            "lighting_mean": None,
            "num_segments": 0,
        }

    has_face = np.array([1.0 if (e.get("faces") or []) else 0.0 for e in events], dtype=float)
    att = np.array([ (e.get("metrics") or {}).get("attention_ema", 0.0) for e in events ], dtype=float)
    eng = np.array([ (e.get("metrics") or {}).get("engagement_ema", 0.0) for e in events ], dtype=float)
    mot = np.array([ (e.get("metrics") or {}).get("motion_ema", 0.0) for e in events ], dtype=float)
    off = np.array([ (e.get("metrics") or {}).get("offscreen_prob", 0.0) for e in events ], dtype=float)
    light = np.array([ (e.get("metrics") or {}).get("lighting", np.nan) for e in events ], dtype=float)

    # time to first face
    t_first = next((float(e["t"]) for e in events if (e.get("faces") or [])), None)
    multi = np.array([ 1.0 if len(e.get("persons") or []) > 1 else 0.0 for e in events ], dtype=float)

    # average face confidence (top face)
    face_confs = []
    for e in events:
        fs = e.get("faces") or []
        if fs:
            face_confs.append(float(fs[0].get("conf", 0.0)))
    avg_face_conf = float(np.mean(face_confs)) if face_confs else None

    lighting_mean = float(np.nanmean(light)) if np.isfinite(light).any() else None

    return {
        "face_presence": round(float(np.mean(has_face)), 4),
        "avg_engagement": round(float(np.mean(eng)), 4),
        "offscreen_fraction": round(float(np.mean(off)), 4),
        "time_to_first_face_sec": None if t_first is None else round(t_first, 3),
        "multi_person_ratio": round(float(np.mean(multi)), 4),
        "avg_attention_ema": round(float(np.mean(att)), 4),
        "avg_motion_ema": round(float(np.mean(mot)), 4),
        "avg_face_conf": None if avg_face_conf is None else round(avg_face_conf, 4),
        "lighting_mean": None if lighting_mean is None else round(lighting_mean, 4),
        "num_segments": len(segments),
    }