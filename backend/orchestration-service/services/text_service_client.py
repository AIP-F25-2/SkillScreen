import httpx
from config.settings import settings
from config.logger import logger
from typing import Dict

class TextServiceClient:
    def __init__(self):
        self.base_url = settings.TEXT_SERVICE_URL
        self.timeout = settings.TEXT_SERVICE_TIMEOUT
    
    async def start_interview(
        self,
        candidate_id: str,
        job_id: str,
        interview_type: str,
        difficulty: str,
        max_questions: int
    ) -> Dict:
        """Start interview - get first question"""
        url = f"{self.base_url}/api/interviews/start"
        
        payload = {
            "candidate_id": candidate_id,
            "job_id": job_id,
            "interview_type": interview_type,
            "difficulty": difficulty,
            "max_questions": max_questions
        }
        
        try:
            logger.info("📝 Starting interview via text-service")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"❌ Start interview failed: {str(e)}")
            raise
    
    async def evaluate_and_generate_next_question(
        self,
        session_id: str,
        question_id: str,
        candidate_response: str,
        response_time_seconds: float
    ) -> Dict:
        """Evaluate response + generate next question"""
        url = f"{self.base_url}/api/interviews/{session_id}/respond"
        
        payload = {
            "response_text": candidate_response,
            "question_id": question_id,
            "response_time_seconds": response_time_seconds
        }
        
        try:
            logger.info("📝 Calling text-service for evaluation + next question")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("status") == "continue":
                    return {
                        "status": "continue",
                        "next_question": data["next_question"]["question_text"],
                        "next_question_id": data["next_question"]["id"],
                        "evaluation_score": data.get("current_score", 0.0),
                        "feedback": "Response evaluated",
                        "anti_cheating_flags": data.get("anti_cheating_flags", {})
                    }
                elif data.get("status") == "completed":
                    return {
                        "status": "completed",
                        "summary": data.get("summary", {}),
                        "termination_reason": data.get("termination_reason", "completed")
                    }
                else:
                    raise Exception(f"Unexpected status: {data.get('status')}")
        except Exception as e:
            logger.error(f"❌ Text service failed: {str(e)}")
            raise