import httpx
from config.settings import settings
from config.logger import logger
from typing import Dict

class AssessmentServiceClient:
    def __init__(self):
        self.base_url = settings.ASSESSMENT_SERVICE_URL
        self.timeout = settings.ASSESSMENT_SERVICE_TIMEOUT
    
    async def get_assessment(self, interview_id: str) -> Dict:
        """Get assessment results"""
        url = f"{self.base_url}/v1/assessment/interview/{interview_id}"
        
        try:
            logger.info(f"📊 Getting assessment for {interview_id}")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"❌ Get assessment failed: {str(e)}")
            raise