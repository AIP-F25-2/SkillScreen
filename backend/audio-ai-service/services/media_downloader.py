from config import logger
import os
import shutil
from utils.media_utils import download_media, validate_media_url, detect_media_type, sanitize_url
from utils.file_utils import create_temp_file, cleanup_temp_file
from typing import Tuple, Optional


class MediaDownloader:
    """Handles media (audio/video) download from URLs"""
    
    def __init__(self):
        self.downloaded_files = []
    
    def download(self, media_url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Download media from URL
        
        Args:
            media_url: URL of media to download
        
        Returns:
            (filepath, media_type, error_message)
            media_type: 'audio', 'video', or 'unknown'
        """
        try:
            # Sanitize URL and detect media type
            media_url = sanitize_url(media_url)

            # Support local files (absolute/relative paths or file:// URLs)
            local_path = None
            if media_url.startswith('file://'):
                local_path = media_url[len('file://'):]
            elif os.path.exists(media_url):
                local_path = media_url
            media_type = detect_media_type(media_url)
            logger.info(f"Detected media type: {media_type}")
            
            # Validate URL (non-blocking). Some servers block HEAD; proceed but log.
            logger.info(f"Validating media URL: {media_url}")
            if not validate_media_url(media_url):
                logger.warning("URL validation failed, attempting direct download anyway")
            
            # Determine file extension more robustly
            url_lower = media_url.lower()
            audio_exts = ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac']
            video_exts = ['.mp4', '.avi', '.mov', '.mkv', '.webm']

            suffix = None
            if media_type == 'audio':
                for ext in audio_exts:
                    if url_lower.endswith(ext) or ext in url_lower:
                        suffix = ext
                        break
                if suffix is None:
                    suffix = '.mp3'  # safe audio default
            elif media_type == 'video':
                for ext in video_exts:
                    if url_lower.endswith(ext) or ext in url_lower:
                        suffix = ext
                        break
                if suffix is None:
                    suffix = '.mp4'
            else:
                # Unknown: try to infer from URL anywhere, prefer audio
                for ext in audio_exts:
                    if ext in url_lower:
                        suffix = ext
                        media_type = 'audio'
                        break
                if suffix is None:
                    for ext in video_exts:
                        if ext in url_lower:
                            suffix = ext
                            media_type = 'video'
                            break
                if suffix is None:
                    # As a last resort assume audio to avoid ffmpeg video parse on audio
                    suffix = '.mp3'
                    media_type = 'audio'
            
            # If local file, copy into temp directory so lifecycle is consistent
            if local_path and os.path.exists(local_path):
                media_path = create_temp_file(suffix=suffix)
                shutil.copyfile(local_path, media_path)
                logger.info(f"Copied local media to: {media_path}")
                success = True
            else:
                # Create temp file and download
                media_path = create_temp_file(suffix=suffix)
                logger.info(f"Downloading to: {media_path}")
                success = download_media(media_url, media_path)
            
            if not success:
                cleanup_temp_file(media_path)
                return None, None, "Failed to download media"
            
            self.downloaded_files.append(media_path)
            logger.info(f"Media downloaded successfully: {media_path}")
            return media_path, media_type, None
            
        except Exception as e:
            error_msg = f"Media download error: {str(e)}"
            logger.error(error_msg)
            return None, None, error_msg
    
    def cleanup(self):
        """Clean up all downloaded files"""
        for filepath in self.downloaded_files:
            cleanup_temp_file(filepath)
        self.downloaded_files.clear()