"""
Repository for AIAnalysis entity operations
"""

import sys
sys.path.append("/common-service")

from repository.base_repository import BaseRepository
from sqlalchemy import select
from database.models import AIAnalysis
from typing import Optional, List, Dict


class AIAnalysisRepository(BaseRepository):
    """Repository for AIAnalysis database operations"""
    
    def create(self, interview_id: str, session_id: Optional[str] = None,
               analysis_type: str = "text_analysis", service_name: str = "text-service",
               raw_results: Optional[Dict] = None, confidence_score: Optional[float] = None,
               processing_time: Optional[int] = None, version: str = "v1.0") -> AIAnalysis:
        """Create a new AI analysis record"""
        analysis = AIAnalysis(
            interview_id=interview_id,
            session_id=session_id,
            analysis_type=analysis_type,
            service_name=service_name,
            raw_results=raw_results,
            confidence_score=confidence_score,
            processing_time=processing_time,
            version=version
        )
        self.session.add(analysis)
        self.session.commit()
        self.session.refresh(analysis)
        return analysis
    
    def get_by_id(self, analysis_id: str) -> Optional[AIAnalysis]:
        """Get AI analysis by ID"""
        query = select(AIAnalysis).where(AIAnalysis.id == analysis_id)
        result = self.session.execute(query).scalar_one_or_none()
        return result
    
    def get_by_interview_id(self, interview_id: str) -> List[AIAnalysis]:
        """Get all AI analysis records for an interview"""
        query = select(AIAnalysis).where(AIAnalysis.interview_id == interview_id).order_by(AIAnalysis.created_at)
        result = self.session.execute(query).scalars().all()
        return list(result)
    
    def get_by_session_id(self, session_id: str) -> List[AIAnalysis]:
        """Get all AI analysis records for a session"""
        query = select(AIAnalysis).where(AIAnalysis.session_id == session_id).order_by(AIAnalysis.created_at)
        result = self.session.execute(query).scalars().all()
        return list(result)

