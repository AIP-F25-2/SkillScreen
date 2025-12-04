"""
Repository for InterviewTemplate entity operations
"""

import sys
sys.path.append("/common-service")

from repository.base_repository import BaseRepository
from sqlalchemy import select
from database.models import InterviewTemplate
from typing import Optional, List, Dict


class InterviewTemplateRepository(BaseRepository):
    """Repository for InterviewTemplate database operations"""
    
    def create(self, organization_id: str, name: str, template_type: str,
               questions: Optional[List[Dict]] = None, settings: Optional[Dict] = None,
               created_by: Optional[str] = None) -> InterviewTemplate:
        """Create a new interview template"""
        template = InterviewTemplate(
            organization_id=organization_id,
            name=name,
            type=template_type,
            questions=questions or [],
            settings=settings or {},
            created_by=created_by
        )
        self.session.add(template)
        self.session.commit()
        self.session.refresh(template)
        return template
    
    def get_by_id(self, template_id: str) -> Optional[InterviewTemplate]:
        """Get interview template by ID"""
        query = select(InterviewTemplate).where(InterviewTemplate.id == template_id)
        result = self.session.execute(query).scalar_one_or_none()
        return result

