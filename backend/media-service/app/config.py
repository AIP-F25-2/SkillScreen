import os
from datetime import timedelta

class Config:
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("SERVER_PORT", 8004))
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "temp/uploads")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_BYTES", 500 * 1024 * 1024))
    CORS_SUPPORTS_CREDENTIALS = True
    SEND_FILE_MAX_AGE_DEFAULT = timedelta(days=7)

    # Storage configuration
    USE_AZURE_STORAGE = os.getenv("USE_AZURE_STORAGE", "true").lower() in ("true", "1", "yes")
    AZURE_BLOB_CONTAINER_URL = os.environ.get("AZURE_BLOB_CONTAINER_URL", "https://skillscreenstorage.blob.core.windows.net/video-recordings?sp=racwdl&st=2025-11-04T14:56:17Z&se=2025-12-31T23:11:17Z&spr=https&sv=2024-11-04&sr=c&sig=7nu5Z5vcJrIuL0ivanRi3BHfHv%2FAPtHycpnhvubw0is%3D")
    AZURE_BLOB_ACCOUNT_URL = os.environ.get("AZURE_BLOB_ACCOUNT_URL", "https://skillscreenstorage.blob.core.windows.net")
    AZURE_BLOB_CONTAINER = os.environ.get("AZURE_BLOB_CONTAINER", "video_recordings")
    AZURE_BLOB_SAS_TOKEN = os.environ.get("AZURE_BLOB_SAS_TOKEN", "?sp=racwdl&st=2025-11-04T14:56:17Z&se=2025-12-31T23:11:17Z&spr=https&sv=2024-11-04&sr=c&sig=7nu5Z5vcJrIuL0ivanRi3BHfHv%2FAPtHycpnhvubw0is%3D")
    WTF_CSRF_ENABLED = os.getenv("ENABLE_CSRF", "false").lower() == "true"
