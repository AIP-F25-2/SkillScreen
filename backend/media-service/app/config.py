# import os
# from datetime import timedelta

# class Config:
#     SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
#     SERVER_PORT = int(os.getenv("SERVER_PORT", 5004))
#     UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "temp/uploads")
#     MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_BYTES", 500 * 1024 * 1024))
#     CORS_SUPPORTS_CREDENTIALS = True
#     SEND_FILE_MAX_AGE_DEFAULT = timedelta(days=7)

#     # Storage configuration
#     USE_AZURE_STORAGE = os.getenv("USE_AZURE_STORAGE", "true").lower() == "true"
#     AZURE_BLOB_CONTAINER_URL = os.environ.get("AZURE_BLOB_CONTAINER_URL", "https://skillscreenstorage.blob.core.windows.net/video-recordings?sp=racwdl&st=2025-11-04T14:56:17Z&se=2025-12-31T23:11:17Z&spr=https&sv=2024-11-04&sr=c&sig=7nu5Z5vcJrIuL0ivanRi3BHfHv%2FAPtHycpnhvubw0is%3D")
#     AZURE_BLOB_ACCOUNT_URL = os.environ.get("AZURE_BLOB_ACCOUNT_URL", "https://skillscreenstorage.blob.core.windows.net")
#     AZURE_BLOB_CONTAINER = os.environ.get("AZURE_BLOB_CONTAINER", "video_recordings")
#     AZURE_BLOB_SAS_TOKEN = os.environ.get("AZURE_BLOB_SAS_TOKEN", "?sp=racwdl&st=2025-11-04T14:56:17Z&se=2025-12-31T23:11:17Z&spr=https&sv=2024-11-04&sr=c&sig=7nu5Z5vcJrIuL0ivanRi3BHfHv%2FAPtHycpnhvubw0is%3D")
#     WTF_CSRF_ENABLED = os.getenv("ENABLE_CSRF", "false").lower() == "true"



import os
from datetime import timedelta

class Config:
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("SERVER_PORT", 5004))
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "temp/uploads")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_BYTES", 500 * 1024 * 1024))
    CORS_SUPPORTS_CREDENTIALS = True
    SEND_FILE_MAX_AGE_DEFAULT = timedelta(days=7)

    USE_AZURE_STORAGE = True

    # =========================
    # STORAGE ACCOUNT BASE URL
    # =========================
    AZURE_BLOB_ACCOUNT_URL = "https://skillscreenstorage00.blob.core.windows.net"

    # ====================================================
    # AUDIO — audio-recordings container
    # ====================================================
    AUDIO_CONTAINER = "audio-recordings"
    AUDIO_SAS_TOKEN = (
        "sp=racwdl"
        "&st=2025-11-27T04:00:22Z"
        "&se=2026-01-01T12:15:22Z"
        "&spr=https"
        "&sv=2024-11-04"
        "&sr=c"
        "&sig=jS4APM2jwknuHiNcqHPxUNJGn%2Fr4rUwFysebxixvxpw%3D"
    )

    AUDIO_CONTAINER_URL = (
        f"{AZURE_BLOB_ACCOUNT_URL}/{AUDIO_CONTAINER}?{AUDIO_SAS_TOKEN}"
    )

    # ====================================================
    # RESUMES — resumes container
    # ====================================================
    RESUME_CONTAINER = "resumes"
    RESUME_SAS_TOKEN = (
        "sp=racwdl"
        "&st=2025-11-27T04:10:47Z"
        "&se=2026-01-01T12:25:47Z"
        "&spr=https"
        "&sv=2024-11-04"
        "&sr=c"
        "&sig=13f8k4JW31E4kbzg52s%2BWhAuZE32AAhvjpo1eLjG%2BdA%3D"
    )

    RESUME_CONTAINER_URL = (
        f"{AZURE_BLOB_ACCOUNT_URL}/{RESUME_CONTAINER}?{RESUME_SAS_TOKEN}"
    )

    # ====================================================
    # VIDEO — video-recordings container
    # ====================================================
    VIDEO_CONTAINER = "video-recordings"
    VIDEO_SAS_TOKEN = (
        "sp=racwdl"
        "&st=2025-11-27T04:11:53Z"
        "&se=2026-01-01T12:26:53Z"
        "&spr=https"
        "&sv=2024-11-04"
        "&sr=c"
        "&sig=RpzJxwoEthSD5RfAiqdUbymIh7No7EUHOP2BewgKYbU%3D"
    )

    VIDEO_CONTAINER_URL = (
        f"{AZURE_BLOB_ACCOUNT_URL}/{VIDEO_CONTAINER}?{VIDEO_SAS_TOKEN}"
    )

    # 🔥 The upload service expects this value
    AZURE_BLOB_CONTAINER_URL = AUDIO_CONTAINER_URL  # default audio container

