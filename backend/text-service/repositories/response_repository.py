"""
Repository for Response entity operations
"""

import sys
sys.path.append("/common-service")

from repository.base_repository import BaseRepository
from sqlalchemy import select
from database.models import Response
from typing import Optional, List, Dict
from datetime import datetime, timezone


class ResponseRepository(BaseRepository):
    """Repository for Response database operations"""
    
    def create(self, interview_id: str, session_id: str, responder_id: str,
               response_text: str, response_json: Optional[Dict] = None,
               latency_ms: Optional[int] = None, duration_ms: Optional[int] = None) -> Response:
        """Create a new response"""
        response = Response(
            interview_id=interview_id,
            session_id=session_id,
            responder_id=responder_id,
            response_text=response_text,
            response_json=response_json,
            latency_ms=latency_ms,
            duration_ms=duration_ms,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc)
        )
        self.session.add(response)
        self.session.commit()
        self.session.refresh(response)
        return response
    
    def get_by_id(self, response_id: str) -> Optional[Response]:
        """Get response by ID"""
        query = select(Response).where(Response.id == response_id)
        result = self.session.execute(query).scalar_one_or_none()
        return result
    
    def get_by_interview_id(self, interview_id: str) -> List[Response]:
        """Get all responses for an interview"""
        query = select(Response).where(Response.interview_id == interview_id).order_by(Response.created_at)
        result = self.session.execute(query).scalars().all()
        return list(result)

