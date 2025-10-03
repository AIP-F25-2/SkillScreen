import requests
from config import logger
from typing import Optional
import os


def download_video(url: str, output_path: str, timeout: int = 300) -> bool:
    """
    Download video from URL
    
    Args:
        url: Video URL
        output_path: Where to save video
        timeout: Request timeout in seconds
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Downloading video from: {url}")
        
        # Stream download for large files
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        
        # Write to file in chunks
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        file_size = os.path.getsize(output_path) / (1024 * 1024)
        logger.info(f"Video downloaded successfully: {file_size:.2f}MB")
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


def validate_video_url(url: str) -> bool:
    """
    Quick validation of video URL
    
    Args:
        url: Video URL to validate
    
    Returns:
        True if valid, False otherwise
    """
    try:
        # HEAD request to check if URL is accessible
        response = requests.head(url, timeout=10, allow_redirects=True)
        return response.status_code == 200
    except:
        return False