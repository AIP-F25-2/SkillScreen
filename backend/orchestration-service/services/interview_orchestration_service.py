"""
Interview Orchestration Service
Orchestrates the interview question generation pipeline by connecting:
- Interview Service (token validation, candidate/interview data)
- Text Service (resume parsing, question generation)
"""

import httpx
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from utilities.logger import init_logger

logger = init_logger("orchestration-service")

# Service URLs from environment
INTERVIEW_SERVICE_URL = os.getenv("INTERVIEW_SERVICE_URL", "http://interview-service:8080")
TEXT_SERVICE_URL = os.getenv("TEXT_SERVICE_URL", "http://text-service:8080")


class InterviewOrchestrationService:
    """Service for orchestrating interview question generation"""
    
    def __init__(self):
        self.interview_service_url = INTERVIEW_SERVICE_URL
        self.text_service_url = TEXT_SERVICE_URL
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def download_and_parse_resume(self, resume_url: str) -> Dict[str, Any]:
        """
        Download resume from Azure Blob Storage and parse it using text-service
        
        Args:
            resume_url: Azure Blob Storage SAS URL for the resume
            
        Returns:
            Parsed resume data (name, email, skills, experience, etc.)
        """
        try:
            # Download resume file
            resume_response = await self.client.get(resume_url, follow_redirects=True)
            resume_response.raise_for_status()
            resume_content = resume_response.content
            
            # Determine file extension from URL or content
            filename = "resume.pdf"
            if resume_url.lower().endswith('.pdf'):
                filename = "resume.pdf"
            elif resume_url.lower().endswith(('.doc', '.docx')):
                filename = "resume.doc"
            
            # Upload to text-service for parsing
            files = {"file": (filename, resume_content, "application/pdf")}
            
            parse_response = await self.client.post(
                f"{self.text_service_url}/resumes/parse",
                files=files
            )
            parse_response.raise_for_status()
            result = parse_response.json()
            
            # Extract parsed data from response
            if result.get("success"):
                parsed_data = result.get("data", {})
            else:
                parsed_data = result
            
            # Normalize field names (text-service might return different field names)
            normalized_data = {
                "name": parsed_data.get("name") or parsed_data.get("candidate_name"),
                "email": parsed_data.get("email") or parsed_data.get("candidate_email"),
                "phone": parsed_data.get("phone") or parsed_data.get("candidate_phone"),
                "skills": parsed_data.get("skills", []),
                "experience_years": parsed_data.get("experience_years", 0),
                "education": parsed_data.get("education", []),
                "work_experience": parsed_data.get("work_experience", []),
                "raw_text": parsed_data.get("raw_text", "")
            }
            
            logger.info(f"Resume parsed successfully: {normalized_data.get('name', 'Unknown')}")
            return normalized_data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Resume parsing HTTP error: {e.response.text}")
            raise ValueError(f"Failed to parse resume: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Resume parsing error: {str(e)}")
            raise
    
    async def create_interview_session(
        self,
        candidate_data: Dict[str, Any],
        resume_data: Dict[str, Any],
        job_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create an interview session in text-service with candidate and job data
        
        Args:
            candidate_data: Candidate information from database
            resume_data: Parsed resume data
            job_data: Optional job position data
            
        Returns:
            Session data with session_id and first question
        """
        try:
            # Create candidate in text-service (in-memory)
            candidate_name = candidate_data.get("candidate_name") or resume_data.get("name", "Candidate")
            candidate_payload = {
                "name": candidate_name,
                "email": candidate_data.get("candidateEmail", ""),
                "resume_text": resume_data.get("raw_text", ""),
                "experience_years": resume_data.get("experience_years", 0),
                "skills": resume_data.get("skills", [])
            }
            
            candidate_response = await self.client.post(
                f"{self.text_service_url}/candidates",
                json=candidate_payload
            )
            candidate_response.raise_for_status()
            candidate_result = candidate_response.json()
            text_service_candidate_id = candidate_result.get("data", {}).get("candidate_id") or candidate_result.get("candidate_id")
            
            # Create job in text-service (in-memory) if not provided
            if not job_data:
                job_payload = {
                    "title": "Software Engineer",  # Default job title
                    "company": "Company",
                    "description": "",
                    "required_skills": resume_data.get("skills", [])[:5],  # Use top 5 skills from resume
                    "experience_level": "mid"
                }
            else:
                job_payload = {
                    "title": job_data.get("title", "Position"),
                    "company": job_data.get("company", "Company"),
                    "description": job_data.get("description", ""),
                    "required_skills": job_data.get("required_skills", []),
                    "experience_level": job_data.get("experience_level", "mid")
                }
            
            job_response = await self.client.post(
                f"{self.text_service_url}/jobs",
                json=job_payload
            )
            job_response.raise_for_status()
            job_result = job_response.json()
            text_service_job_id = job_result.get("data", {}).get("job_id") or job_result.get("job_id")
            
            # Start interview session in text-service
            interview_response = await self.client.post(
                f"{self.text_service_url}/interviews/start",
                json={
                    "candidate_id": text_service_candidate_id,
                    "job_id": text_service_job_id
                }
            )
            interview_response.raise_for_status()
            interview_result = interview_response.json()
            
            session_id = interview_result.get("session_id")
            first_question = interview_result.get("first_question", "Tell me about yourself and your experience with this role.")
            
            logger.info(f"Created interview session {session_id} for candidate {candidate_name}")
            
            return {
                "session_id": session_id,
                "first_question": first_question,
                "text_service_candidate_id": text_service_candidate_id,
                "text_service_job_id": text_service_job_id
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Session creation HTTP error: {e.response.text}")
            # Fallback: generate question directly
            return {
                "session_id": None,
                "first_question": self._generate_fallback_question(resume_data),
                "text_service_candidate_id": None,
                "text_service_job_id": None
            }
        except Exception as e:
            logger.error(f"Session creation error: {str(e)}")
            # Fallback: generate question directly
            return {
                "session_id": None,
                "first_question": self._generate_fallback_question(resume_data),
                "text_service_candidate_id": None,
                "text_service_job_id": None
            }
    
    def _generate_fallback_question(self, resume_data: Dict[str, Any]) -> str:
        """Generate fallback question when text-service is unavailable"""
        skills = resume_data.get("skills", [])
        resume_text = resume_data.get("raw_text", "")
        
        if skills:
            top_skills = skills[:3]
            skills_str = ", ".join(top_skills)
            return f"Tell me about yourself and your experience with {skills_str}."
        elif resume_text:
            resume_lower = resume_text.lower()
            if any(keyword in resume_lower for keyword in ['python', 'java', 'javascript', 'react', 'angular', 'node']):
                return "Tell me about yourself and your experience in software development."
            elif any(keyword in resume_lower for keyword in ['data', 'analysis', 'machine learning', 'ai']):
                return "Tell me about yourself and your experience in data science and analytics."
        
        return "Tell me about yourself and your experience with this role."
    
    async def generate_next_question(
        self,
        interview_id: str,
        session_id: str,
        previous_response: str,
        question_number: int,
        resume_data: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Generate next question based on candidate's previous response
        
        Args:
            interview_id: Interview ID
            session_id: Session ID from text-service (or interview_id if session not created)
            previous_response: Candidate's response to previous question
            question_number: Current question number (1-indexed)
            resume_data: Optional resume data for context
            
        Returns:
            Generated follow-up question string, or None if interview completed
        """
        try:
            # If we have a valid session_id from text-service, use it
            if session_id and session_id.startswith("session_"):
                # Submit response to text-service to get next question
                response = await self.client.post(
                    f"{self.text_service_url}/interviews/{session_id}/respond",
                    json={
                        "response_text": previous_response
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                # Extract next question from response
                next_question = result.get("next_question")
                if not next_question:
                    # Check if interview is completed
                    if result.get("status") == "completed":
                        return None  # Interview completed
                    # Fallback
                    next_question = "Thank you for your response. Do you have any questions for us?"
                
                logger.info(f"Generated question #{question_number} for interview {interview_id}")
                return next_question
            else:
                # No text-service session, generate question based on response and resume
                return self._generate_contextual_followup(previous_response, question_number, resume_data)
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Next question generation HTTP error: {e.response.text}")
            # Fallback: generate contextual question
            return self._generate_contextual_followup(previous_response, question_number, resume_data)
        except Exception as e:
            logger.error(f"Next question generation error: {str(e)}")
            # Fallback: generate contextual question
            return self._generate_contextual_followup(previous_response, question_number, resume_data)
    
    def _generate_contextual_followup(
        self,
        previous_response: str,
        question_number: int,
        resume_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate contextual follow-up question based on response"""
        response_lower = previous_response.lower()
        skills = resume_data.get("skills", []) if resume_data else []
        
        # Question 2: Based on response content
        if question_number == 1:
            if any(word in response_lower for word in ['project', 'worked', 'developed', 'built']):
                return "Can you tell me about a specific project you mentioned? What challenges did you face and how did you overcome them?"
            elif any(word in response_lower for word in ['team', 'collaborate', 'lead']):
                return "You mentioned working with teams. Can you describe a time when you had to collaborate with a difficult team member?"
            else:
                return "What are your key strengths that make you a good fit for this role?"
        
        # Question 3: Technical depth
        elif question_number == 2:
            if skills:
                top_skill = skills[0] if skills else "your primary technology"
                return f"I see you have experience with {top_skill}. Can you describe a challenging technical problem you solved using {top_skill}?"
            else:
                return "Can you walk me through your approach to solving a complex technical problem?"
        
        # Question 4-9: Progressive questions
        elif question_number == 3:
            return "How do you stay updated with the latest trends and technologies in your field?"
        elif question_number == 4:
            return "Describe a time when you had to learn a new technology quickly for a project. How did you approach it?"
        elif question_number == 5:
            return "Tell me about a time when you had to make a difficult decision at work. What was the situation and outcome?"
        elif question_number == 6:
            return "How do you handle tight deadlines and pressure in your work?"
        elif question_number == 7:
            return "What motivates you most in your professional life?"
        elif question_number == 8:
            return "Where do you see yourself in 3-5 years, and how does this role align with your career goals?"
        else:
            # Question 9 or beyond - wrap up
            return "Thank you for your responses. Do you have any questions for us about the role or company?"
    
    async def get_interview_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Get interview summary after completion
        
        Args:
            session_id: Session ID
            
        Returns:
            Interview summary with scores and recommendations
        """
        try:
            response = await self.client.get(
                f"{self.text_service_url}/interviews/{session_id}/summary"
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Get summary HTTP error: {e.response.text}")
            raise ValueError(f"Failed to get interview summary: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Get summary error: {str(e)}")
            raise
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

