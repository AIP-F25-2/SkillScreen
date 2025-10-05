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
        
        response = requests.get(url, stream=True, timeout=timeout)
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
        response = requests.head(url, timeout=10, allow_redirects=True)
        return response.status_code == 200
    except:
        return False