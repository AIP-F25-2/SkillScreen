# app/helpers/device_select.py
import torch

def pick_device(use_gpu: bool = True) -> str:
    try:
        if use_gpu and torch.cuda.is_available():
            return "cuda"
        # Apple Silicon fallback
        if use_gpu and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        return "cpu"
    except Exception:
        return "cpu"