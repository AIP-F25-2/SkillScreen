from __future__ import annotations
from typing import Dict, Optional, List, Tuple
import numpy as np

try:
    # Option 1: DeepFace (pip install deepface)
    from deepface import DeepFace
    _HAS_DEEPFACE = True
except Exception:
    _HAS_DEEPFACE = False

EMO_ORDER = ["angry","disgust","fear","happy","sad","surprise","neutral"]

def face_crop(frame_bgr: np.ndarray, bbox: List[int]) -> Optional[np.ndarray]:
    x1,y1,x2,y2 = [int(v) for v in bbox]
    h,w = frame_bgr.shape[:2]
    x1,y1 = max(0,x1), max(0,y1)
    x2,y2 = min(w,x2), min(h,y2)
    if x2 <= x1 or y2 <= y1: return None
    return frame_bgr[y1:y2, x1:x2].copy()

def infer_emotion(frame_bgr: np.ndarray, bbox: List[int]) -> Optional[Dict[str,float]]:
    """
    Returns dict like {"happy":0.14, "neutral":0.70, ...} or None.
    Backend: DeepFace (default). Falls back to None if not installed.
    """
    if not _HAS_DEEPFACE: return None
    crop = face_crop(frame_bgr, bbox)
    if crop is None: return None
    try:
        # DeepFace expects RGB
        import cv2
        rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        res = DeepFace.analyze(rgb, actions=["emotion"], enforce_detection=False, prog_bar=False)
        emo = res[0]["emotion"] if isinstance(res, list) else res["emotion"]
        # normalize to 0..1
        total = sum(float(emo.get(k,0.0)) for k in emo)
        if total <= 0: return None
        return {k: float(emo.get(k,0.0))/total for k in EMO_ORDER if k in emo}
    except Exception:
        return None

def top_emotion(emo: Dict[str,float], min_conf: float=0.35) -> Optional[Tuple[str,float]]:
    if not emo: return None
    k = max(emo, key=lambda x: emo[x])
    v = float(emo[k])
    return (k, v) if v >= min_conf else None