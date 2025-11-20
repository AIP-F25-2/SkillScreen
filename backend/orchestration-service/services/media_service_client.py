"""
Media Service Client

Handles communication with media-service for:
- Video/audio upload
- File storage
- Chunk management
- File retrieval
"""

import httpx
import logging
from typing import Dict, Any, Optional
from config import settings

logger = logging.getLogger(__name__)


class MediaServiceClient:
    """Client for media-service API"""
    
    def __init__(self):
        self.base_url = settings.MEDIA_SERVICE_URL
        self.timeout = settings.SERVICE_TIMEOUT
        
    async def get_media_file(self, media_file_id: str) -> Dict[str, Any]:
        """
        Get media file details
        
        Returns:
        - File metadata
        - Storage URI
        - File status
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/media/files/{media_file_id}"
                )
                
                response.raise_for_status()
                result = response.json()
                
                return result
                
        except httpx.HTTPError as e:
            logger.error(f"❌ HTTP error getting media file: {str(e)}")
            raise Exception(f"Failed to get media file: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error getting media file: {str(e)}")
            raise
    
    async def get_upload_status(
        self,
        interview_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Get upload/recording status
        
        Returns:
        - Upload completion status
        - Chunks received
        - File availability
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/media/recording-status",
                    params={
                        "interview_id": interview_id,
                        "session_id": session_id
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                return result
                
        except httpx.HTTPError as e:
            logger.error(f"❌ HTTP error getting upload status: {str(e)}")
            raise Exception(f"Failed to get upload status: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error getting upload status: {str(e)}")
            raise

