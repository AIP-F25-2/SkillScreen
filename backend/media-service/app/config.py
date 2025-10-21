import os
from datetime import timedelta

class Config:
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("SERVER_PORT", 5004))
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_BYTES", 500 * 1024 * 1024))
    CORS_SUPPORTS_CREDENTIALS = True
    SEND_FILE_MAX_AGE_DEFAULT = timedelta(days=7)
