"""
Repository for Candidate entity operations
"""

import sys
sys.path.append("/common-service")

from repository.base_repository import BaseRepository
from sqlalchemy import select, desc
from database.models import Candidate
from typing import Optional, List, Dict


class CandidateRepository(BaseRepository):
    """Repository for Candidate database operations"""
    
    def create(self, organization_id: str, full_name: str, email: Optional[str] = None,
               phone: Optional[str] = None, location: Optional[str] = None,
               resume_url: Optional[str] = None, skills: Optional[List[str]] = None,
               experience: Optional[Dict] = None, education: Optional[Dict] = None,
               projects: Optional[List[Dict]] = None) -> Candidate:
        """Create a new candidate"""
        candidate = Candidate(
            organization_id=organization_id,
            full_name=full_name,
            email=email,
            phone=phone,
            location=location,
            resume_url=resume_url,
            skills=skills or [],
            experience=experience or {},
            education=education or {},
            projects=projects or []
        )
        self.session.add(candidate)
        self.session.commit()
        self.session.refresh(candidate)
        return candidate
    
    def get_by_id(self, candidate_id: str) -> Optional[Candidate]:
        """Get candidate by ID"""
        query = select(Candidate).where(Candidate.id == candidate_id)
        result = self.session.execute(query).scalar_one_or_none()
        return result
    
    def get_by_email(self, email: str) -> Optional[Candidate]:
        """Get candidate by email"""
        query = select(Candidate).where(Candidate.email == email)
        result = self.session.execute(query).scalar_one_or_none()
        return result
    
    def get_by_organization_id(self, organization_id: str) -> List[Candidate]:
        """Get all candidates for an organization"""
        query = select(Candidate).where(Candidate.organization_id == organization_id).order_by(desc(Candidate.created_at))
        result = self.session.execute(query).scalars().all()
        return list(result)
    
    def update(self, candidate_id: str, full_name: Optional[str] = None, # nosonar
               email: Optional[str] = None, phone: Optional[str] = None,
               location: Optional[str] = None, resume_url: Optional[str] = None,
               skills: Optional[List[str]] = None, experience: Optional[Dict] = None,
               education: Optional[Dict] = None, projects: Optional[List[Dict]] = None) -> Optional[Candidate]:
        """Update candidate information"""
        candidate = self.get_by_id(candidate_id)
        if candidate:
            if full_name is not None:
                candidate.full_name = full_name
            if email is not None:
                candidate.email = email
            if phone is not None:
                candidate.phone = phone
            if location is not None:
                candidate.location = location
            if resume_url is not None:
                candidate.resume_url = resume_url
            if skills is not None:
                candidate.skills = skills
            if experience is not None:
                candidate.experience = experience
            if education is not None:
                candidate.education = education
            if projects is not None:
                candidate.projects = projects
            
            self.session.commit()
            self.session.refresh(candidate)
        return candidate

