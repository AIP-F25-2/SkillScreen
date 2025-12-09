"""
Repository for Score entity operations
"""

import sys
sys.path.append("/common-service")

from repository.base_repository import BaseRepository
from sqlalchemy import select
from database.models import Score
from typing import Optional, List, Dict


class ScoreRepository(BaseRepository):
    """Repository for Score database operations"""
    
    def create(self, interview_id: str, response_id: str, dimension: str,
               auto_score: Optional[float] = None, human_override_score: Optional[float] = None,
               rubric: Optional[Dict] = None, evidence_refs: Optional[List[str]] = None,
               notes: Optional[str] = None, created_by: Optional[str] = None) -> Score:
        """Create a new score"""
        score = Score(
            interview_id=interview_id,
            response_id=response_id,
            dimension=dimension,
            auto_score=auto_score,
            human_override_score=human_override_score,
            rubric=rubric,
            evidence_refs=evidence_refs,
            notes=notes,
            created_by=created_by
        )
        self.session.add(score)
        self.session.commit()
        self.session.refresh(score)
        return score
    
    def get_by_id(self, score_id: str) -> Optional[Score]:
        """Get score by ID"""
        query = select(Score).where(Score.id == score_id)
        result = self.session.execute(query).scalar_one_or_none()
        return result
    
    def get_by_interview_id(self, interview_id: str) -> List[Score]:
        """Get all scores for an interview"""
        query = select(Score).where(Score.interview_id == interview_id)
        result = self.session.execute(query).scalars().all()
        return list(result)

