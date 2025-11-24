from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone
import uuid

Base = declarative_base()

class Candidate(Base):
    """Candidate model for interview service"""
    __tablename__ = 'candidates'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    resume_url = Column(String(500), nullable=True)
    skills = Column(JSONB, nullable=True)
    experience = Column(JSONB, nullable=True)
    education = Column(JSONB, nullable=True)
    projects = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    def to_dict(self):
        """Convert candidate to dictionary"""
        return {
            'id': str(self.id),
            'organization_id': str(self.organization_id),
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'location': self.location,
            'resume_url': self.resume_url,
            'skills': self.skills,
            'experience': self.experience,
            'education': self.education,
            'projects': self.projects,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
        }

