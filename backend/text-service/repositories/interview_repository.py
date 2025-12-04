"""
Repository for Interview entity operations
"""

import sys
sys.path.append("/common-service")

from repository.base_repository import BaseRepository
from sqlalchemy import select, desc
from database.models import Interview, InterviewStatus, InterviewMode
from typing import Optional, List
from datetime import datetime, timezone


class InterviewRepository(BaseRepository):
    """Repository for Interview database operations"""
    
    def create(self, organization_id: str, job_position_id: str, template_id: str,
               candidate_id: Optional[str] = None, interviewer_id: Optional[str] = None,
               mode: InterviewMode = InterviewMode.CHAT, scheduled_at: Optional[datetime] = None) -> Interview:
        """Create a new interview"""
        interview = Interview(
            organization_id=organization_id,
            job_position_id=job_position_id,
            template_id=template_id,
            candidate_id=candidate_id,
            interviewer_id=interviewer_id,
            status=InterviewStatus.SCHEDULED,
            mode=mode,
            scheduled_at=scheduled_at
        )
        self.session.add(interview)
        self.session.commit()
        self.session.refresh(interview)
        return interview
    
    def get_by_id(self, interview_id: str) -> Optional[Interview]:
        """Get interview by ID"""
        query = select(Interview).where(Interview.id == interview_id)
        result = self.session.execute(query).scalar_one_or_none()
        return result
    
    def get_by_candidate_id(self, candidate_id: str) -> List[Interview]:
        """Get all interviews for a candidate"""
        query = select(Interview).where(Interview.candidate_id == candidate_id).order_by(desc(Interview.created_at))
        result = self.session.execute(query).scalars().all()
        return list(result)
    
    def start(self, interview_id: str) -> Optional[Interview]:
        """Start an interview"""
        interview = self.get_by_id(interview_id)
        if interview:
            interview.status = InterviewStatus.IN_PROGRESS
            interview.started_at = datetime.now(timezone.utc)
            self.session.commit()
            self.session.refresh(interview)
        return interview
    
    def complete(self, interview_id: str) -> Optional[Interview]:
        """Complete an interview"""
        interview = self.get_by_id(interview_id)
        if interview:
            interview.status = InterviewStatus.COMPLETED
            interview.completed_at = datetime.now(timezone.utc)
            self.session.commit()
            self.session.refresh(interview)
        return interview

