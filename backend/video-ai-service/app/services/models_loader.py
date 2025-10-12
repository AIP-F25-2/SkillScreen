from __future__ import annotations
from app.core.logging import get_logger
from app.helpers.device_select import pick_device
from app.config import settings
import os

_LOG = get_logger("models_loader")

# Public device string for downstream modules
DEVICE = pick_device(use_gpu=settings.USE_GPU)

def load_yolo(weights_path: str, use_gpu: bool = False, use_half: bool = False):
    from ultralytics import YOLO
    model = YOLO(weights_path)
    # place on device once
    if use_gpu and DEVICE == "cuda":
        model.to("cuda")
        if use_half:
            try:
                model.model.half()
            except Exception:
                _LOG.warning("Half precision not supported; using fp32.")
    elif use_gpu and DEVICE == "mps":
        try:
            model.to("mps")
        except Exception:
            _LOG.warning("MPS not available; staying on CPU.")
    return model

def warmup(model):
    try:
        import numpy as np
        img = np.zeros((640, 640, 3), dtype=np.uint8)
        _ = model.predict(img, verbose=False)
    except Exception as e:
        _LOG.warning(f"Warmup skipped: {e}")


# app/services/models_loader.py (append)

def pick_first_existing(candidates):
    for name in candidates:
        path = os.path.join(settings.MODELS_PATH, name)
        if os.path.exists(path):
            return path
    return None