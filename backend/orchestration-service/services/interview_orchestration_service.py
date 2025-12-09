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
CODING_SERVICE_URL = os.getenv("CODING_SERVICE_URL", "http://coding-service:8080")
AUDIO_AI_SERVICE_URL = os.getenv("AUDIO_AI_SERVICE_URL", "http://audio-ai-service:8080")
VIDEO_AI_SERVICE_URL = os.getenv("VIDEO_AI_SERVICE_URL", "http://video-ai-service:8080")
MEDIA_SERVICE_URL = os.getenv("MEDIA_SERVICE_URL", "http://media-service:8080")

UNKNOWN_ERROR = "Unknown error"


class InterviewOrchestrationService:
    """Service for orchestrating interview question generation"""
    
    def __init__(self):
        self.interview_service_url = INTERVIEW_SERVICE_URL
        self.text_service_url = TEXT_SERVICE_URL
        self.client = httpx.AsyncClient(timeout=60.0)
    
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
        job_data: Optional[Dict[str, Any]] = None,
        interview_id: Optional[str] = None
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
            # Create candidate in text-service
            text_service_candidate_id = await self._create_text_service_candidate(candidate_data, resume_data)
            
            # Create job in text-service
            text_service_job_id = await self._create_text_service_job(job_data, resume_data)
            
            # Start interview session in text-service
            session_info = await self._start_text_service_session(text_service_candidate_id, text_service_job_id)
            session_id = session_info.get("session_id")
            first_question = session_info.get("first_question", "Tell me about yourself and your experience with this role.")

            # Optionally generate a coding question
            coding_question = await self._generate_coding_question_if_needed(
                candidate_data, resume_data, job_data, interview_id
            )
            
            candidate_name = candidate_data.get("candidate_name") or resume_data.get("name", "Candidate")
            logger.info(f"Created interview session {session_id} for candidate {candidate_name}")
            
            result = {
                "session_id": session_id,
                "first_question": first_question,
                "text_service_candidate_id": text_service_candidate_id,
                "text_service_job_id": text_service_job_id
            }

            if coding_question:
                result["coding_question"] = coding_question

            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Session creation HTTP error: {e.response.text}")
            return self._get_fallback_session_result(resume_data)
        except Exception as e:
            logger.error(f"Session creation error: {str(e)}")
            return self._get_fallback_session_result(resume_data)

    async def _create_text_service_candidate(self, candidate_data: Dict[str, Any], resume_data: Dict[str, Any]) -> str:
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
        return candidate_result.get("data", {}).get("candidate_id") or candidate_result.get("candidate_id")

    async def _create_text_service_job(self, job_data: Optional[Dict[str, Any]], resume_data: Dict[str, Any]) -> str:
        if not job_data:
            job_payload = {
                "title": "Software Engineer",
                "company": "Company",
                "description": "",
                "required_skills": resume_data.get("skills", [])[:5],
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
        return job_result.get("data", {}).get("job_id") or job_result.get("job_id")

    async def _start_text_service_session(self, candidate_id: str, job_id: str) -> Dict[str, Any]:
        interview_response = await self.client.post(
            f"{self.text_service_url}/interviews/start",
            json={
                "candidate_id": candidate_id,
                "job_id": job_id
            }
        )
        interview_response.raise_for_status()
        return interview_response.json()

    async def _generate_coding_question_if_needed( # nosonar
        self,
        candidate_data: Dict[str, Any],
        resume_data: Dict[str, Any],
        job_data: Optional[Dict[str, Any]],
        interview_id: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        try:
            include_coding = False
            coding_skills = ["python", "java", "javascript", "typescript", "c++", "c#", "cpp", "go", "rust", "swift", "kotlin", "scala", "ruby", "php", "r", "matlab"]
            
            if job_data and job_data.get("requires_coding"):
                include_coding = True
                logger.info(f"Coding question requested via job_data for interview {interview_id}")
            elif resume_data.get("skills"):
                skills_list = [s.lower().strip() for s in resume_data.get("skills", [])]
                matched_skills = [s for s in skills_list if any(cs in s or s in cs for cs in coding_skills)]
                if matched_skills:
                    include_coding = True
                    logger.info(f"Coding question requested based on skills: {matched_skills} for interview {interview_id}")
                else:
                    logger.info(f"No matching coding skills found. Candidate skills: {skills_list[:10]}")

            if not include_coding:
                logger.info(f"Skipping coding question generation for interview {interview_id} - not required")
                return None

            logger.info(f"Generating coding question for interview {interview_id}...")
            
            # Assess difficulty
            assess_payload = {"resumeData": resume_data, "jobDescription": job_data or {}}
            logger.debug(f"Calling coding service for difficulty assessment: {CODING_SERVICE_URL}/difficulty/assess")
            resp = await self.client.post(f"{CODING_SERVICE_URL}/difficulty/assess", json=assess_payload)
            resp.raise_for_status()
            assess_result = resp.json()
            difficulty = assess_result.get("data", {}).get("difficulty") or assess_result.get("difficulty") or "medium"
            logger.info(f"Assessed difficulty: {difficulty} for interview {interview_id}")

            # Generate question
            candidate_id_str = str(candidate_data.get("candidateId")) if candidate_data.get("candidateId") else None
            interview_id_str = str(interview_id) if interview_id else None
            
            generate_payload = {
                "resumeData": resume_data,
                "jobDescription": job_data or {},
                "difficulty": difficulty,
                "questionNumber": 1,
                "previousQuestions": [],
                "candidateId": candidate_id_str,
                "interviewId": interview_id_str
            }
            logger.debug(f"Calling coding service to generate question: {CODING_SERVICE_URL}/questions/generate")
            qresp = await self.client.post(f"{CODING_SERVICE_URL}/questions/generate", json=generate_payload)
            qresp.raise_for_status()
            qresp_json = qresp.json()
            coding_question = qresp_json.get("data") or qresp_json
            
            if coding_question:
                logger.info(f"Successfully generated coding question for interview {interview_id}")
                return coding_question
            else:
                logger.warning(f"Coding question response is empty for interview {interview_id}. Response: {qresp_json}")
                return None

        except Exception as e:
            logger.error(f"Error creating coding question for interview {interview_id}: {type(e).__name__}: {str(e)}", exc_info=True)
            return None

    def _get_fallback_session_result(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
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
            # Check if this should be a coding question (e.g., Q9 out of 10)
            # We assume a standard 10-question interview for now
            TOTAL_QUESTIONS = 10
            if question_number == TOTAL_QUESTIONS - 1:
                logger.info(f"Question {question_number} is the penultimate question. Checking for coding question...")
                coding_question = await self._generate_coding_question_if_needed(
                    candidate_data={}, # We might need to fetch this if not available, but for now pass empty or rely on resume_data
                    resume_data=resume_data or {},
                    job_data=None, # We don't have job_data here easily without fetching, rely on resume
                    interview_id=interview_id
                )
                
                if coding_question:
                    logger.info(f"Injecting coding question for interview {interview_id}")
                    # Return structured data for coding question
                    # We need to ensure the controller and frontend can handle this JSON string or dict
                    # For now, we'll return a special marker or JSON string that the frontend can parse
                    import json
                    return json.dumps({
                        "type": "coding",
                        "data": coding_question,
                        "text": "Please solve the following coding challenge."
                    })

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
    
    def _generate_contextual_followup( # nosonar
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
            # Question 9 - wrap up
            if question_number == 9:
                return "Thank you for your responses. Do you have any questions for us about the role or company?"
            # Question 10+ - finish interview
            return None
    
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
    
    async def trigger_audio_analysis(
        self,
        interview_id: str,
        session_id: str,
        media_file_id: str
    ) -> Dict[str, Any]:
        """
        Trigger audio analysis for interview video/audio
        
        Args:
            interview_id: Interview ID
            session_id: Session ID
            media_file_id: Media file ID from media_files table
            
        Returns:
            Result dictionary with status and error info if failed
        """
        try:
            # Ensure all IDs are strings for JSON serialization
            interview_id_str = str(interview_id)
            session_id_str = str(session_id)
            media_file_id_str = str(media_file_id)
            
            logger.info(f"Triggering audio analysis for interview {interview_id_str}, media_file {media_file_id_str}")
            
            response = await self.client.post(
                f"{AUDIO_AI_SERVICE_URL}/process-interview-audio",
                json={
                    "interview_id": interview_id_str,
                    "session_id": session_id_str,
                    "media_file_id": media_file_id_str
                },
                timeout=60.0  # Increased timeout for audio processing
            )
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Audio analysis triggered successfully for interview {interview_id}")
            return {
                "status": "success",
                "service": "audio-ai",
                "result": result
            }
            
        except httpx.TimeoutException as e:
            logger.error(f"Audio analysis timeout for interview {interview_id}: {str(e)}")
            return {
                "status": "error",
                "service": "audio-ai",
                "error": f"Timeout: {str(e)}"
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"Audio analysis HTTP error for interview {interview_id}: {e.response.status_code} - {e.response.text}")
            return {
                "status": "error",
                "service": "audio-ai",
                "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            }
        except Exception as e:
            logger.error(f"Audio analysis error for interview {interview_id}: {type(e).__name__}: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "service": "audio-ai",
                "error": f"{type(e).__name__}: {str(e)}"
            }
    
    async def trigger_video_analysis(
        self,
        interview_id: str,
        video_url: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Trigger video analysis for interview video
        
        Args:
            interview_id: Interview ID (used as user_id if not provided)
            video_url: Video URL or path
            user_id: Optional user ID (defaults to interview_id)
            
        Returns:
            Result dictionary with status and error info if failed
        """
        try:
            # Ensure ALL IDs are converted to strings for JSON serialization (in case they're UUID objects)
            interview_id_str = str(interview_id) if interview_id else None
            user_id_str = str(user_id) if user_id else interview_id_str
            
            logger.info(f"Triggering video analysis for interview {interview_id_str}, user_id: {user_id_str}, video: {video_url}")
            
            # Double-check: ensure video_url is also a string (not a UUID or other object)
            video_url_str = str(video_url) if video_url else ""
            
            response = await self.client.post(
                f"{VIDEO_AI_SERVICE_URL}/analyze-url",
                json={
                    "user_id": user_id_str,
                    "video_url": video_url_str
                },
                timeout=300.0  # Video analysis can take longer
            )
            response.raise_for_status()
            result = response.json()
            
            interview_id_for_log = interview_id_str if 'interview_id_str' in locals() else str(interview_id) # nosonar
            logger.info(f"Video analysis triggered successfully for interview {interview_id_for_log}")
            return {
                "status": "success",
                "service": "video-ai",
                "result": result
            }
            
        except httpx.TimeoutException as e:
            interview_id_for_log = interview_id_str if 'interview_id_str' in locals() else str(interview_id) # nosonar
            logger.error(f"Video analysis timeout for interview {interview_id_for_log}: {str(e)}")
            return {
                "status": "error",
                "service": "video-ai",
                "error": f"Timeout: {str(e)}"
            }
        except httpx.HTTPStatusError as e:
            interview_id_for_log = interview_id_str if 'interview_id_str' in locals() else str(interview_id) # nosonar
            logger.error(f"Video analysis HTTP error for interview {interview_id_for_log}: {e.response.status_code} - {e.response.text}")
            return {
                "status": "error",
                "service": "video-ai",
                "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            }
        except Exception as e:
            interview_id_for_log = interview_id_str if 'interview_id_str' in locals() else str(interview_id) # nosonar
            logger.error(f"Video analysis error for interview {interview_id_for_log}: {type(e).__name__}: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "service": "video-ai",
                "error": f"{type(e).__name__}: {str(e)}"
            }
    
    async def get_text_analysis( # nosonar
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Get text analysis summary for interview
        
        Args:
            session_id: Session ID from text-service
            
        Returns:
            Result dictionary with status and analysis data
        """
        # Ensure session_id is a string
        session_id_str = str(session_id)
        
        try:
            logger.info(f"Getting text analysis summary for session {session_id_str}")
            
            # Try multiple endpoint paths in case the session_id format is different
            endpoints_to_try = [
                f"{self.text_service_url}/api/interviews/{session_id_str}/summary",
                f"{self.text_service_url}/interviews/{session_id_str}/summary",
            ]
            
            last_error = None
            for endpoint in endpoints_to_try:
                try:
                    logger.debug(f"Trying endpoint: {endpoint}")
                    response = await self.client.get(endpoint, timeout=30.0)
                    response.raise_for_status()
                    result = response.json()
                    
                    logger.info(f"Text analysis retrieved successfully for session {session_id_str}")
                    return {
                        "status": "success",
                        "service": "text-service",
                        "result": result
                    }
                except httpx.HTTPStatusError as e:
                    last_error = e
                    if e.response.status_code == 404:
                        logger.debug(f"Endpoint {endpoint} returned 404, trying next...")
                        continue
                    else:
                        # Non-404 error - raise immediately to be caught by outer exception handler
                        raise
                except Exception as e:
                    last_error = e
                    logger.debug(f"Error trying endpoint {endpoint}: {e}")
                    continue
            
            # If we get here, all endpoints failed with 404
            if last_error:
                error_msg = str(last_error)
                if isinstance(last_error, httpx.HTTPStatusError):
                    error_msg = f"HTTP {last_error.response.status_code}: {last_error.response.text[:200]}"
                
                # Check if the error is about session not existing - this is expected if text-service wasn't used
                if "Interview session not found" in error_msg or "Not Found" in error_msg:
                    logger.info(
                        f"Text service session {session_id_str} not found. "
                        "This is expected if the interview was not processed through text-service. "
                        "Text analysis may not be available for this interview."
                    )
                    return {
                        "status": "skipped",
                        "service": "text-service",
                        "message": "Text service session not found. The interview may not have been processed through text-service.",
                        "hint": "Text analysis is only available for interviews that were processed through the text-service pipeline."
                    }
                else:
                    logger.warning(f"Text analysis endpoint failed for session {session_id_str}: {error_msg}")
                    return {
                        "status": "error",
                        "service": "text-service",
                        "error": f"HTTP 404: Interview session not found or endpoint does not exist. Tried: {endpoints_to_try}"
                    }
            
        except httpx.TimeoutException as e:
            logger.error(f"Text analysis timeout for session {session_id_str}: {str(e)}")
            return {
                "status": "error",
                "service": "text-service",
                "error": f"Timeout: {str(e)}"
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"Text analysis HTTP error for session {session_id_str}: {e.response.status_code} - {e.response.text}")
            return {
                "status": "error",
                "service": "text-service",
                "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            }
        except Exception as e:
            logger.error(f"Text analysis error for session {session_id_str}: {type(e).__name__}: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "service": "text-service",
                "error": f"{type(e).__name__}: {str(e)}"
            }
    
    async def trigger_all_analyses( # nosonar
        self,
        interview_id: str,
        session_id: str,
        media_file_id: Optional[str] = None,
        video_url: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Trigger all analyses (audio, video, text) for a completed interview
        
        This method is fault-tolerant - if any service fails, it logs the error
        and continues with the other services.
        
        Args:
            interview_id: Interview ID
            session_id: Session ID (from text-service or interview_id)
            media_file_id: Optional media file ID for audio analysis
            video_url: Optional video URL for video analysis
            user_id: Optional user ID for video analysis
            
        Returns:
            Dictionary with results from all services and summary
        """
        # Ensure ALL IDs are converted to strings (in case they're UUID objects)
        interview_id_str = str(interview_id) if interview_id else None
        session_id_str = str(session_id) if session_id else None
        media_file_id_str = str(media_file_id) if media_file_id else None
        user_id_str = str(user_id) if user_id else None
        
        results = {
            "interview_id": interview_id_str,
            "session_id": session_id_str,
            "analyses": {},
            "summary": {
                "total_services": 3,
                "successful": 0,
                "failed": 0,
                "errors": []
            }
        }
        
        # Trigger audio analysis (async, non-blocking)
        if media_file_id_str:
            logger.info(f"[Analysis Orchestration] Triggering audio analysis for interview {interview_id_str}")
            audio_result = await self.trigger_audio_analysis(
                interview_id=interview_id_str,
                session_id=session_id_str,
                media_file_id=media_file_id_str
            )
            results["analyses"]["audio"] = audio_result
            
            if audio_result["status"] == "success":
                results["summary"]["successful"] += 1
            else:
                results["summary"]["failed"] += 1
                results["summary"]["errors"].append({
                    "service": "audio-ai",
                    "error": audio_result.get("error", UNKNOWN_ERROR)
                })
        else:
            logger.warning(f"[Analysis Orchestration] Skipping audio analysis - no media_file_id provided for interview {interview_id_str}")
            results["analyses"]["audio"] = {
                "status": "skipped",
                "service": "audio-ai",
                "reason": "No media_file_id provided"
            }
        
        # Trigger video analysis (async, non-blocking)
        if video_url:
            logger.info(f"[Analysis Orchestration] Triggering video analysis for interview {interview_id_str}")
            video_result = await self.trigger_video_analysis(
                interview_id=interview_id_str,
                video_url=video_url,
                user_id=user_id_str
            )
            results["analyses"]["video"] = video_result
            
            if video_result["status"] == "success":
                results["summary"]["successful"] += 1
            else:
                results["summary"]["failed"] += 1
                results["summary"]["errors"].append({
                    "service": "video-ai",
                    "error": video_result.get("error", UNKNOWN_ERROR)
                })
        else:
            logger.warning(f"[Analysis Orchestration] Skipping video analysis - no video_url provided for interview {interview_id_str}")
            results["analyses"]["video"] = {
                "status": "skipped",
                "service": "video-ai",
                "reason": "No video_url provided"
            }
        
        # Get text analysis (may already be generated)
        logger.info(f"[Analysis Orchestration] Getting text analysis summary for session {session_id_str}")
        text_result = await self.get_text_analysis(session_id=session_id_str)
        results["analyses"]["text"] = text_result
        
        if text_result["status"] == "success":
            results["summary"]["successful"] += 1
        elif text_result["status"] == "skipped":
            # Text analysis skipped (e.g., session not found) - don't count as failure
            logger.info(f"Text analysis skipped for session {session_id_str}: {text_result.get('message', 'Session not found')}")
            # Don't increment failed count for skipped status
        else:
            results["summary"]["failed"] += 1
            results["summary"]["errors"].append({
                "service": "text-service",
                "error": text_result.get("error", UNKNOWN_ERROR)
            })
        
        # Log summary
        logger.info(
            f"[Analysis Orchestration] Completed for interview {interview_id_str}: "
            f"{results['summary']['successful']} successful, "
            f"{results['summary']['failed']} failed"
        )
        
        return results
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

