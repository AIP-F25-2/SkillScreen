import requests
from config import logger
from typing import Optional, Tuple
import os


def is_audio_file(url: str) -> bool:
    """Check if URL points to audio file based on extension"""
    audio_extensions = ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac', '.wma']
    url_lower = url.lower()
    return any(url_lower.endswith(ext) for ext in audio_extensions)


def is_video_file(url: str) -> bool:
    """Check if URL points to video file based on extension"""
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv']
    url_lower = url.lower()
    return any(url_lower.endswith(ext) for ext in video_extensions)


def detect_media_type(url: str) -> str:
    """
    Detect media type from URL
    
    Returns: 'audio', 'video', or 'unknown'
    """
    if is_audio_file(url):
        return 'audio'
    elif is_video_file(url):
        return 'video'
    else:
        return 'unknown'


def sanitize_url(url: str) -> str:
    """
    Remove surrounding whitespace and common hidden characters that often sneak in
    from copy/paste (zero-width spaces, BOM, smart quotes).
    """
    if not isinstance(url, str):
        return url
    cleaned = url.strip()
    # Remove zero-width and BOM-like characters
    hidden_chars = [
        "\u200b",  # zero width space
        "\u200c",  # zero width non-joiner
        "\u200d",  # zero width joiner
        "\ufeff",  # BOM
        "\u2060",  # word joiner
    ]
    for ch in hidden_chars:
        cleaned = cleaned.replace(ch, "")
    # Replace smart quotes with normal quotes and strip quotes
    cleaned = cleaned.replace("“", '"').replace("”", '"').replace("’", "'")
    if cleaned.startswith(('"', "'")) and cleaned.endswith(('"', "'")):
        cleaned = cleaned[1:-1]
    return cleaned

def download_media(url: str, output_path: str, timeout: int = 300) -> bool:
    """
    Download media (audio or video) from URL
    
    Args:
        url: Media URL
        output_path: Where to save
        timeout: Request timeout in seconds
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Downloading media from: {url}")

        # Some servers reject requests without a User-Agent or Range header
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; SkillScreen-AudioAI/1.0)",
            "Accept": "*/*",
        }

        response = requests.get(sanitize_url(url), stream=True, timeout=timeout, allow_redirects=True, headers=headers)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        file_size = os.path.getsize(output_path) / (1024 * 1024)
        logger.info(f"Media downloaded successfully: {file_size:.2f}MB")
        return True
        
    except requests.exceptions.Timeout:
        logger.error(f"Download timeout after {timeout}s")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Download failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during download: {str(e)}")
        return False


def validate_media_url(url: str) -> bool:
    """
    Quick validation of media URL
    
    Args:
        url: Media URL to validate
    
    Returns:
        True if valid, False otherwise
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; SkillScreen-AudioAI/1.0)",
            "Accept": "*/*",
        }

        # First try HEAD (fast). Many servers either 200/3xx here.
        try:
            response = requests.head(sanitize_url(url), timeout=10, allow_redirects=True, headers=headers)
            if 200 <= response.status_code < 400:
                return True
        except requests.exceptions.RequestException:
            # Fall back to GET below
            pass

        # Fallback: try a lightweight GET with stream; read a tiny chunk
        with requests.get(sanitize_url(url), stream=True, timeout=10, allow_redirects=True, headers=headers) as r:
            if 200 <= r.status_code < 400:
                # Attempt to read a very small chunk to ensure accessibility
                try:
                    next(r.iter_content(chunk_size=1024), None)  # Try to read one chunk, ignore content
                except Exception:
                    return False
                return True
            return False
    except Exception as e:
        logger.warning(f"URL validation failed: {str(e)}")
        return False