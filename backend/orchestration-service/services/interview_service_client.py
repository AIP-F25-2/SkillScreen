import httpx
from fastapi import UploadFile
from config.settings import settings
from config.logger import logger
from typing import List, Dict

class InterviewServiceClient:
    def __init__(self):
        self.base_url = settings.INTERVIEW_SERVICE_URL
        self.timeout = settings.INTERVIEW_SERVICE_TIMEOUT
    
    async def upload_resumes(self, files: List[UploadFile], organization_id: str) -> Dict:
        """Upload resumes - Interview service auto-schedules interviews"""
        url = f"{self.base_url}/resumes/upload"
        
        files_data = []
        for file in files:
            content = await file.read()
            files_data.append(('files', (file.filename, content, file.content_type)))
            await file.seek(0)
        
        form_data = {'organization_id': organization_id}
        
        try:
            logger.info(f"📤 Uploading {len(files)} resumes to interview service")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, files=files_data, data=form_data)
                response.raise_for_status()
                result = response.json()
                logger.info(f"✅ Resumes uploaded, interviews auto-scheduled")
                return result
        except Exception as e:
            logger.error(f"❌ Resume upload failed: {str(e)}")
            raise
    
    async def validate_token(self, token: str) -> Dict:
        """Validate interview token"""
        url = f"{self.base_url}/api/token/validate"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json={"token": token})
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"❌ Token validation failed: {str(e)}")
            raise