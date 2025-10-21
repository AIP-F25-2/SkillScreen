# app/services/pose_helper.py
from __future__ import annotations
from typing import Dict, Any, Optional, List, Tuple
import math
import numpy as np

# COCO order used by Ultralytics Pose (17kp):
# 0 nose, 1 left_eye, 2 right_eye, 3 left_ear, 4 right_ear,
# 5 left_shoulder, 6 right_shoulder, 7 left_elbow, 8 right_elbow,
# 9 left_wrist, 10 right_wrist, 11 left_hip, 12 right_hip,
# 13 left_knee, 14 right_knee, 15 left_ankle, 16 right_ankle

def _vec(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return (b - a).astype(np.float32)

def _angle_deg(v1: np.ndarray, v2: np.ndarray) -> float:
    n1 = np.linalg.norm(v1) + 1e-6
    n2 = np.linalg.norm(v2) + 1e-6
    c = float(np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0))
    return float(math.degrees(math.acos(c)))

def extract_keypoints(pose_model, frame_bgr) -> Optional[Dict[str, Any]]:
    """
    Returns {'kps': np.ndarray (17,3)} or None. (x,y,conf) per kp.
    """
    try:
        res = pose_model.predict(frame_bgr, verbose=False)[0]
        if not hasattr(res, "keypoints") or res.keypoints is None or len(res.keypoints) == 0:
            return None
        # take the person with highest confidence
        kps = res.keypoints.data.cpu().numpy()  # (n,17,3)
        if kps.ndim != 3 or kps.shape[1] < 17:
            return None
        # choose the first (best) track
        return {"kps": kps[0]}
    except Exception:
        return None

def head_pose_proxy(kps: np.ndarray) -> Dict[str, float]:
    """
    Rough yaw/pitch from 2D keypoints:
    - yaw  : horizontal deviation of nose vs shoulders midline
    - pitch: vertical ratio nose->shoulders vs shoulders->hips
    """
    # safety
    if kps is None or kps.shape[0] < 13:
        return {"yaw_deg": 0.0, "pitch_deg": 0.0}

    nose = kps[0,:2]
    ls, rs = kps[5,:2], kps[6,:2]
    lh, rh = kps[11,:2], kps[12,:2]

    ctr_sh = (ls + rs) * 0.5
    ctr_hip = (lh + rh) * 0.5
    # yaw: angle between shoulders line and vector shoulders_center->nose
    shoulders_vec = _vec(ls, rs)
    nose_vec = _vec(ctr_sh, nose)
    yaw = _angle_deg(shoulders_vec, nose_vec) - 90.0  # center ~0
    yaw = float(np.clip(yaw, -90, 90))

    # pitch: compare vertical distances; more nose above shoulders → pitch down/up
    sh_to_hip = np.linalg.norm(_vec(ctr_sh, ctr_hip)) + 1e-6
    sh_to_nose = np.linalg.norm(_vec(ctr_sh, nose))
    # scale to degrees-like proxy
    pitch = (sh_to_hip - sh_to_nose) / sh_to_hip * 60.0
    pitch = float(np.clip(pitch, -60, 60))

    return {"yaw_deg": yaw, "pitch_deg": pitch}

def torso_tilt_deg(kps: np.ndarray) -> float:
    """Angle of shoulders→hips vector from vertical; large angle => slouch/lean."""
    if kps is None or kps.shape[0] < 13:
        return 0.0
    ls, rs = kps[5,:2], kps[6,:2]
    lh, rh = kps[11,:2], kps[12,:2]
    ctr_sh = (ls + rs) * 0.5
    ctr_hip = (lh + rh) * 0.5
    v = _vec(ctr_hip, ctr_sh)
    vertical = np.array([0.0, -1.0], dtype=np.float32)
    return _angle_deg(v, vertical)

def hand_near_face(face_bbox: List[int], kps: np.ndarray, frame_wh: Tuple[int,int], pad: int = 30, iou_thresh: float = 0.03) -> bool:
    """True if either wrist's small box overlaps face bbox by IoU >= threshold."""
    if kps is None or kps.shape[0] < 11 or face_bbox is None:
        return False
    w, h = frame_wh
    def _clip(x1,y1,x2,y2):
        return [max(0,min(x1,w)), max(0,min(y1,h)), max(0,min(x2,w)), max(0,min(y2,h))]
    fx1, fy1, fx2, fy2 = face_bbox
    def _iou(a,b):
        ax1, ay1, ax2, ay2 = a; bx1, by1, bx2, by2 = b
        ix1, iy1 = max(ax1,bx1), max(ay1,by1)
        ix2, iy2 = min(ax2,bx2), min(ay2,by2)
        iw, ih = max(0, ix2-ix1), max(0, iy2-iy1)
        inter = iw*ih
        aarea = max(0, ax2-ax1)*max(0, ay2-ay1)
        barea = max(0, bx2-bx1)*max(0, by2-by1)
        denom = aarea + barea - inter + 1e-6
        return inter/denom
    for wi in (9, 10):  # wrists
        cx, cy = int(kps[wi,0]), int(kps[wi,1])
        box = _clip(cx-pad, cy-pad, cx+pad, cy+pad)
        if _iou(box, [fx1,fy1,fx2,fy2]) >= iou_thresh:
            return True
    return False

def eye_closure_proxy(kps: np.ndarray) -> float:
    """
    Returns 0..1 proxy for eye openness.
    Using distance between eyes vs nose/ears baseline as a crude heuristic.
    Larger -> open, Smaller -> closed.
    """
    if kps is None or kps.shape[0] < 5: return 1.0
    le, re = kps[1,:2], kps[2,:2]
    nose   = kps[0,:2]
    baseline = np.linalg.norm(le - re) + 1e-6
    dn_l = np.linalg.norm(le - nose)
    dn_r = np.linalg.norm(re - nose)
    openness = float(((dn_l + dn_r)/2.0) / baseline)
    # normalize roughly to 0..1
    return float(np.clip((openness - 0.6) / 0.5, 0.0, 1.0))