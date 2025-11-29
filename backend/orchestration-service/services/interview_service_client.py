import httpx
from fastapi import UploadFile
from config.settings import settings
from config.logger import logger
from typing import List, Dict, Optional

class InterviewServiceClient:
    def __init__(self):
        self.base_url = settings.INTERVIEW_SERVICE_URL
        self.timeout = settings.INTERVIEW_SERVICE_TIMEOUT
    
    async def upload_resumes(
        self, 
        files: List[UploadFile], 
        organization_id: str, 
        job_position_id: str,
        interview_settings: Optional[Dict] = None
    ) -> Dict:
        """Upload resumes - Interview service auto-schedules interviews"""
        url = f"{self.base_url}/resumes/upload"
        
        files_data = []
        for file in files:
            content = await file.read()
            files_data.append(('files', (file.filename, content, file.content_type)))
            await file.seek(0)
        
        form_data = {
            'organization_id': organization_id,
            'job_position_id': job_position_id
        }
        
        # Add optional interview settings if provided
        if interview_settings:
            if 'mode' in interview_settings:
                form_data['mode'] = interview_settings['mode']
            if 'difficulty' in interview_settings:
                form_data['difficulty'] = interview_settings['difficulty']
            if 'max_questions' in interview_settings:
                form_data['max_questions'] = str(interview_settings['max_questions'])
            if 'interview_type' in interview_settings:
                form_data['interview_type'] = interview_settings['interview_type']
            if 'target_duration_minutes' in interview_settings:
                form_data['target_duration_minutes'] = str(interview_settings['target_duration_minutes'])
        
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
    
    async def get_interview(self, interview_id: str) -> Dict:
        """Get interview by ID"""
        url = f"{self.base_url}/api/interviews/{interview_id}"
        
        try:
            logger.info(f"📋 Getting interview {interview_id}")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                result = response.json()
                logger.info(f"✅ Interview retrieved")
                return result
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Interview {interview_id} not found")
            raise
        except Exception as e:
            logger.error(f"❌ Get interview failed: {str(e)}")
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