# app/services/detectors.py
from __future__ import annotations
from typing import List, Dict, Any, Optional, Iterable
import numpy as np
from app.core.logging import get_logger
from app.config import settings

_LOG = get_logger("detectors")

def _extract(result):
    try:
        boxes = result.boxes
        conf = boxes.conf.detach().cpu().numpy()
        xyxy = boxes.xyxy.detach().cpu().numpy()
        cls = getattr(boxes, "cls", None)
        classes = cls.detach().cpu().numpy() if cls is not None else None
        return xyxy, conf, classes
    except Exception:
        return np.empty((0, 4)), np.empty((0,)), None

def _predict(model, frame):
    if model is None:
        return None
    try:
        return model.predict(frame, stream=False, verbose=False)
    except Exception:
        return None

def detect_faces(model, frame, max_faces: Optional[int] = None) -> List[Dict[str, Any]]:
    res = _predict(model, frame)
    r = res[0] if isinstance(res, (list, tuple)) and res else res
    if r is None:
        _LOG.exception("face inference failed")
        return []
    xyxy, conf, _ = _extract(r)
    if xyxy.size == 0:
        return []
    k = max_faces or settings.MAX_FACES
    order = np.argsort(-conf)[:k]
    out = []
    for i in order:
        b = xyxy[i]
        out.append({"bbox": [int(b[0]), int(b[1]), int(b[2]), int(b[3])], "conf": float(conf[i])})
    return out

def detect_persons(model, frame, max_people: int = 10) -> List[Dict[str, Any]]:
    res = _predict(model, frame)
    r = res[0] if isinstance(res, (list, tuple)) and res else res
    if r is None:
        _LOG.exception("person inference failed")
        return []
    xyxy, conf, classes = _extract(r)
    if xyxy.size == 0 or classes is None:
        return []
    # COCO "person" id is 0 on common YOLO weights
    mask = (classes == 0)
    if not mask.any():
        return []
    xyxy, conf = xyxy[mask], conf[mask]
    order = np.argsort(-conf)[:max_people]
    return [
        {"bbox": [int(xyxy[i][0]), int(xyxy[i][1]), int(xyxy[i][2]), int(xyxy[i][3])], "conf": float(conf[i])}
        for i in order
    ]

def detect_objects(model, frame, class_ids: Iterable[int], topk: int = 20) -> List[Dict[str, Any]]:
    res = _predict(model, frame)
    r = res[0] if isinstance(res, (list, tuple)) and res else res
    if r is None:
        _LOG.exception("object inference failed")
        return []
    xyxy, conf, classes = _extract(r)
    if xyxy.size == 0 or classes is None:
        return []
    mask = np.isin(classes, list(class_ids))
    if not mask.any():
        return []
    xyxy, conf, classes = xyxy[mask], conf[mask], classes[mask]
    order = np.argsort(-conf)[:topk]
    return [
        {
            "bbox": [int(xyxy[i][0]), int(xyxy[i][1]), int(xyxy[i][2]), int(xyxy[i][3])],
            "conf": float(conf[i]),
            "class_id": int(classes[i]),
        }
        for i in order
    ]