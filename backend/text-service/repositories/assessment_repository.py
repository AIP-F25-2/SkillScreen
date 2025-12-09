"""
Repository for Assessment entity operations
"""

import sys
sys.path.append("/common-service")

from repository.base_repository import BaseRepository
from sqlalchemy import select
from database.models import Assessment
from typing import Optional, List


class AssessmentRepository(BaseRepository):
    """Repository for Assessment database operations"""
    
    def create(self, interview_id: str, overall_score: Optional[float] = None,
               hard_skills_score: Optional[float] = None, soft_skills_score: Optional[float] = None,
               communication_score: Optional[float] = None, technical_score: Optional[float] = None,
               proctoring_risk_score: Optional[float] = None, recommendation: Optional[str] = None,
               evidence_clips: Optional[List[str]] = None, summary: Optional[str] = None,
               reviewer_notes: Optional[str] = None, reviewed_by: Optional[str] = None) -> Assessment:
        """Create a new assessment"""
        assessment = Assessment(
            interview_id=interview_id,
            overall_score=overall_score,
            hard_skills_score=hard_skills_score,
            soft_skills_score=soft_skills_score,
            communication_score=communication_score,
            technical_score=technical_score,
            proctoring_risk_score=proctoring_risk_score,
            recommendation=recommendation,
            evidence_clips=evidence_clips,
            summary=summary,
            reviewer_notes=reviewer_notes,
            reviewed_by=reviewed_by
        )
        self.session.add(assessment)
        self.session.commit()
        self.session.refresh(assessment)
        return assessment
    
    def get_by_id(self, assessment_id: str) -> Optional[Assessment]:
        """Get assessment by ID"""
        query = select(Assessment).where(Assessment.id == assessment_id)
        result = self.session.execute(query).scalar_one_or_none()
        return result
    
    def get_by_interview_id(self, interview_id: str) -> Optional[Assessment]:
        """Get assessment for an interview"""
        query = select(Assessment).where(Assessment.interview_id == interview_id)
        result = self.session.execute(query).scalar_one_or_none()
        return result

