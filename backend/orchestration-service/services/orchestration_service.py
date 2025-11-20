"""
Interview Orchestration Service

This service coordinates the entire interview workflow:
1. Interview creation and management
2. Question generation
3. Answer submission and processing
4. Multi-service coordination (text, audio, video)
5. Result aggregation and summary generation
"""

import uuid
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from services.text_service_client import TextServiceClient
from services.audio_service_client import AudioServiceClient
from services.video_service_client import VideoServiceClient
from services.media_service_client import MediaServiceClient
from db import UnitOfWork
from repositories.orchestration_repository import OrchestrationRepository

logger = logging.getLogger(__name__)


class OrchestrationService:
    """
    Central orchestration service for managing interview workflows
    """
    
    def __init__(self):
        self.text_client = TextServiceClient()
        self.audio_client = AudioServiceClient()
        self.video_client = VideoServiceClient()
        self.media_client = MediaServiceClient()
        
    async def create_interview(
        self,
        candidate_id: str,
        job_position_id: str,
        interview_type: str = "mixed",
        max_questions: int = 15
    ) -> Dict[str, Any]:
        """
        Create a new interview session
        
        Steps:
        1. Create interview record in database
        2. Get candidate and job details
        3. Generate first question from text-service
        4. Return interview details
        """
        try:
            logger.info(f"Creating interview for candidate {candidate_id}, job {job_position_id}")
            
            uow = UnitOfWork()
            repo = OrchestrationRepository(uow)
            
            # Create interview record
            interview_id = str(uuid.uuid4())
            interview_data = {
                "id": interview_id,
                "candidate_id": candidate_id,
                "job_position_id": job_position_id,
                "interview_type": interview_type,
                "max_questions": max_questions,
                "status": "in_progress",
                "current_question_number": 0,
                "total_questions_asked": 0,
                "start_time": datetime.now(timezone.utc)
            }
            
            repo.create_interview(interview_data)
            uow.session.commit()
            
            # Get candidate and job details
            candidate = repo.get_candidate(candidate_id)
            job_position = repo.get_job_position(job_position_id)
            
            if not candidate or not job_position:
                raise ValueError("Candidate or job position not found")
            
            # Generate first question from text-service
            first_question = await self.text_client.generate_question(
                interview_id=interview_id,
                candidate_id=candidate_id,
                job_position_id=job_position_id,
                question_number=1,
                interview_type=interview_type,
                context={
                    "candidate_name": candidate.get("name"),
                    "job_title": job_position.get("title"),
                    "skills": job_position.get("required_skills", [])
                }
            )
            
            # Create session record for first question
            session_id = str(uuid.uuid4())
            session_data = {
                "id": session_id,
                "interview_id": interview_id,
                "question_id": first_question.get("question_id"),
                "question_number": 1,
                "question_text": first_question.get("question_text"),
                "status": "pending"
            }
            
            repo.create_session(session_data)
            
            # Update interview
            repo.update_interview(interview_id, {
                "current_question_number": 1,
                "total_questions_asked": 1
            })
            
            uow.session.commit()
            
            logger.info(f"✅ Interview {interview_id} created successfully")
            
            return {
                "interview_id": interview_id,
                "session_id": session_id,
                "first_question": first_question,
                "status": "created"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create interview: {str(e)}", exc_info=True)
            raise
    
    async def get_next_question(
        self,
        interview_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get next question for the interview
        
        Steps:
        1. Check if interview can continue
        2. Get previous responses for context
        3. Generate next question from text-service
        4. Create new session record
        """
        try:
            logger.info(f"Getting next question for interview {interview_id}")
            
            uow = UnitOfWork()
            repo = OrchestrationRepository(uow)
            
            # Get interview details
            interview = repo.get_interview(interview_id)
            
            if not interview:
                raise ValueError(f"Interview {interview_id} not found")
            
            # Check if interview can continue
            if interview["status"] != "in_progress":
                raise ValueError(f"Interview is not in progress. Status: {interview['status']}")
            
            if interview["current_question_number"] >= interview["max_questions"]:
                raise ValueError("Maximum questions reached")
            
            # Get candidate and job details
            candidate = repo.get_candidate(interview["candidate_id"])
            job_position = repo.get_job_position(interview["job_position_id"])
            
            # Get previous responses for context
            previous_sessions = repo.get_interview_sessions(interview_id)
            
            # Generate next question
            next_question_number = interview["current_question_number"] + 1
            
            next_question = await self.text_client.generate_question(
                interview_id=interview_id,
                candidate_id=interview["candidate_id"],
                job_position_id=interview["job_position_id"],
                question_number=next_question_number,
                interview_type=interview["interview_type"],
                context={
                    "candidate_name": candidate.get("name"),
                    "job_title": job_position.get("title"),
                    "skills": job_position.get("required_skills", []),
                    "previous_questions": [s.get("question_text") for s in previous_sessions],
                    "previous_answers": [s.get("text_answer") for s in previous_sessions if s.get("text_answer")],
                    **(context or {})
                }
            )
            
            # Create new session
            session_id = str(uuid.uuid4())
            session_data = {
                "id": session_id,
                "interview_id": interview_id,
                "question_id": next_question.get("question_id"),
                "question_number": next_question_number,
                "question_text": next_question.get("question_text"),
                "status": "pending"
            }
            
            repo.create_session(session_data)
            
            # Update interview
            repo.update_interview(interview_id, {
                "current_question_number": next_question_number,
                "total_questions_asked": next_question_number
            })
            
            uow.session.commit()
            
            logger.info(f"✅ Generated question {next_question_number} for interview {interview_id}")
            
            return {
                "question_id": next_question.get("question_id"),
                "session_id": session_id,
                "question_text": next_question.get("question_text"),
                "question_number": next_question_number,
                "question_type": next_question.get("question_type"),
                "metadata": next_question.get("metadata", {})
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get next question: {str(e)}", exc_info=True)
            raise
    
    async def submit_answer(
        self,
        interview_id: str,
        session_id: str,
        question_id: str,
        text_answer: str,
        media_file_id: Optional[str] = None,
        response_time_seconds: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Submit answer to interview question
        
        Steps:
        1. Validate interview and session
        2. Store text answer
        3. Link media file if provided
        4. Mark session as answered
        5. Return processing status
        """
        try:
            logger.info(f"Submitting answer for session {session_id}")
            
            uow = UnitOfWork()
            repo = OrchestrationRepository(uow)
            
            # Validate session
            session = repo.get_session(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            if session["interview_id"] != interview_id:
                raise ValueError("Session does not belong to this interview")
            
            # Update session with answer
            answer_data = {
                "text_answer": text_answer,
                "media_file_id": media_file_id,
                "response_time_seconds": response_time_seconds,
                "answered_at": datetime.now(timezone.utc),
                "status": "answered"
            }
            
            repo.update_session(session_id, answer_data)
            uow.session.commit()
            
            logger.info(f"✅ Answer submitted for session {session_id}")
            
            return {
                "session_id": session_id,
                "status": "answered",
                "processing_status": "pending" if media_file_id else "completed"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to submit answer: {str(e)}", exc_info=True)
            raise
    
    async def process_media_in_background(
        self,
        interview_id: str,
        session_id: str,
        media_file_id: str
    ):
        """
        Process media files in background
        
        Steps:
        1. Get media file details from media-service
        2. Trigger audio-ai-service for audio analysis
        3. Trigger video-ai-service for video analysis
        4. Wait for processing completion
        5. Store results
        """
        try:
            logger.info(f"🔄 Starting background media processing for session {session_id}")
            
            uow = UnitOfWork()
            repo = OrchestrationRepository(uow)
            
            # Update processing status
            repo.update_session(session_id, {"processing_status": "processing"})
            uow.session.commit()
            
            # Trigger audio-ai-service
            logger.info(f"📢 Triggering audio-ai-service for media {media_file_id}")
            audio_result = await self.audio_client.process_interview_audio(
                interview_id=interview_id,
                session_id=session_id,
                media_file_id=media_file_id
            )
            
            logger.info(f"✅ Audio processing triggered: {audio_result.get('status')}")
            
            # Note: Video processing can be added similarly if needed
            # video_result = await self.video_client.analyze_video(...)
            
            # Update processing status
            repo.update_session(session_id, {
                "processing_status": "completed",
                "audio_processing_status": audio_result.get("status")
            })
            uow.session.commit()
            
            logger.info(f"✅ Background media processing completed for session {session_id}")
            
        except Exception as e:
            logger.error(f"❌ Background media processing failed: {str(e)}", exc_info=True)
            
            # Update error status
            try:
                uow = UnitOfWork()
                repo = OrchestrationRepository(uow)
                repo.update_session(session_id, {
                    "processing_status": "failed",
                    "processing_error": str(e)
                })
                uow.session.commit()
            except:
                pass
    
    async def complete_interview(self, interview_id: str) -> Dict[str, Any]:
        """
        Complete interview and mark for summary generation
        
        Steps:
        1. Validate interview
        2. Mark as completed
        3. Calculate basic metrics
        """
        try:
            logger.info(f"Completing interview {interview_id}")
            
            uow = UnitOfWork()
            repo = OrchestrationRepository(uow)
            
            interview = repo.get_interview(interview_id)
            if not interview:
                raise ValueError(f"Interview {interview_id} not found")
            
            # Calculate duration
            start_time = interview.get("start_time")
            end_time = datetime.now(timezone.utc)
            duration_minutes = None
            
            if start_time:
                duration_seconds = (end_time - start_time).total_seconds()
                duration_minutes = duration_seconds / 60
            
            # Update interview
            repo.update_interview(interview_id, {
                "status": "completed",
                "end_time": end_time,
                "duration_minutes": duration_minutes
            })
            
            uow.session.commit()
            
            logger.info(f"✅ Interview {interview_id} completed")
            
            return {
                "interview_id": interview_id,
                "status": "completed",
                "duration_minutes": duration_minutes
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to complete interview: {str(e)}", exc_info=True)
            raise
    
    async def generate_interview_summary(self, interview_id: str):
        """
        Generate comprehensive interview summary
        
        Steps:
        1. Get all interview data
        2. Collect text evaluation results
        3. Collect audio analysis results
        4. Collect video analysis results
        5. Generate final summary using text-service
        6. Store summary
        """
        try:
            logger.info(f"📊 Generating summary for interview {interview_id}")
            
            uow = UnitOfWork()
            repo = OrchestrationRepository(uow)
            
            interview = repo.get_interview(interview_id)
            if not interview:
                raise ValueError(f"Interview {interview_id} not found")
            
            # Get candidate and job details
            candidate = repo.get_candidate(interview["candidate_id"])
            job_position = repo.get_job_position(interview["job_position_id"])
            
            # Get all sessions with answers
            sessions = repo.get_interview_sessions(interview_id)
            answered_sessions = [s for s in sessions if s.get("text_answer")]
            
            # Collect audio analysis results
            audio_analyses = []
            for session in answered_sessions:
                if session.get("media_file_id"):
                    try:
                        analysis = await self.audio_client.get_audio_analysis(
                            interview_id=interview_id,
                            session_id=session["id"]
                        )
                        audio_analyses.append(analysis)
                    except Exception as e:
                        logger.warning(f"Could not get audio analysis for session {session['id']}: {e}")
            
            # Generate summary from text-service
            summary_data = await self.text_client.generate_interview_summary(
                interview_id=interview_id,
                candidate_id=interview["candidate_id"],
                job_position_id=interview["job_position_id"],
                sessions=answered_sessions,
                audio_analyses=audio_analyses
            )
            
            # Store summary
            summary_record = {
                "interview_id": interview_id,
                "overall_score": summary_data.get("overall_score"),
                "recommendation": summary_data.get("recommendation"),
                "text_evaluation": summary_data.get("text_evaluation"),
                "audio_summary": summary_data.get("audio_summary"),
                "video_summary": summary_data.get("video_summary"),
                "strengths": summary_data.get("strengths"),
                "weaknesses": summary_data.get("weaknesses"),
                "red_flags": summary_data.get("red_flags"),
                "next_steps": summary_data.get("next_steps"),
                "generated_at": datetime.now(timezone.utc)
            }
            
            repo.create_or_update_summary(summary_record)
            uow.session.commit()
            
            logger.info(f"✅ Summary generated for interview {interview_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to generate summary: {str(e)}", exc_info=True)
            raise
    
    async def get_interview_status(self, interview_id: str) -> Dict[str, Any]:
        """Get current interview status"""
        try:
            uow = UnitOfWork()
            repo = OrchestrationRepository(uow)
            
            interview = repo.get_interview(interview_id)
            if not interview:
                raise ValueError(f"Interview {interview_id} not found")
            
            return {
                "interview_id": interview_id,
                "status": interview["status"],
                "current_question_number": interview["current_question_number"],
                "total_questions_asked": interview["total_questions_asked"],
                "max_questions": interview["max_questions"],
                "start_time": interview.get("start_time"),
                "end_time": interview.get("end_time"),
                "processing_status": interview.get("processing_status")
            }
            
        except Exception as e:
            logger.error(f"Failed to get interview status: {str(e)}")
            raise
    
    async def get_interview_summary(self, interview_id: str) -> Dict[str, Any]:
        """Get comprehensive interview summary"""
        try:
            uow = UnitOfWork()
            repo = OrchestrationRepository(uow)
            
            interview = repo.get_interview(interview_id)
            if not interview:
                raise ValueError(f"Interview {interview_id} not found")
            
            summary = repo.get_summary(interview_id)
            if not summary:
                raise ValueError(f"Summary not available for interview {interview_id}")
            
            candidate = repo.get_candidate(interview["candidate_id"])
            job_position = repo.get_job_position(interview["job_position_id"])
            
            sessions = repo.get_interview_sessions(interview_id)
            answered_count = len([s for s in sessions if s.get("text_answer")])
            
            return {
                "interview_id": interview_id,
                "candidate_id": interview["candidate_id"],
                "candidate_name": candidate.get("name"),
                "job_title": job_position.get("title"),
                "overall_score": summary.get("overall_score"),
                "recommendation": summary.get("recommendation"),
                "text_evaluation": summary.get("text_evaluation"),
                "audio_analysis": summary.get("audio_summary"),
                "video_analysis": summary.get("video_summary"),
                "total_questions": interview["total_questions_asked"],
                "total_answers": answered_count,
                "duration_minutes": interview.get("duration_minutes"),
                "completion_rate": (answered_count / interview["total_questions_asked"]) * 100 if interview["total_questions_asked"] > 0 else 0,
                "start_time": interview.get("start_time"),
                "end_time": interview.get("end_time"),
                "summary_generated_at": summary.get("generated_at"),
                "strengths": summary.get("strengths"),
                "weaknesses": summary.get("weaknesses"),
                "red_flags": summary.get("red_flags"),
                "next_steps": summary.get("next_steps")
            }
            
        except Exception as e:
            logger.error(f"Failed to get interview summary: {str(e)}")
            raise
    
    async def get_detailed_results(self, interview_id: str) -> Dict[str, Any]:
        """Get all detailed results from all services"""
        try:
            uow = UnitOfWork()
            repo = OrchestrationRepository(uow)
            
            interview = repo.get_interview(interview_id)
            if not interview:
                raise ValueError(f"Interview {interview_id} not found")
            
            sessions = repo.get_interview_sessions(interview_id)
            
            # Collect all analyses
            detailed_results = {
                "interview_metadata": interview,
                "sessions": sessions,
                "audio_analyses": [],
                "text_evaluations": []
            }
            
            # Get audio analyses
            for session in sessions:
                if session.get("media_file_id"):
                    try:
                        analysis = await self.audio_client.get_audio_analysis(
                            interview_id=interview_id,
                            session_id=session["id"]
                        )
                        detailed_results["audio_analyses"].append(analysis)
                    except Exception as e:
                        logger.warning(f"Could not get audio analysis: {e}")
            
            return detailed_results
            
        except Exception as e:
            logger.error(f"Failed to get detailed results: {str(e)}")
            raise
    
    async def cancel_interview(self, interview_id: str) -> Dict[str, Any]:
        """Cancel an ongoing interview"""
        try:
            uow = UnitOfWork()
            repo = OrchestrationRepository(uow)
            
            interview = repo.get_interview(interview_id)
            if not interview:
                raise ValueError(f"Interview {interview_id} not found")
            
            repo.update_interview(interview_id, {
                "status": "cancelled",
                "end_time": datetime.now(timezone.utc)
            })
            
            uow.session.commit()
            
            return {
                "interview_id": interview_id,
                "status": "cancelled"
            }
            
        except Exception as e:
            logger.error(f"Failed to cancel interview: {str(e)}")
            raise

