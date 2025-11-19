import os
from datetime import timedelta

class Config:
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("SERVER_PORT", 5004))
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "temp/uploads")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_BYTES", 500 * 1024 * 1024))
    CORS_SUPPORTS_CREDENTIALS = True
    SEND_FILE_MAX_AGE_DEFAULT = timedelta(days=7)

    # Storage configuration
    USE_AZURE_STORAGE = os.getenv("USE_AZURE_STORAGE", "true").lower() == "true"
    AZURE_BLOB_CONTAINER_URL = os.environ.get("AZURE_BLOB_CONTAINER_URL", "https://skillscreenstorage.blob.core.windows.net/video-recordings?sp=racwdl&st=2025-11-18T22:02:53Z&se=2026-01-01T06:17:53Z&spr=https&sv=2024-11-04&sr=c&sig=7nA14qtnnJ6wGV9Mu5RQJDPBfLANTdFu2rcgD1QikBI%3D")
    AZURE_BLOB_ACCOUNT_URL = os.environ.get("AZURE_BLOB_ACCOUNT_URL", "https://skillscreenstorage.blob.core.windows.net")
    AZURE_BLOB_CONTAINER = os.environ.get("AZURE_BLOB_CONTAINER", "video-recordings")
    AZURE_BLOB_SAS_TOKEN = os.environ.get("AZURE_BLOB_SAS_TOKEN", "?sp=racwdl&st=2025-11-18T22:02:53Z&se=2026-01-01T06:17:53Z&spr=https&sv=2024-11-04&sr=c&sig=7nA14qtnnJ6wGV9Mu5RQJDPBfLANTdFu2rcgD1QikBI%3D")
    WTF_CSRF_ENABLED = os.getenv("ENABLE_CSRF", "false").lower() == "true"
