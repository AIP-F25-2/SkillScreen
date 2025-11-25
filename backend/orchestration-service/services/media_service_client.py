import httpx
from config.settings import settings
from config.logger import logger
from typing import Dict

class MediaServiceClient:
    def __init__(self):
        self.base_url = settings.MEDIA_SERVICE_URL
        self.timeout = settings.MEDIA_SERVICE_TIMEOUT
    
    async def finalize_upload(self, interview_id: str, session_id: str) -> Dict:
        """Finalize video upload - merge chunks, get media_file_id"""
        url = f"{self.base_url}/finalize_upload"
        
        payload = {
            "interview_id": interview_id,
            "session_id": session_id
        }
        
        try:
            logger.info("📹 Finalizing video upload via media-service")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
                data = response.json()
                logger.info(f"✅ Video finalized: {data.get('status')}")
                return data
        except Exception as e:
            logger.error(f"❌ Finalize upload failed: {str(e)}")
            raise