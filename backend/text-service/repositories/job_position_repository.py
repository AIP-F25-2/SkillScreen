"""
Repository for JobPosition entity operations
"""

import sys
sys.path.append("/common-service")

from repository.base_repository import BaseRepository
from sqlalchemy import select
from database.models import JobPosition
from typing import Optional, List


class JobPositionRepository(BaseRepository):
    """Repository for JobPosition database operations"""
    
    def create(self, organization_id: str, title: str, description: Optional[str] = None,
               required_skills: Optional[List[str]] = None, department: Optional[str] = None,
               created_by: Optional[str] = None) -> JobPosition:
        """Create a new job position"""
        job = JobPosition(
            organization_id=organization_id,
            title=title,
            description=description,
            required_skills=required_skills or [],
            department=department,
            created_by=created_by,
            is_active=True
        )
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job
    
    def get_by_id(self, job_id: str) -> Optional[JobPosition]:
        """Get job position by ID"""
        query = select(JobPosition).where(JobPosition.id == job_id)
        result = self.session.execute(query).scalar_one_or_none()
        return result

