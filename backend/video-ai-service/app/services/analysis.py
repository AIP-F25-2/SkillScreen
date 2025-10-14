from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import math

_EPS = 1e-6

def _to_gray(frame: np.ndarray) -> np.ndarray:
    if frame.ndim == 2:
        return frame.astype(np.uint8, copy=False)
    # assume HWC RGB/BGR; using mean keeps it dependency-free
    return frame.mean(axis=2).astype(np.uint8)

def _clip_bbox(bbox: List[int], w: int, h: int) -> Tuple[int, int, int, int]:
    x1, y1, x2, y2 = bbox
    x1 = max(0, min(x1, w))
    y1 = max(0, min(y1, h))
    x2 = max(0, min(x2, w))
    y2 = max(0, min(y2, h))
    return x1, y1, x2, y2

def face_signature(frame: np.ndarray, bbox: List[int]) -> np.ndarray:
    """
    Lightweight proxy embedding: concatenated 3x32-bin histograms (RGB/BGR).
    Falls back to 3 copies of gray hist if frame is grayscale.
    Returns float32 vector length 96 in [0,1], L1-normalized per channel.
    """
    h, w = frame.shape[:2]
    x1, y1, x2, y2 = _clip_bbox(bbox, w, h)
    if x2 <= x1 or y2 <= y1:
        return np.zeros((96,), dtype=np.float32)

    roi = frame[y1:y2, x1:x2]
    if roi.size == 0:
        return np.zeros((96,), dtype=np.float32)

    bins = 32
    if roi.ndim == 2:  # grayscale
        hist = np.histogram(roi, bins=bins, range=(0, 255))[0].astype(np.float32)
        hist /= (hist.sum() + _EPS)
        return np.tile(hist, 3).astype(np.float32, copy=False)

    sig = []
    for ch in range(3):
        hch = np.histogram(roi[:, :, ch], bins=bins, range=(0, 255))[0].astype(np.float32)
        hch /= (hch.sum() + _EPS)
        sig.append(hch)
    return np.concatenate(sig, axis=0).astype(np.float32, copy=False)

def cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    a = a.astype(np.float32, copy=False)
    b = b.astype(np.float32, copy=False)
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na < _EPS or nb < _EPS:
        return 1.0
    return float(1.0 - np.dot(a, b) / (na * nb))

def liveness_micro_motion(prev_sig: Optional[np.ndarray], cur_sig: np.ndarray) -> float:
    if prev_sig is None:
        return 0.1
    d = float(np.linalg.norm(prev_sig.astype(np.float32) - cur_sig.astype(np.float32)))
    return float(min(1.0, d * 2.0))

def gaze_center_score(frame_w: int, frame_h: int, bbox: List[int], tol: float = 0.2) -> float:
    x1, y1, x2, y2 = _clip_bbox(bbox, frame_w, frame_h)
    if x2 <= x1 or y2 <= y1 or tol <= 0:
        return 0.0
    cx = (x1 + x2) * 0.5
    cy = (y1 + y2) * 0.5
    nx = abs((cx / max(1, frame_w)) - 0.5) / tol
    ny = abs((cy / max(1, frame_h)) - 0.5) / tol
    d = math.hypot(nx, ny)
    return float(max(0.0, 1.0 - d))

def lighting_ok(frame: np.ndarray, min_mean: float = 40.0, max_mean: float = 210.0,
                max_saturation_pct: float = 0.05) -> bool:
    if frame.size == 0:
        return False
    gray = _to_gray(frame)
    m = float(gray.mean())
    if not (min_mean <= m <= max_mean):
        return False
    sat_low = (gray <= 2).mean()
    sat_high = (gray >= 253).mean()
    return (sat_low + sat_high) <= max_saturation_pct

def motion_score(prev_gray: Optional[np.ndarray], gray: np.ndarray) -> float:
    g = _to_gray(gray)
    if prev_gray is None or prev_gray.shape != g.shape:
        return 1.0
    pg = _to_gray(prev_gray)
    diff = np.abs(g.astype(np.int16) - pg.astype(np.int16))
    return float(np.clip(diff.mean() / 255.0, 0.0, 1.0))

def engagement_score(attn: float, motion: float, liveness: float) -> float:
    attn = float(np.clip(attn, 0.0, 1.0))
    motion = float(np.clip(motion, 0.0, 1.0))
    liveness = float(np.clip(liveness, 0.0, 1.0))
    score = 0.6 * attn + 0.2 * liveness + 0.2 * (1.0 - abs(motion - 0.15))
    return float(np.clip(score, 0.0, 1.0))