import os
import tempfile
import uuid
from pathlib import Path
from config import settings, logger
from typing import Tuple


def create_temp_file(suffix: str = "") -> str:
    """
    Create a temporary file path
    
    Args:
        suffix: File extension (e.g., '.mp4', '.wav')
    
    Returns:
        Full path to temporary file
    """
    temp_dir = Path(settings.TEMP_AUDIO_DIR)
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{uuid.uuid4()}{suffix}"
    filepath = temp_dir / filename
    
    return str(filepath)


def cleanup_temp_file(filepath: str) -> bool:
    """
    Delete temporary file
    
    Args:
        filepath: Path to file to delete
    
    Returns:
        True if deleted, False if failed
    """
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Cleaned up temp file: {filepath}")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to cleanup {filepath}: {str(e)}")
        return False


def get_file_size_mb(filepath: str) -> float:
    """Get file size in MB"""
    if os.path.exists(filepath):
        return os.path.getsize(filepath) / (1024 * 1024)
    return 0.0


def validate_file_size(filepath: str) -> Tuple[bool, str]:
    """
    Validate file size is within limits
    
    Returns:
        (is_valid, error_message)
    """
    size_mb = get_file_size_mb(filepath)
    
    if size_mb > settings.MAX_FILE_SIZE_MB:
        return False, f"File size {size_mb:.2f}MB exceeds limit of {settings.MAX_FILE_SIZE_MB}MB"
    
    return True, ""