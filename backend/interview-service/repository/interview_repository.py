from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
import uuid
from datetime import datetime, timezone

from models.interview import Interview

class InterviewRepository:
    """Repository for interview database operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_interview(self, interview_data: Dict[str, Any]) -> Interview:
        """Create a new interview"""
        interview = Interview(
            organization_id=uuid.UUID(interview_data['organization_id']) if interview_data.get('organization_id') else None,
            job_position_id=uuid.UUID(interview_data['job_position_id']) if interview_data.get('job_position_id') else None,
            candidate_id=uuid.UUID(interview_data['candidate_id']) if interview_data.get('candidate_id') else None,
            interviewer_id=uuid.UUID(interview_data['interviewer_id']) if interview_data.get('interviewer_id') else None,
            template_id=uuid.UUID(interview_data['template_id']) if interview_data.get('template_id') else None,
            status=interview_data.get('status', 'scheduled'),
            mode=interview_data.get('mode'),
            scheduled_at=datetime.fromisoformat(interview_data['scheduled_at'].replace('Z', '+00:00')) if interview_data.get('scheduled_at') else None,
            started_at=datetime.fromisoformat(interview_data['started_at'].replace('Z', '+00:00')) if interview_data.get('started_at') else None,
            completed_at=datetime.fromisoformat(interview_data['completed_at'].replace('Z', '+00:00')) if interview_data.get('completed_at') else None,
            settings=interview_data.get('settings')
        )
        
        self.session.add(interview)
        self.session.flush()  # Get the ID without committing
        return interview
    
    def get_interview_by_id(self, interview_id: str) -> Optional[Interview]:
        """Get interview by ID"""
        return self.session.query(Interview).filter(
            and_(
                Interview.id == uuid.UUID(interview_id),
                Interview.deleted_at.is_(None)
            )
        ).first()
    
    def get_all_interviews(self, organization_id: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Interview]:
        """Get all interviews, optionally filtered by organization"""
        query = self.session.query(Interview).filter(
            Interview.deleted_at.is_(None)
        )
        
        if organization_id:
            query = query.filter(Interview.organization_id == uuid.UUID(organization_id))
        
        return query.order_by(desc(Interview.created_at)).offset(offset).limit(limit).all()
    
    def get_interviews_by_candidate(self, candidate_id: str) -> List[Interview]:
        """Get all interviews for a candidate"""
        return self.session.query(Interview).filter(
            and_(
                Interview.candidate_id == uuid.UUID(candidate_id),
                Interview.deleted_at.is_(None)
            )
        ).order_by(desc(Interview.created_at)).all()
    
    def update_interview(self, interview_id: str, update_data: Dict[str, Any]) -> Optional[Interview]:
        """Update interview information"""
        interview = self.get_interview_by_id(interview_id)
        if not interview:
            return None
        
        # Update fields
        for field, value in update_data.items():
            if hasattr(interview, field) and value is not None:
                if field in ['organization_id', 'job_position_id', 'candidate_id', 'interviewer_id', 'template_id']:
                    setattr(interview, field, uuid.UUID(value) if value else None)
                elif field in ['scheduled_at', 'started_at', 'completed_at']:
                    if isinstance(value, str):
                        setattr(interview, field, datetime.fromisoformat(value.replace('Z', '+00:00')))
                    else:
                        setattr(interview, field, value)
                else:
                    setattr(interview, field, value)
        
        interview.updated_at = datetime.now(timezone.utc)
        self.session.flush()
        return interview
    
    def update_interview_status(self, interview_id: str, status: str) -> Optional[Interview]:
        """Update interview status"""
        interview = self.get_interview_by_id(interview_id)
        if not interview:
            return None
        
        interview.status = status
        interview.updated_at = datetime.now(timezone.utc)
        
        # Set timestamps based on status
        if status == 'in_progress' and not interview.started_at:
            interview.started_at = datetime.now(timezone.utc)
        elif status == 'completed' and not interview.completed_at:
            interview.completed_at = datetime.now(timezone.utc)
        
        self.session.flush()
        return interview
    
    def soft_delete_interview(self, interview_id: str) -> bool:
        """Soft delete an interview"""
        interview = self.get_interview_by_id(interview_id)
        if not interview:
            return False
        
        interview.deleted_at = datetime.now(timezone.utc)
        self.session.flush()
        return True

