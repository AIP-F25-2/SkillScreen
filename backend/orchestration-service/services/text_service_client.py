import httpx
from config.settings import settings
from config.logger import logger
from typing import Dict, Optional

class TextServiceClient:
    def __init__(self):
        self.base_url = settings.TEXT_SERVICE_URL
        self.timeout = settings.TEXT_SERVICE_TIMEOUT

    async def start_interview(
        self,
        interview_id: str,
        candidate_id: str
    ) -> Dict:
        """Start interview and get first question"""
        url = f"{self.base_url}/api/interviews/start"

        payload = {
            "interview_id": interview_id,
            "candidate_id": candidate_id
        }

        try:
            logger.info(f"📝 Starting interview {interview_id} via text-service")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                logger.info(f"✅ Interview started, first question retrieved")
                return result
        except Exception as e:
            logger.error(f"❌ Start interview failed: {str(e)}")
            raise

    async def submit_response(
        self,
        interview_id: str,
        session_id: str,
        response_text: str,
        expected_answer_points: Optional[list] = None
    ) -> Dict:
        """Submit candidate response and get evaluation"""
        url = f"{self.base_url}/api/interviews/{interview_id}/respond"

        payload = {
            "interview_id": interview_id,
            "session_id": session_id,
            "response_text": response_text
        }

        if expected_answer_points:
            payload["expected_answer_points"] = expected_answer_points

        try:
            logger.info(f"📝 Submitting response for session {session_id}")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                logger.info(f"✅ Response evaluated")
                return result
        except Exception as e:
            logger.error(f"❌ Submit response failed: {str(e)}")
            raise

    async def get_next_question(
        self,
        interview_id: str,
        candidate_id: str,
        job_position_id: str
    ) -> Dict:
        """Get dynamically generated next question"""
        url = f"{self.base_url}/api/interviews/{interview_id}/next-question"

        payload = {
            "candidate_id": candidate_id,
            "job_position_id": job_position_id
        }

        try:
            logger.info(f"📝 Generating next question for interview {interview_id}")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                logger.info(f"✅ Next question generated")
                return result
        except Exception as e:
            logger.error(f"❌ Get next question failed: {str(e)}")
            raise

    async def evaluate_interview(self, interview_id: str) -> Dict:
        """Get overall interview evaluation and scores"""
        url = f"{self.base_url}/api/interviews/{interview_id}/evaluate"

        try:
            logger.info(f"📊 Evaluating interview {interview_id}")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url)
                response.raise_for_status()
                result = response.json()
                logger.info(f"✅ Interview evaluation complete")
                return result
        except Exception as e:
            logger.error(f"❌ Evaluate interview failed: {str(e)}")
            raise

    async def generate_questions(
        self,
        interview_id: str,
        candidate_id: str,
        job_position_id: str,
        num_questions: int = 5
    ) -> Dict:
        """Generate initial interview questions"""
        url = f"{self.base_url}/api/questions/generate"

        payload = {
            "interview_id": interview_id,
            "candidate_id": candidate_id,
            "job_position_id": job_position_id,
            "num_questions": num_questions
        }

        try:
            logger.info(f"🔄 Generating {num_questions} questions for interview {interview_id}")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                logger.info(f"✅ Questions generated")
                return result
        except Exception as e:
            logger.error(f"❌ Generate questions failed: {str(e)}")
            raise

    async def get_session(self, session_id: str) -> Dict:
        """Get session (question) details by ID"""
        url = f"{self.base_url}/api/sessions/{session_id}"

        try:
            logger.info(f"📋 Getting session {session_id}")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                result = response.json()
                return result.get("data", {})
        except Exception as e:
            logger.error(f"❌ Get session failed: {str(e)}")
            raise