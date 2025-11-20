"""
Video AI Service Client

Handles communication with video-ai-service for:
- Video analysis
- Cheating detection
- Attention tracking
- Behavior analysis
"""

import httpx
import logging
from typing import Dict, Any, Optional
from config import settings

logger = logging.getLogger(__name__)


class VideoServiceClient:
    """Client for video-ai-service API"""
    
    def __init__(self):
        self.base_url = settings.VIDEO_AI_SERVICE_URL
        self.timeout = settings.PROCESSING_TIMEOUT
        
    async def analyze_video(
        self,
        user_id: str,
        video_url: str
    ) -> Dict[str, Any]:
        """
        Trigger video analysis
        
        Analyzes video for:
        - Face detection
        - Attention tracking
        - Multiple person detection
        - Prohibited objects
        - Cheating indicators
        """
        try:
            logger.info(f"Triggering video analysis for user {user_id}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/analyze-url",
                    json={
                        "user_id": user_id,
                        "video_url": video_url
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"✅ Video analysis completed")
                
                return result
                
        except httpx.HTTPError as e:
            logger.error(f"❌ HTTP error analyzing video: {str(e)}")
            raise Exception(f"Failed to analyze video: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error analyzing video: {str(e)}")
            raise
    
    async def get_video_report(
        self,
        user_id: str,
        timestamp: str
    ) -> Dict[str, Any]:
        """
        Get video analysis report
        
        Returns:
        - Cheating detection results
        - Attention metrics
        - Behavior analysis
        - Flagged events
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/processed/{user_id}/{timestamp}/report"
                )
                
                response.raise_for_status()
                result = response.json()
                
                return result
                
        except httpx.HTTPError as e:
            logger.error(f"❌ HTTP error getting video report: {str(e)}")
            raise Exception(f"Failed to get video report: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error getting video report: {str(e)}")
            raise
    
    async def list_video_sessions(self, user_id: str) -> Dict[str, Any]:
        """
        List all video analysis sessions for user
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/processed/{user_id}/sessions"
                )
                
                response.raise_for_status()
                result = response.json()
                
                return result
                
        except httpx.HTTPError as e:
            logger.error(f"❌ HTTP error listing video sessions: {str(e)}")
            raise Exception(f"Failed to list video sessions: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error listing video sessions: {str(e)}")
            raise

