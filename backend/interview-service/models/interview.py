"""
Interview model for interview service
"""
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone
import uuid

Base = declarative_base()

class Interview(Base):
    """Interview database model"""
    __tablename__ = 'interviews'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=True)
    job_position_id = Column(UUID(as_uuid=True), nullable=True)
    candidate_id = Column(UUID(as_uuid=True), nullable=True)
    interviewer_id = Column(UUID(as_uuid=True), nullable=True)
    template_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(50), default='scheduled')  # scheduled, in_progress, completed, cancelled
    mode = Column(String(50), nullable=True)  # video, audio, text
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    settings = Column(JSONB, nullable=True)  # Interview settings/config
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'interview_id': str(self.id),  # Alias for compatibility
            'organization_id': str(self.organization_id) if self.organization_id else None,
            'job_position_id': str(self.job_position_id) if self.job_position_id else None,
            'candidate_id': str(self.candidate_id) if self.candidate_id else None,
            'interviewer_id': str(self.interviewer_id) if self.interviewer_id else None,
            'template_id': str(self.template_id) if self.template_id else None,
            'status': self.status,
            'mode': self.mode,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'settings': self.settings,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
        }

