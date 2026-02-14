"""
Repository for InterviewSession entity operations
"""

import sys
sys.path.append("/common-service")

from repository.base_repository import BaseRepository
from sqlalchemy import select
from database.models import InterviewSession
from typing import Optional, List
from datetime import datetime, timezone


class InterviewSessionRepository(BaseRepository):
    """Repository for InterviewSession database operations"""
    
    def create(self, interview_id: str, question_id: Optional[str] = None,
               question_text: Optional[str] = None, question_type: Optional[str] = None) -> InterviewSession:
        """Create a new interview session"""
        session = InterviewSession(
            interview_id=interview_id,
            question_id=question_id,
            question_text=question_text,
            question_type=question_type,
            started_at=datetime.now(timezone.utc)
        )
        self.session.add(session)
        self.session.commit()
        self.session.refresh(session)
        return session
    
    def get_by_id(self, session_id: str) -> Optional[InterviewSession]:
        """Get interview session by ID"""
        query = select(InterviewSession).where(InterviewSession.id == session_id)
        result = self.session.execute(query).scalar_one_or_none()
        return result
    
    def get_by_interview_id(self, interview_id: str) -> List[InterviewSession]:
        """Get all sessions for an interview"""
        query = select(InterviewSession).where(InterviewSession.interview_id == interview_id).order_by(InterviewSession.created_at)
        result = self.session.execute(query).scalars().all()
        return list(result)
    
    def complete(self, session_id: str, candidate_response: Optional[str] = None,
                 response_duration: Optional[int] = None) -> Optional[InterviewSession]:
        """Complete an interview session"""
        session = self.get_by_id(session_id)
        if session:
            session.candidate_response = candidate_response
            session.response_duration = response_duration
            session.completed_at = datetime.now(timezone.utc)
            self.session.commit()
            self.session.refresh(session)
        return session

