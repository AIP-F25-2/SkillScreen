from config import logger
from utils.video_utils import download_video, validate_video_url
from utils.file_utils import create_temp_file, cleanup_temp_file
from typing import Tuple, Optional


class VideoDownloader:
    """Handles video download from URLs"""
    
    def __init__(self):
        self.downloaded_files = []
    
    def download(self, video_url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Download video from URL
        
        Args:
            video_url: URL of video to download
        
        Returns:
            (filepath, error_message) - filepath is None if error
        """
        try:
            # Validate URL first
            logger.info(f"Validating video URL: {video_url}")
            if not validate_video_url(video_url):
                return None, "Invalid or inaccessible video URL"
            
            # Create temp file for video
            video_path = create_temp_file(suffix=".mp4")
            logger.info(f"Downloading to: {video_path}")
            
            # Download
            success = download_video(video_url, video_path)
            
            if not success:
                cleanup_temp_file(video_path)
                return None, "Failed to download video"
            
            self.downloaded_files.append(video_path)
            logger.info(f"Video downloaded successfully: {video_path}")
            return video_path, None
            
        except Exception as e:
            error_msg = f"Video download error: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
    
    def cleanup(self):
        """Clean up all downloaded files"""
        for filepath in self.downloaded_files:
            cleanup_temp_file(filepath)
        self.downloaded_files.clear()