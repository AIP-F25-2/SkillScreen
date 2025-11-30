import httpx
from fastapi import UploadFile
from config.settings import settings
from config.logger import logger
from typing import List, Dict, Optional


class InterviewServiceClient:
    """Client to communicate with Interview Service"""

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
        """
        Upload resumes to Interview Service

        Interview Service will:
        1. Parse resume files
        2. Extract candidate information
        3. Create candidate records
        4. Get template_id from interview_templates table
        5. Create interview records (scheduled status)
        6. Send email invitations

        Args:
            files: List of UploadFile objects
            organization_id: Organization UUID
            job_position_id: Job Position UUID
            interview_settings: Optional settings (mode, difficulty, etc.)

        Returns:
            {
                "success": true,
                "data": {
                    "candidates_created": int,
                    "interviews_scheduled": int,
                    "candidates": [...],
                    "interviews": [...]
                }
            }
        """
        url = f"{self.base_url}/resumes/upload"

        # Prepare files for multipart upload
        files_data = []
        for file in files:
            content = await file.read()
            files_data.append(('files', (file.filename, content, file.content_type)))
            await file.seek(0)

        # Prepare form data
        form_data = {
            'organization_id': organization_id,
            'job_position_id': job_position_id
        }

        # Add optional interview settings
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
            logger.info(f"📤 Calling Interview Service: POST {url}")
            logger.info(f"   Files: {len(files)}")
            logger.info(f"   Organization: {organization_id}")
            logger.info(f"   Job Position: {job_position_id}")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, files=files_data, data=form_data)
                response.raise_for_status()
                result = response.json()

                logger.info(f"✅ Interview Service response received")
                logger.info(f"   Status: {response.status_code}")
                logger.info(f"   Success: {result.get('success')}")

                return result

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Interview Service HTTP Error: {e.response.status_code}")
            logger.error(f"   Response: {e.response.text}")
            raise Exception(f"Interview Service error: {e.response.status_code} - {e.response.text}")
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
            logger.info(f"🔑 Validating interview token")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json={"token": token})
                response.raise_for_status()
                result = response.json()
                logger.info(f"✅ Token validated")
                return result
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Token validation failed: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"❌ Token validation error: {str(e)}")
            raise

    async def update_interview_status(self, interview_id: str, status: str) -> Dict:
        """Update interview status"""
        url = f"{self.base_url}/api/session/{interview_id}/status"

        try:
            logger.info(f"📝 Updating interview {interview_id} status to {status}")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.patch(url, json={"status": status})
                response.raise_for_status()
                result = response.json()
                logger.info(f"✅ Interview status updated")
                return result
        except Exception as e:
            logger.error(f"❌ Status update failed: {str(e)}")
            raise