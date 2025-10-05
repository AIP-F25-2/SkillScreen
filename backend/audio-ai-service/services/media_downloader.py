from config import logger
from utils.media_utils import download_media, validate_media_url, detect_media_type
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
            # Detect media type
            media_type = detect_media_type(media_url)
            logger.info(f"Detected media type: {media_type}")
            
            # Validate URL
            logger.info(f"Validating media URL: {media_url}")
            if not validate_media_url(media_url):
                return None, None, "Invalid or inaccessible media URL"
            
            # Determine file extension
            if media_type == 'audio':
                # Try to get actual extension from URL
                for ext in ['.mp3', '.wav', '.m4a', '.aac']:
                    if media_url.lower().endswith(ext):
                        suffix = ext
                        break
                else:
                    suffix = '.mp3'  # default
            else:
                suffix = '.mp4'  # video or unknown
            
            # Create temp file
            media_path = create_temp_file(suffix=suffix)
            logger.info(f"Downloading to: {media_path}")
            
            # Download
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