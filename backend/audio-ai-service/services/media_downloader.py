from config import logger, settings
import os
import shutil
import time
import re
from urllib.parse import urlparse, parse_qs, urlencode
from azure.storage.blob import BlobServiceClient, BlobClient
from azure.core.exceptions import AzureError
from utils.media_utils import download_media, validate_media_url, detect_media_type, sanitize_url
from utils.file_utils import create_temp_file, cleanup_temp_file
from typing import Tuple, Optional, Dict
from uuid import UUID


class MediaDownloader:
    """Handles media (audio/video) download from multiple sources with database integration"""
    
    def __init__(self, max_retries: int = 3, retry_delay: int = 2):
        """
        Initialize MediaDownloader
        
        Args:
            max_retries: Maximum number of download retry attempts
            retry_delay: Initial delay between retries in seconds (exponential backoff)
        """
        self.downloaded_files = []
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Azure Blob Storage configuration
        self.azure_account_name = settings.AZURE_STORAGE_ACCOUNT_NAME
        self.azure_container_name = settings.AZURE_STORAGE_CONTAINER_NAME
        self.azure_sas_token = settings.AZURE_STORAGE_SAS_TOKEN
    
    def _is_azure_blob_url(self, url: str) -> bool:
        """Check if URL is an Azure Blob Storage URL"""
        return 'blob.core.windows.net' in url.lower()
    
    def _download_from_azure_blob(
        self, 
        url: str, 
        destination_path: str,
        log_prefix: str
    ) -> bool:
        """
        Download file from Azure Blob Storage
        
        Args:
            url: Complete Azure Blob Storage URL with SAS token
            destination_path: Local file path to save to
            log_prefix: Logging prefix
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"{log_prefix} Downloading from complete Azure Blob URL")
            
            # Use the complete URL directly with BlobClient
            # No need to parse and reconstruct - the URL is already complete
            blob_client = BlobClient.from_blob_url(url)
            
            with open(destination_path, "wb") as download_file:
                download_stream = blob_client.download_blob()
                download_file.write(download_stream.readall())
            
            logger.info(f"{log_prefix} Successfully downloaded from Azure Blob")
            return True
            
        except AzureError as e:
            logger.error(f"{log_prefix} Azure Blob download error: {e}")
            return False
        except Exception as e:
            logger.error(f"{log_prefix} Unexpected error downloading from Azure: {e}")
            return False
    
    def _convert_google_drive_url(self, url: str) -> str:
        """
        Convert Google Drive sharing URL to direct download URL
        
        Supports formats:
        - https://drive.google.com/file/d/FILE_ID/view
        - https://drive.google.com/uc?id=FILE_ID&export=download (already direct)
        - https://drive.google.com/open?id=FILE_ID
        
        Returns:
            Direct download URL
        """
        try:
            # Already a direct download link
            if 'export=download' in url or '/uc?' in url:
                return url
            
            # Extract file ID from various Google Drive URL formats
            file_id = None
            
            # Format: /file/d/FILE_ID/view
            match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
            if match:
                file_id = match.group(1)
            
            # Format: ?id=FILE_ID
            if not file_id:
                parsed = urlparse(url)
                query_params = parse_qs(parsed.query)
                file_id = query_params.get('id', [None])[0]
            
            if file_id:
                direct_url = f"https://drive.google.com/uc?id={file_id}&export=download"
                logger.info(f"Converted Google Drive URL: {file_id}")
                return direct_url
            
            logger.warning(f"Could not extract Google Drive file ID from: {url}")
            return url
            
        except Exception as e:
            logger.warning(f"Error converting Google Drive URL: {e}")
            return url
    
    def _is_google_drive_url(self, url: str) -> bool:
        """Check if URL is a Google Drive link"""
        return 'drive.google.com' in url.lower()
    
    def download(
        self, 
        media_url: str, 
        media_file_id: Optional[UUID] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Download media from URL with retry logic
        Supports: HTTP/HTTPS, Google Drive, Azure Blob Storage, local files
        
        Args:
            media_url: URL of media to download (can be complete Azure Blob URL with SAS)
            media_file_id: Optional UUID for database tracking
        
        Returns:
            (filepath, media_type, error_message)
            media_type: 'audio', 'video', or 'unknown'
        """
        log_prefix = f"[MediaFile:{media_file_id}]" if media_file_id else "[Download]"
        
        try:
            # Sanitize URL
            media_url = sanitize_url(media_url)
            logger.info(f"{log_prefix} Processing URL: {media_url[:100]}...")
            
            # Detect source type
            is_azure = self._is_azure_blob_url(media_url)
            is_google_drive = self._is_google_drive_url(media_url)
            
            # Convert Google Drive URLs to direct download
            if is_google_drive:
                logger.info(f"{log_prefix} Detected Google Drive URL")
                media_url = self._convert_google_drive_url(media_url)
            elif is_azure:
                logger.info(f"{log_prefix} Detected Azure Blob Storage URL")
            
            # Support local files (absolute/relative paths or file:// URLs)
            local_path = None
            if media_url.startswith('file://'):
                local_path = media_url[len('file://'):]
            elif os.path.exists(media_url):
                local_path = media_url
            
            # Detect media type
            media_type = detect_media_type(media_url)
            logger.info(f"{log_prefix} Detected media type: {media_type}")
            
            # Validate URL (non-blocking for servers that block HEAD requests)
            if not is_azure and not local_path:
                logger.info(f"{log_prefix} Validating media URL")
                if not validate_media_url(media_url):
                    logger.warning(f"{log_prefix} URL validation failed, attempting direct download anyway")
            
            # Determine file extension
            suffix = self._determine_file_extension(media_url, media_type)
            logger.info(f"{log_prefix} Using file extension: {suffix}")
            
            # Handle local file copy
            if local_path and os.path.exists(local_path):
                return self._copy_local_file(local_path, suffix, log_prefix)
            
            # Download with retry logic (handles Azure, Google Drive, and direct URLs)
            return self._download_with_retry(
                media_url, 
                suffix, 
                media_type, 
                log_prefix,
                is_azure=is_azure
            )
            
        except Exception as e:
            error_msg = f"{log_prefix} Media download error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return None, None, error_msg
    
    def _find_extension_in_url(self, url_lower: str, extensions: list) -> Optional[str]:
        """
        Find matching extension in URL

        Args:
            url_lower: Lowercase URL
            extensions: List of extensions to check

        Returns:
            Matching extension or None
        """
        for ext in extensions:
            if url_lower.endswith(ext) or ext in url_lower:
                return ext
        return None

    def _get_extension_for_media_type(self, url_lower: str, media_type: str) -> str:
        """
        Get file extension based on media type and URL

        Args:
            url_lower: Lowercase URL
            media_type: 'audio', 'video', or 'unknown'

        Returns:
            File extension with dot
        """
        audio_exts = ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac', '.wma']
        video_exts = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv']

        if media_type == 'audio':
            return self._find_extension_in_url(url_lower, audio_exts) or '.mp3'

        if media_type == 'video':
            return self._find_extension_in_url(url_lower, video_exts) or '.mp4'

        # Unknown type: try audio first, then video
        return (self._find_extension_in_url(url_lower, audio_exts) or
                self._find_extension_in_url(url_lower, video_exts) or
                '.mp3')

    def _determine_file_extension(self, url: str, media_type: str) -> str:
        """
        Determine appropriate file extension based on URL and media type

        Args:
            url: Media URL
            media_type: Detected media type ('audio', 'video', or 'unknown')

        Returns:
            File extension with dot (e.g., '.mp4', '.mp3')
        """
        url_lower = url.lower()
        return self._get_extension_for_media_type(url_lower, media_type)
    
    def _copy_local_file(
        self, 
        local_path: str, 
        suffix: str, 
        log_prefix: str
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Copy local file to temp directory
        
        Args:
            local_path: Path to local file
            suffix: File extension
            log_prefix: Logging prefix
        
        Returns:
            (filepath, media_type, error_message)
        """
        try:
            media_path = create_temp_file(suffix=suffix)
            shutil.copyfile(local_path, media_path)
            logger.info(f"{log_prefix} Copied local media to: {media_path}")
            
            self.downloaded_files.append(media_path)
            media_type = 'audio' if suffix in ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac'] else 'video'
            
            return media_path, media_type, None
            
        except Exception as e:
            error_msg = f"{log_prefix} Failed to copy local file: {str(e)}"
            logger.error(error_msg)
            return None, None, error_msg
    
    def _perform_download(
        self,
        media_url: str,
        media_path: str,
        is_azure: bool,
        log_prefix: str
    ) -> bool:
        """
        Perform the actual download operation

        Args:
            media_url: URL to download from (complete URL for Azure)
            media_path: Destination file path
            is_azure: Whether this is an Azure Blob Storage download
            log_prefix: Logging prefix

        Returns:
            True if download succeeded, False otherwise
        """
        if is_azure:
            return self._download_from_azure_blob(media_url, media_path, log_prefix)
        return download_media(media_url, media_path)

    def _validate_downloaded_file(self, media_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that downloaded file exists and has content

        Args:
            media_path: Path to downloaded file

        Returns:
            (is_valid, error_message)
        """
        if not os.path.exists(media_path) or os.path.getsize(media_path) == 0:
            return False, "Downloaded file is empty or missing"
        return True, None

    def _handle_successful_download(
        self,
        media_path: str,
        media_type: str,
        log_prefix: str
    ) -> Tuple[str, str, None]:
        """
        Handle successful download

        Args:
            media_path: Path to downloaded file
            media_type: Detected media type
            log_prefix: Logging prefix

        Returns:
            (filepath, media_type, None)
        """
        file_size = os.path.getsize(media_path)
        self.downloaded_files.append(media_path)
        size_mb = round(file_size / (1024 * 1024), 2)
        logger.info(f"{log_prefix} Media downloaded successfully: {media_path} ({file_size} bytes / {size_mb} MB)")
        return media_path, media_type, None

    def _cleanup_failed_download(self, media_path: Optional[str]):
        """Clean up file from failed download attempt"""
        if media_path and os.path.exists(media_path):
            cleanup_temp_file(media_path)

    def _wait_before_retry(self, attempt: int, log_prefix: str):
        """Wait before retrying with exponential backoff"""
        delay = self.retry_delay * (2 ** (attempt - 1))
        logger.info(f"{log_prefix} Retrying in {delay} seconds...")
        time.sleep(delay)

    def _attempt_download(
        self,
        attempt: int,
        media_url: str,
        suffix: str,
        media_type: str,
        log_prefix: str,
        is_azure: bool
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Attempt a single download with error handling

        Args:
            attempt: Current attempt number
            media_url: URL to download from (complete URL for Azure)
            suffix: File extension
            media_type: Detected media type
            log_prefix: Logging prefix
            is_azure: Whether this is an Azure Blob Storage download

        Returns:
            (filepath, media_type, error_message, last_error)
        """
        media_path = None
        try:
            media_path = create_temp_file(suffix=suffix)
            logger.info(f"{log_prefix} Attempt {attempt}/{self.max_retries} - Downloading to: {media_path}")

            success = self._perform_download(media_url, media_path, is_azure, log_prefix)

            if not success:
                self._cleanup_failed_download(media_path)
                return None, None, None, "Download function returned False"

            is_valid, error = self._validate_downloaded_file(media_path)
            if not is_valid:
                self._cleanup_failed_download(media_path)
                return None, None, None, error

            return self._handle_successful_download(media_path, media_type, log_prefix) + (None,)

        except Exception as e:
            self._cleanup_failed_download(media_path)
            error_msg = str(e)
            logger.error(f"{log_prefix} Attempt {attempt} failed: {error_msg}")
            return None, None, None, error_msg

    def _download_with_retry(
        self,
        media_url: str,
        suffix: str,
        media_type: str,
        log_prefix: str,
        is_azure: bool = False
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Download media with exponential backoff retry logic

        Args:
            media_url: URL to download from (complete URL for Azure)
            suffix: File extension
            media_type: Detected media type
            log_prefix: Logging prefix
            is_azure: Whether this is an Azure Blob Storage download

        Returns:
            (filepath, media_type, error_message)
        """
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            filepath, ftype, _, last_error = self._attempt_download(
                attempt, media_url, suffix, media_type, log_prefix, is_azure
            )

            if filepath:
                return filepath, ftype, None

            if attempt < self.max_retries:
                self._wait_before_retry(attempt, log_prefix)

        # All retries exhausted
        error_msg = f"{log_prefix} Failed to download after {self.max_retries} attempts. Last error: {last_error}"
        logger.error(error_msg)
        return None, None, error_msg
    
    def get_download_info(self, filepath: str) -> Dict[str, any]:
        """
        Get information about a downloaded file
        
        Args:
            filepath: Path to downloaded file
        
        Returns:
            Dictionary with file info (size, exists, path)
        """
        return {
            'filepath': filepath,
            'exists': os.path.exists(filepath),
            'size_bytes': os.path.getsize(filepath) if os.path.exists(filepath) else 0,
            'size_mb': round(os.path.getsize(filepath) / (1024 * 1024), 2) if os.path.exists(filepath) else 0
        }
    
    def cleanup_file(self, filepath: str):
        """
        Clean up a specific downloaded file
        
        Args:
            filepath: Path to file to clean up
        """
        cleanup_temp_file(filepath)
        if filepath in self.downloaded_files:
            self.downloaded_files.remove(filepath)
            logger.info(f"Cleaned up file: {filepath}")
    
    def cleanup(self):
        """Clean up all downloaded files"""
        count = len(self.downloaded_files)
        for filepath in self.downloaded_files:
            cleanup_temp_file(filepath)
        self.downloaded_files.clear()
        logger.info(f"Cleaned up {count} downloaded file(s)")