"""
Text Service Client

Handles communication with text-service for:
- Question generation
- Response evaluation
- Interview summary generation
"""

import httpx
import logging
from typing import Dict, Any, Optional, List
from config import settings

logger = logging.getLogger(__name__)


class TextServiceClient:
    """Client for text-service API"""
    
    def __init__(self):
        self.base_url = settings.TEXT_SERVICE_URL
        self.timeout = settings.SERVICE_TIMEOUT
        
    async def generate_question(
        self,
        interview_id: str,
        candidate_id: str,
        job_position_id: str,
        question_number: int,
        interview_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate interview question
        
        Calls text-service to generate contextual question based on:
        - Candidate profile
        - Job requirements
        - Previous Q&A history
        - Interview type
        """
        try:
            logger.info(f"Generating question {question_number} for interview {interview_id}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/interviews/generate-question",
                    json={
                        "interview_id": interview_id,
                        "candidate_id": candidate_id,
                        "job_position_id": job_position_id,
                        "question_number": question_number,
                        "interview_type": interview_type,
                        "context": context or {}
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"✅ Question generated successfully")
                
                return {
                    "question_id": result.get("question_id"),
                    "question_text": result.get("question_text"),
                    "question_type": result.get("question_type"),
                    "metadata": result.get("metadata", {})
                }
                
        except httpx.HTTPError as e:
            logger.error(f"❌ HTTP error generating question: {str(e)}")
            raise Exception(f"Failed to generate question: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error generating question: {str(e)}")
            raise
    
    async def evaluate_response(
        self,
        interview_id: str,
        question_id: str,
        question_text: str,
        response_text: str,
        candidate_id: str,
        job_position_id: str
    ) -> Dict[str, Any]:
        """
        Evaluate candidate response
        
        Calls text-service to evaluate:
        - Relevance
        - Technical accuracy
        - Communication quality
        - Depth and completeness
        """
        try:
            logger.info(f"Evaluating response for question {question_id}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/interviews/evaluate-response",
                    json={
                        "interview_id": interview_id,
                        "question_id": question_id,
                        "question_text": question_text,
                        "response_text": response_text,
                        "candidate_id": candidate_id,
                        "job_position_id": job_position_id
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"✅ Response evaluated successfully")
                
                return result
                
        except httpx.HTTPError as e:
            logger.error(f"❌ HTTP error evaluating response: {str(e)}")
            raise Exception(f"Failed to evaluate response: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error evaluating response: {str(e)}")
            raise
    
    async def generate_interview_summary(
        self,
        interview_id: str,
        candidate_id: str,
        job_position_id: str,
        sessions: List[Dict[str, Any]],
        audio_analyses: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive interview summary
        
        Calls text-service to generate:
        - Overall assessment
        - Recommendation
        - Strengths and weaknesses
        - Next steps
        """
        try:
            logger.info(f"Generating summary for interview {interview_id}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/interviews/generate-summary",
                    json={
                        "interview_id": interview_id,
                        "candidate_id": candidate_id,
                        "job_position_id": job_position_id,
                        "sessions": sessions,
                        "audio_analyses": audio_analyses or []
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"✅ Summary generated successfully")
                
                return result
                
        except httpx.HTTPError as e:
            logger.error(f"❌ HTTP error generating summary: {str(e)}")
            raise Exception(f"Failed to generate summary: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error generating summary: {str(e)}")
            raise

