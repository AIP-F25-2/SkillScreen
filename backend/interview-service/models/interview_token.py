"""
Interview Token Model - stores tokens for interview access
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()


class InterviewToken(Base):
    """Model for interview access tokens"""
    __tablename__ = "interview_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(String(255), unique=True, nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), nullable=False)
    candidate_name = Column(String(255), nullable=True)
    candidate_email = Column(String(255), nullable=True)
    session_id = Column(String(255), nullable=True)
    interview_id = Column(UUID(as_uuid=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<InterviewToken(token={self.token[:10]}..., candidate_id={self.candidate_id})>"

    def is_valid(self) -> bool:
        """Check if token is still valid (not expired and not used)"""
        now = datetime.now(timezone.utc)
        return self.expires_at > now and self.used_at is None

    def mark_used(self):
        """Mark token as used"""
        self.used_at = datetime.now(timezone.utc)
