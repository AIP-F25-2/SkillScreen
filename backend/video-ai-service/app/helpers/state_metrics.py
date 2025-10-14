from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import time
import numpy as np
from numpy.linalg import norm

from app.services.analysis import (
    _to_gray,
    face_signature,
    liveness_micro_motion,
    motion_score,
    gaze_center_score,
    engagement_score,
)

def _cos_sim(a: np.ndarray, b: np.ndarray) -> float:
    if a is None or b is None:
        return 0.0
    d = (norm(a) * norm(b)) or 1e-6
    return float(np.dot(a, b) / d)

@dataclass
class TrackingState:
    """Keeps minimal rolling state for engagement/liveness/motion metrics."""
    prev_gray: Optional[np.ndarray] = None
    prev_face_sig: Optional[np.ndarray] = None
    last_bbox: Optional[List[int]] = None
    last_ts: float = field(default_factory=time.time)

    # Optional running averages (EMA)
    ema_alpha: float = 0.2
    attn_ema: Optional[float] = None
    motion_ema: Optional[float] = None
    live_ema: Optional[float] = None
    engage_ema: Optional[float] = None

    def reset(self) -> None:
        self.prev_gray = None
        self.prev_face_sig = None
        self.last_bbox = None
        self.last_ts = time.time()
        self.attn_ema = self.motion_ema = self.live_ema = self.engage_ema = None

    def _ema(self, prev: Optional[float], x: float) -> float:
        return (self.ema_alpha * x) + ((1.0 - self.ema_alpha) * (prev if prev is not None else x))

    def update(
        self,
        frame: np.ndarray,
        bbox: Optional[List[int]],
        gaze_tol: float = 0.2,
        timestamp: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Update state from current frame and face bbox (x1,y1,x2,y2).
        Returns raw & EMA metrics. If no bbox, returns safe defaults and updates only motion.
        """
        ts = timestamp if timestamp is not None else time.time()

        # Prepare grayscale for motion
        gray = _to_gray(frame)

        # --- MOTION ---
        mot = motion_score(self.prev_gray, gray)

        # --- FACE-DEPENDENT METRICS ---
        if bbox is not None:
            sig = face_signature(frame, bbox)
            live = liveness_micro_motion(self.prev_face_sig, sig)
            attn = gaze_center_score(frame.shape[1], frame.shape[0], bbox, tol=gaze_tol)
            engage = engagement_score(attn, mot, live)

            # Update state
            self.prev_face_sig = sig
            self.last_bbox = bbox
        else:
            # No face this frame — degrade liveness/attention softly
            live = 0.0
            attn = 0.0
            engage = engagement_score(attn, mot, live)
            self.last_bbox = None

        # Commit gray after computing motion
        self.prev_gray = gray
        self.last_ts = ts

        # --- EMA updates ---
        self.attn_ema = self._ema(self.attn_ema, attn)
        self.motion_ema = self._ema(self.motion_ema, mot)
        self.live_ema = self._ema(self.live_ema, live)
        self.engage_ema = self._ema(self.engage_ema, engage)

        return {
            "timestamp": ts,
            "bbox": bbox,
            "attention": attn,
            "motion": mot,
            "liveness": live,
            "engagement": engage,
            "attention_ema": self.attn_ema,
            "motion_ema": self.motion_ema,
            "liveness_ema": self.live_ema,
            "engagement_ema": self.engage_ema,
        }