"""
app/constants.py
Centralized constants used across the media-service app.
"""

# --------------------------------------------------------------------
# 🧱 General Application Constants
# --------------------------------------------------------------------
APP_NAME = "Media Service"
DEFAULT_PAGE_SIZE = 20
MAX_UPLOAD_SIZE_MB = 500


# --------------------------------------------------------------------
# ⚠️ Error Messages
# --------------------------------------------------------------------
ERROR_INTERVIEW_NOT_FOUND = "Interview not found"
ERROR_MISSING_FILE = "Missing file"
ERROR_INVALID_FILE_TYPE = "Invalid or unsupported file type"
ERROR_UPLOAD_FAILED = "File upload failed"
ERROR_MISSING_STATUS = "Missing status field"
ERROR_INTERNAL = "An unexpected error occurred"
ERROR_MISSING_INTERVIEW_ID = "Missing interview_id"

# --------------------------------------------------------------------
# ✅ Success Messages
# --------------------------------------------------------------------
SUCCESS_FILE_UPLOADED = "File uploaded successfully"
SUCCESS_INTERVIEW_UPDATED = "Interview updated successfully"
SUCCESS_TRANSCRIPT_UPDATED = "Transcript updated successfully"


# --------------------------------------------------------------------
# 📦 Database / Media Constants
# --------------------------------------------------------------------
MEDIA_TYPE_FILE = "file"
MEDIA_TYPE_INTERVIEW = "interview"
MEDIA_TYPE_VIDEO = "video"
VIDEO_WEBM_FORMAT = "video/webm"
MERGED_WEBM_NAMING = "merged.webm"
# --------------------------------------------------------------------
# 🌍 Miscellaneous
# --------------------------------------------------------------------
TIMEZONE_UTC = "UTC"
