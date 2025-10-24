from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
import uuid
from datetime import datetime, timezone

from models.candidate import Candidate

class CandidateRepository:
    """Repository for candidate database operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_candidate(self, candidate_data: Dict[str, Any]) -> Candidate:
        """Create a new candidate"""
        candidate = Candidate(
            organization_id=candidate_data['organization_id'],
            full_name=candidate_data['full_name'],
            email=candidate_data['email'],
            phone=candidate_data.get('phone'),
            location=candidate_data.get('location'),
            resume_url=candidate_data.get('resume_url'),
            skills=candidate_data.get('skills'),
            experience=candidate_data.get('experience'),
            education=candidate_data.get('education'),
            projects=candidate_data.get('projects')
        )
        
        self.session.add(candidate)
        self.session.flush()  # Get the ID without committing
        return candidate
    
    def get_candidate_by_id(self, candidate_id: str) -> Optional[Candidate]:
        """Get candidate by ID"""
        return self.session.query(Candidate).filter(
            and_(
                Candidate.id == uuid.UUID(candidate_id),
                Candidate.deleted_at.is_(None)
            )
        ).first()
    
    def get_candidate_by_email(self, organization_id: str, email: str) -> Optional[Candidate]:
        """Get candidate by email within organization"""
        return self.session.query(Candidate).filter(
            and_(
                Candidate.organization_id == organization_id,
                Candidate.email == email,
                Candidate.deleted_at.is_(None)
            )
        ).first()
    
    def get_candidates_by_organization(self, organization_id: str, limit: int = 100, offset: int = 0) -> List[Candidate]:
        """Get all candidates for an organization"""
        return self.session.query(Candidate).filter(
            and_(
                Candidate.organization_id == organization_id,
                Candidate.deleted_at.is_(None)
            )
        ).offset(offset).limit(limit).all()
    
    def update_candidate(self, candidate_id: str, update_data: Dict[str, Any]) -> Optional[Candidate]:
        """Update candidate information"""
        candidate = self.get_candidate_by_id(candidate_id)
        if not candidate:
            return None
        
        # Update fields
        for field, value in update_data.items():
            if hasattr(candidate, field):
                setattr(candidate, field, value)
        
        candidate.updated_at = datetime.now(timezone.utc)
        self.session.flush()
        return candidate
    
    def soft_delete_candidate(self, candidate_id: str) -> bool:
        """Soft delete a candidate"""
        candidate = self.get_candidate_by_id(candidate_id)
        if not candidate:
            return False
        
        candidate.deleted_at = datetime.now(timezone.utc)
        self.session.flush()
        return True
    
    def search_candidates(self, organization_id: str, search_term: str, limit: int = 50) -> List[Candidate]:
        """Search candidates by name or email"""
        search_pattern = f"%{search_term}%"
        return self.session.query(Candidate).filter(
            and_(
                Candidate.organization_id == organization_id,
                Candidate.deleted_at.is_(None),
                (Candidate.full_name.ilike(search_pattern) | 
                 Candidate.email.ilike(search_pattern))
            )
        ).limit(limit).all()
    
    def candidate_exists(self, organization_id: str, email: str) -> bool:
        """Check if candidate already exists"""
        candidate = self.get_candidate_by_email(organization_id, email)
        return candidate is not None
