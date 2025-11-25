import httpx
from config.settings import settings
from config.logger import logger

class AIServicesClient:
    def __init__(self):
        self.audio_url = settings.AUDIO_AI_SERVICE_URL
        self.video_url = settings.VIDEO_AI_SERVICE_URL
        self.timeout = settings.AI_SERVICE_TIMEOUT
    
    async def trigger_audio_analysis(
        self,
        interview_id: str,
        session_id: str,
        media_file_id: str
    ) -> bool:
        """Fire-and-forget audio AI analysis"""
        url = f"{self.audio_url}/api/audio/process-interview-audio"
        
        payload = {
            "interview_id": interview_id,
            "session_id": session_id,
            "media_file_id": media_file_id
        }
        
        try:
            logger.info("🔥 Triggering audio AI analysis")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                return response.status_code == 202
        except Exception as e:
            logger.error(f"❌ Audio AI trigger failed: {str(e)}")
            return False
    
    async def trigger_video_analysis(
        self,
        interview_id: str,
        session_id: str,
        media_file_id: str
    ) -> bool:
        """Fire-and-forget video AI analysis"""
        url = f"{self.video_url}/analyze-url"
        
        payload = {
            "user_id": interview_id,
            "video_url": f"videos/{interview_id}/{media_file_id}"
        }
        
        try:
            logger.info("🔥 Triggering video AI analysis")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                return response.status_code in [200, 202]
        except Exception as e:
            logger.error(f"❌ Video AI trigger failed: {str(e)}")
            return False