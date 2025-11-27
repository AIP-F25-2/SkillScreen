from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import uuid
from datetime import datetime, timezone

from models.job_position import JobPosition

class JobPositionRepository:
    """Repository for job position database operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_job_position(self, job_position_data: Dict[str, Any]) -> JobPosition:
        """Create a new job position"""
        job_position = JobPosition(
            organization_id=uuid.UUID(job_position_data['organization_id']),
            title=job_position_data['title'],
            description=job_position_data.get('description'),
            required_skills=job_position_data.get('required_skills'),
            department=job_position_data.get('department'),
            is_active=job_position_data.get('is_active', True),
            created_by=uuid.UUID(job_position_data['created_by']) if job_position_data.get('created_by') else None
        )
        
        self.session.add(job_position)
        self.session.flush()  # Get the ID without committing
        return job_position
    
    def get_job_position_by_id(self, job_position_id: str) -> Optional[JobPosition]:
        """Get job position by ID"""
        return self.session.query(JobPosition).filter(
            and_(
                JobPosition.id == uuid.UUID(job_position_id),
                JobPosition.deleted_at.is_(None)
            )
        ).first()
    
    def get_job_positions_by_organization(
        self, 
        organization_id: str, 
        limit: int = 100, 
        offset: int = 0,
        is_active: Optional[bool] = None
    ) -> List[JobPosition]:
        """Get all job positions for an organization with optional filters"""
        query = self.session.query(JobPosition).filter(
            and_(
                JobPosition.organization_id == uuid.UUID(organization_id),
                JobPosition.deleted_at.is_(None)
            )
        )
        
        if is_active is not None:
            query = query.filter(JobPosition.is_active == is_active)
        
        return query.order_by(JobPosition.created_at.desc()).offset(offset).limit(limit).all()
    
    def count_job_positions_by_organization(
        self,
        organization_id: str,
        is_active: Optional[bool] = None
    ) -> int:
        """Count job positions for an organization"""
        query = self.session.query(JobPosition).filter(
            and_(
                JobPosition.organization_id == uuid.UUID(organization_id),
                JobPosition.deleted_at.is_(None)
            )
        )
        
        if is_active is not None:
            query = query.filter(JobPosition.is_active == is_active)
        
        return query.count()
    
    def get_all_job_positions(
        self,
        limit: int = 100,
        offset: int = 0,
        is_active: Optional[bool] = True
    ) -> List[JobPosition]:
        """Get all job positions across all organizations"""
        query = self.session.query(JobPosition).filter(
            JobPosition.deleted_at.is_(None)
        )
        
        if is_active is not None:
            query = query.filter(JobPosition.is_active == is_active)
        
        return query.order_by(JobPosition.created_at.desc()).offset(offset).limit(limit).all()
    
    def count_all_job_positions(self, is_active: Optional[bool] = True) -> int:
        """Count all job positions across all organizations"""
        query = self.session.query(JobPosition).filter(
            JobPosition.deleted_at.is_(None)
        )
        
        if is_active is not None:
            query = query.filter(JobPosition.is_active == is_active)
        
        return query.count()
    
    def update_job_position(self, job_position_id: str, update_data: Dict[str, Any]) -> Optional[JobPosition]:
        """Update job position information"""
        job_position = self.get_job_position_by_id(job_position_id)
        if not job_position:
            return None
        
        # Update fields
        for field, value in update_data.items():
            if hasattr(job_position, field) and value is not None:
                setattr(job_position, field, value)
        
        job_position.updated_at = datetime.now(timezone.utc)
        self.session.flush()
        return job_position
    
    def soft_delete_job_position(self, job_position_id: str) -> bool:
        """Soft delete a job position"""
        job_position = self.get_job_position_by_id(job_position_id)
        if not job_position:
            return False
        
        job_position.deleted_at = datetime.now(timezone.utc)
        self.session.flush()
        return True


