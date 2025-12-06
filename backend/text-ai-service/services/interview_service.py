import uuid
import json
from typing import Dict, Optional, List
from config import logger, settings
from repositories import InterviewRepository, QuestionRepository
from database import DBFactory, UnitOfWork


class InterviewService:
    """Service for interview management"""

    def __init__(self):
        self.interview_repo = InterviewRepository()
        self.question_repo = QuestionRepository()

    def get_interview(self, interview_id: str) -> Dict:
        """Get interview details"""
        try:
            interview = self.interview_repo.get_interview_by_id(interview_id)

            if not interview:
                return {
                    "success": False,
                    "error": f"Interview not found: {interview_id}"
                }

            return {
                "success": True,
                "data": interview
            }

        except Exception as e:
            logger.error(f"❌ Error getting interview: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_interview_with_questions(self, interview_id: str) -> Dict:
        """Get interview details with all sessions (questions)"""
        try:
            interview = self.interview_repo.get_interview_by_id(interview_id)

            if not interview:
                return {
                    "success": False,
                    "error": f"Interview not found: {interview_id}"
                }

            sessions = self.question_repo.get_sessions_by_interview(interview_id)

            return {
                "success": True,
                "data": {
                    "interview": interview,
                    "sessions": sessions,
                    "total_sessions": len(sessions)
                }
            }

        except Exception as e:
            logger.error(f"❌ Error getting interview with sessions: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def start_interview(self, interview_id: str, candidate_id: str) -> Dict:
        """Start an interview (transition from scheduled to in_progress)"""
        try:
            interview = self.interview_repo.get_interview_by_id(interview_id)

            if not interview:
                return {
                    "success": False,
                    "error": f"Interview not found: {interview_id}"
                }

            if interview.get("status") != "scheduled":
                return {
                    "success": False,
                    "error": f"Interview is in {interview['status']} status, cannot start"
                }

            # Update interview status
            self.interview_repo.update_interview_status(interview_id, "in_progress")

            # Get first unanswered session
            first_session = self.question_repo.get_next_unanswered_session(interview_id)

            if not first_session:
                return {
                    "success": False,
                    "error": "No questions available for this interview"
                }

            logger.info(f"✅ Interview {interview_id} started")

            return {
                "success": True,
                "data": {
                    "interview_id": interview_id,
                    "status": "in_progress",
                    "current_session": first_session,
                    "message": "Interview started successfully"
                }
            }

        except Exception as e:
            logger.error(f"❌ Error starting interview: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def update_interview_status(self, interview_id: str, status: str) -> Dict:
        """Update interview status"""
        try:
            interview = self.interview_repo.get_interview_by_id(interview_id)

            if not interview:
                return {
                    "success": False,
                    "error": f"Interview not found: {interview_id}"
                }

            self.interview_repo.update_interview_status(interview_id, status)

            return {
                "success": True,
                "data": {
                    "interview_id": interview_id,
                    "status": status
                }
            }

        except Exception as e:
            logger.error(f"❌ Error updating interview status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_next_question(self, interview_id: str, candidate_id: str = None, job_position_id: str = None, previous_response: str = None) -> Dict:
        """Get next question - generate dynamically if needed"""
        try:
            interview = self.interview_repo.get_interview_by_id(interview_id)

            if not interview:
                return {
                    "success": False,
                    "error": f"Interview not found: {interview_id}"
                }

            # Check if there's an unanswered session
            next_session = self.question_repo.get_next_unanswered_session(interview_id)

            if next_session:
                # Session already exists, return it
                return {
                    "success": True,
                    "data": next_session
                }

            # No unanswered session - check if interview is complete
            all_sessions = self.question_repo.get_sessions_by_interview(interview_id)
            total_questions = interview.get("settings", {}).get("num_questions", 5)

            if len(all_sessions) >= total_questions:
                # Mark interview as completed
                logger.info(f"⛔ All questions answered - interview complete ({len(all_sessions)}/{total_questions})")
                self.interview_repo.update_interview_status(interview_id, "completed")
                return {
                    "success": False,
                    "error": f"Interview completed - all {total_questions} questions answered",
                    "completed": True,  # Signal completion to the endpoint
                    "questions_asked": len(all_sessions),
                    "max_questions": total_questions
                }

            # Extract previous response from the most recently answered session if not provided
            if not previous_response and all_sessions:
                for session in reversed(all_sessions):
                    if session.get("candidate_response"):
                        previous_response = session.get("candidate_response")
                        break

            # Generate next question dynamically
            if not candidate_id or not job_position_id:
                return {
                    "success": False,
                    "error": "candidate_id and job_position_id required to generate next question"
                }

            from services import QuestionGenerationService
            question_service = QuestionGenerationService()

            result = question_service.generate_next_question(
                interview_id=interview_id,
                candidate_id=candidate_id,
                job_position_id=job_position_id,
                previous_response=previous_response
            )

            # If generation indicates completion, pass it through
            if not result.get("success") and result.get("completed"):
                logger.info(f"⛔ Interview completion detected - passing through completion signal")
                return result  # Pass through the completed flag

            if not result.get("success"):
                return result

            return {
                "success": True,
                "data": result.get("data")
            }

        except Exception as e:
            logger.error(f"❌ Error getting next session: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_candidates_interviews(self, candidate_id: str) -> Dict:
        """Get all interviews for a candidate"""
        try:
            interviews = self.interview_repo.get_interviews_by_candidate(candidate_id)

            return {
                "success": True,
                "data": {
                    "interviews": interviews,
                    "total_count": len(interviews)
                }
            }

        except Exception as e:
            logger.error(f"❌ Error getting candidate interviews: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
