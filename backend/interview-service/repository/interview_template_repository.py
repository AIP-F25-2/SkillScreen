from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
import uuid

from models.interview_template import InterviewTemplate

class InterviewTemplateRepository:
    """Repository for interview template database operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_template_by_organization(self, organization_id: str) -> Optional[InterviewTemplate]:
        """
        Get the first active interview template for an organization
        Option 3: Simple fallback - get first template for organization
        """
        return self.session.query(InterviewTemplate).filter(
            and_(
                InterviewTemplate.organization_id == uuid.UUID(organization_id),
                InterviewTemplate.deleted_at.is_(None)
            )
        ).first()

