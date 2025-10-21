# app/config.py
import os

def _get_bool(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip() in ("1", "true", "TRUE", "yes", "YES")

def _get_json(name: str, default: str):
    try:
        return json.loads(os.getenv(name, default))
    except Exception:
        return json.loads(default)

class Settings:
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))
    APP_NAME: str = os.getenv("APP_NAME", "anti_cheat_service")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_JSON: bool = _get_bool("LOG_JSON", "1")

    USE_GPU: bool = _get_bool("USE_GPU", "0")
    USE_HALF: bool = _get_bool("USE_HALF", "0")

    FACE_MODEL_PATH: str = os.getenv("FACE_MODEL_PATH", "models/yolov8n-face.pt")
    POSE_MODEL_PATH: str = os.getenv("POSE_MODEL_PATH", "models/yolov8n-pose.pt")
    PERSON_MODEL_PATH: str = os.getenv("PERSON_MODEL_PATH", "models/yolo11n.pt")
    OBJ_MODEL_PATH: str = os.getenv("OBJ_MODEL_PATH", "models/yolo11n-obb.pt")

    UPLOADS_HOST_VOLUME_MOUNT_PATH: str = os.getenv("UPLOADS_HOST_VOLUME_MOUNT_PATH", "/Users/mukulgarg/Downloads/AIP_backup/video_recordings/")
    PROCESSED_HOST_VOLUME_MOUNT_PATH: str = os.getenv("PROCESSED_HOST_VOLUME_MOUNT_PATH", "/Users/mukulgarg/Downloads/AIP_backup/processed_videos/")
    CHEATING_MODEL_PATH: str = os.getenv("CHEATING_MODEL_PATH", "/Users/mukulgarg/Downloads/anti_cheat_service_mvc/models")

    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "/app/uploads")
    PROCESSED_FOLDER: str = os.getenv("PROCESSED_FOLDER", "/app/processed")
    MODELS_PATH: str = os.getenv("MODELS_PATH", "/app/models")

    UPLOADS_DIR: str = os.getenv("UPLOADS_DIR", "/app/uploads")
    PROCESSED_DIR: str = os.getenv("PROCESSED_DIR", "/app/processed")

    MAX_FACES: int = int(os.getenv("MAX_FACES", "3"))
    INITIAL_FRAME_SKIP: int = int(os.getenv("INITIAL_FRAME_SKIP", "1"))
    MAX_FRAME_SKIP: int = int(os.getenv("MAX_FRAME_SKIP", "6"))
    MIN_FRAME_SKIP: int = int(os.getenv("MIN_FRAME_SKIP", "1"))

    MIN_SEGMENT_SEC: float = float(os.getenv("MIN_SEGMENT_SEC", "1.0"))
    JOIN_GAP_SEC: float = float(os.getenv("JOIN_GAP_SEC", "0.5"))

    LIVENESS_STILL_SEC: float = float(os.getenv("LIVENESS_STILL_SEC", "5.0"))
    IDENTITY_DRIFT_THRESH: float = float(os.getenv("IDENTITY_DRIFT_THRESH", "0.25"))

    ATTN_CENTER_TOL: float = float(os.getenv("ATTN_CENTER_TOL", "0.2"))
    ATTENTION_TH: float = float(os.getenv("ATTENTION_TH", "0.45"))
    OFFSCREEN_TH: float = float(os.getenv("OFFSCREEN_TH", "0.60"))
    OFFSCREEN_MIN_SEC: float = float(os.getenv("OFFSCREEN_MIN_SEC", "1.5"))

    STILLNESS_MOTION_TH: float = float(os.getenv("STILLNESS_MOTION_TH", "0.02"))
    STILLNESS_MIN_SEC: float = float(os.getenv("STILLNESS_MIN_SEC", "2.0"))

    ID_DRIFT_TH: float = float(os.getenv("ID_DRIFT_TH", "0.25"))

    PERSON_MAX: int = int(os.getenv("PERSON_MAX", "1"))
    LIGHT_TH: float = float(os.getenv("LIGHT_TH", "0.25"))

    # Lighting-aware adaptation
    LIGHTING_GOOD_MIN: float = float(os.getenv("LIGHTING_GOOD_MIN", "0.45"))
    ATTENTION_BASELINE: float = float(os.getenv("ATTENTION_BASELINE", "0.50"))
    ATTENTION_BONUS_GOOD_LIGHT: float = float(os.getenv("ATTENTION_BONUS_GOOD_LIGHT", "0.08"))

    PROHIBITED_CLASSES = {
        s.strip().lower()
        for s in os.getenv("PROHIBITED_CLASSES", "phone,book,note,earbud,headphone,tablet").split(",")
        if s.strip()
    }
    # Example with class IDs for phone/book/laptop: 67,73,63 on COCO
    # COCO IDs to flag as prohibited / suspicious for interviews
    PROHIBITED_CLASS_IDS = [62, 63, 67, 73, 77]
    PROHIBITED_MIN_CONF = 0.4   # ignore detections below this confidence
    PROHIBITED_FRAME_RATIO_THRESH = 0.03  # e.g., 3% of analyzed frames
    PROHIBITED_CONSECUTIVE_FRAMES = 3     # require 3 sampled frames in a row to confirm

    CHEATING_MODEL_PATH: str = os.getenv("CHEATING_MODEL_PATH", "/app/models/cheating_classifier_incremental.pkl")

    HEAD_YAW_AWAY_DEG: float = float(os.getenv("HEAD_YAW_AWAY_DEG", "25"))
    HEAD_PITCH_AWAY_DEG: float = float(os.getenv("HEAD_PITCH_AWAY_DEG", "20"))
    GAZE_CENTER_TOL: float = float(os.getenv("GAZE_CENTER_TOL", "0.20"))

    TARGET_FPS: float = float(os.getenv("TARGET_FPS", "5"))
    MIN_SEGMENT_SEC: float = float(os.getenv("MIN_SEGMENT_SEC", "1.0"))
    JOIN_GAP_SEC: float = float(os.getenv("JOIN_GAP_SEC", "0.5"))
    DRAW_ANNOTATIONS: bool = _get_bool("DRAW_ANNOTATIONS", "1")

    # app/config.py (add/adjust these defaults)

    # Where models live
    MODELS_PATH: str = os.getenv("MODELS_PATH", "/app/models")

    # Preferred → fallback (we pick the first file that exists)
    FACE_MODEL_CANDIDATES = [
        "yolov8n-face.pt",           # lightweight face
        "yolov9e-face-lindevs.pt",   # higher accuracy face
    ]

    PERSON_MODEL_CANDIDATES = [
        "yolo11n.pt",                
        "yolo11m.pt",                # balanced accuracy/speed
        "yolo11s.pt",                # faster
        "yolo11l.pt",                # highest accuracy among 11 (slower)
    ]

    OBJECT_MODEL_CANDIDATES = [
        "yolo11n-obb.pt",                # also COCO; works fine too
        "yolov8n-obb.pt",                # COCO objects (phone/book/laptop)
        "yolo11s-obb.pt",                # also COCO; works fine too
    ]

    POSE_MODEL_CANDIDATES = [
        "yolo11n-pose.pt",
        "yolo11m-pose.pt",
        "yolov8x-pose.pt",
        "yolo11s-pose.pt",
    ]

    SEG_MODEL_CANDIDATES = [
        "yolo11n-seg.pt",
        "yolo11m-seg.pt",
        "yolo11s-seg.pt",
        "yolo11l-seg.pt",
    ]

    OBB_MODEL_CANDIDATES = [
        "yolo11n-obb.pt",
        "yolo11m-obb.pt",
        "yolo11s-obb.pt",
        "yolo11l-obb.pt",
    ]


    # app/config.py (inside Settings)
    POSE_ENABLED = True                     # turn on pose-based features
    AUDIO_ENABLED = False                   # off by default; turns on if deps available
    EMIT_THUMBNAILS = False                  # save snapshots for flagged events

    # thresholds (tune later)
    HEAD_YAW_DEG_THRESH = 25.0              # left/right look
    HEAD_PITCH_DEG_THRESH = 20.0            # up/down nod
    HAND_NEAR_FACE_IOU = 0.03               # ~overlap between face bbox & wrist 30x30 box
    SLOUCH_TORSO_ANGLE_DEG = 35.0           # torso tilt angle from vertical

    
    # thumbnails
    THUMBNAIL_JPEG_QUALITY = 85
    MAX_THUMBNAILS_PER_RUN = 12

    EMOTION_ENABLED = True
    EMOTION_BACKEND = "deepface"     # or "ferplus"
    EMOTION_TOPK = 1                 # keep 1 strongest label
    EMOTION_MIN_CONF = 0.35          # soft minimum

    BLINK_ENABLED = True
    BLINK_MIN_GAP_FR = 3        # frames between consecutive blinks
    BLINK_EYE_ASPECT_THR = 0.19 # if using landmarks; for pose-only fallback use eye-area heuristic

    CHEAT_FUSION_ENABLED = True
    CHEAT_FUSION_WEIGHTS = {
        "prohibited_ratio": 0.50,
        "look_away_ratio":  0.15,
        "multi_person_ratio": 0.15,
        "hand_near_face_ratio": 0.10,
        "slouch_ratio":     0.05,
        "blink_ratio":      0.05   # e.g., unusually low blink rate → suspicious; invert if desired
    }

    # Scoring weights (sum to 1.0)
    PERFORMANCE_WEIGHTS = {
        "attention":        0.27,
        "engagement":       0.22,
        "professionalism":  0.18,
        "presence":         0.15,
        "integrity":        0.10,
        "confidence":       0.08,
    }

    # Thresholds
    PERF_THRESHOLDS = {
        "lighting_ok_low":  0.35,
        "look_away_hi":     0.35,
        "slouch_hi":        0.25,
        "hand_face_hi":     0.20,
        "prohibited_hi":    0.01,
        "multi_person_hi":  0.02,
        "blink_lo":         0.02,
        "ttff_penalty_s":   3.0,
    }

    # Grade bands
    PERF_GRADE_BANDS = { "A": 85, "B": 70, "C": 55 }



settings = Settings()