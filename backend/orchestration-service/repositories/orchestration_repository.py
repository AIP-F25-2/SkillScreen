"""
Orchestration Repository

Database operations for orchestration service
Uses existing database tables from other services
"""

import logging
from typing import Optional, Dict, Any, List
from sqlalchemy import Table, MetaData, select, insert, update, and_
from datetime import datetime

logger = logging.getLogger(__name__)


class OrchestrationRepository:
    """Repository for orchestration database operations"""
    
    def __init__(self, uow):
        self.session = uow.session
        self.metadata = MetaData()
        
        # Define table references (assuming these exist in the database)
        # These tables should be created by the respective services
        self.interviews_table = Table('interviews', self.metadata, autoload_with=self.session.bind)
        self.interview_sessions_table = Table('interview_sessions', self.metadata, autoload_with=self.session.bind)
        self.candidates_table = Table('candidates', self.metadata, autoload_with=self.session.bind)
        self.job_positions_table = Table('job_positions', self.metadata, autoload_with=self.session.bind)
        self.interview_summaries_table = Table('interview_summaries', self.metadata, autoload_with=self.session.bind)
    
    # Interview operations
    def create_interview(self, interview_data: Dict[str, Any]) -> str:
        """Create new interview record"""
        try:
            stmt = insert(self.interviews_table).values(**interview_data)
            self.session.execute(stmt)
            return interview_data["id"]
        except Exception as e:
            logger.error(f"Failed to create interview: {str(e)}")
            raise
    
    def get_interview(self, interview_id: str) -> Optional[Dict[str, Any]]:
        """Get interview by ID"""
        try:
            stmt = select(self.interviews_table).where(
                self.interviews_table.c.id == interview_id
            )
            result = self.session.execute(stmt).fetchone()
            return dict(result._mapping) if result else None
        except Exception as e:
            logger.error(f"Failed to get interview: {str(e)}")
            return None
    
    def update_interview(self, interview_id: str, update_data: Dict[str, Any]) -> bool:
        """Update interview record"""
        try:
            stmt = update(self.interviews_table).where(
                self.interviews_table.c.id == interview_id
            ).values(**update_data)
            self.session.execute(stmt)
            return True
        except Exception as e:
            logger.error(f"Failed to update interview: {str(e)}")
            raise
    
    # Session operations
    def create_session(self, session_data: Dict[str, Any]) -> str:
        """Create new interview session (question)"""
        try:
            stmt = insert(self.interview_sessions_table).values(**session_data)
            self.session.execute(stmt)
            return session_data["id"]
        except Exception as e:
            logger.error(f"Failed to create session: {str(e)}")
            raise
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID"""
        try:
            stmt = select(self.interview_sessions_table).where(
                self.interview_sessions_table.c.id == session_id
            )
            result = self.session.execute(stmt).fetchone()
            return dict(result._mapping) if result else None
        except Exception as e:
            logger.error(f"Failed to get session: {str(e)}")
            return None
    
    def update_session(self, session_id: str, update_data: Dict[str, Any]) -> bool:
        """Update session record"""
        try:
            stmt = update(self.interview_sessions_table).where(
                self.interview_sessions_table.c.id == session_id
            ).values(**update_data)
            self.session.execute(stmt)
            return True
        except Exception as e:
            logger.error(f"Failed to update session: {str(e)}")
            raise
    
    def get_interview_sessions(self, interview_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for an interview"""
        try:
            stmt = select(self.interview_sessions_table).where(
                self.interview_sessions_table.c.interview_id == interview_id
            ).order_by(self.interview_sessions_table.c.question_number)
            
            results = self.session.execute(stmt).fetchall()
            return [dict(row._mapping) for row in results]
        except Exception as e:
            logger.error(f"Failed to get interview sessions: {str(e)}")
            return []
    
    # Candidate operations
    def get_candidate(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        """Get candidate by ID"""
        try:
            stmt = select(self.candidates_table).where(
                self.candidates_table.c.id == candidate_id
            )
            result = self.session.execute(stmt).fetchone()
            return dict(result._mapping) if result else None
        except Exception as e:
            logger.error(f"Failed to get candidate: {str(e)}")
            return None
    
    # Job position operations
    def get_job_position(self, job_position_id: str) -> Optional[Dict[str, Any]]:
        """Get job position by ID"""
        try:
            stmt = select(self.job_positions_table).where(
                self.job_positions_table.c.id == job_position_id
            )
            result = self.session.execute(stmt).fetchone()
            return dict(result._mapping) if result else None
        except Exception as e:
            logger.error(f"Failed to get job position: {str(e)}")
            return None
    
    # Summary operations
    def create_or_update_summary(self, summary_data: Dict[str, Any]) -> str:
        """Create or update interview summary"""
        try:
            # Check if summary exists
            stmt = select(self.interview_summaries_table).where(
                self.interview_summaries_table.c.interview_id == summary_data["interview_id"]
            )
            existing = self.session.execute(stmt).fetchone()
            
            if existing:
                # Update
                stmt = update(self.interview_summaries_table).where(
                    self.interview_summaries_table.c.interview_id == summary_data["interview_id"]
                ).values(**summary_data)
                self.session.execute(stmt)
                return summary_data["interview_id"]
            else:
                # Create
                stmt = insert(self.interview_summaries_table).values(**summary_data)
                self.session.execute(stmt)
                return summary_data["interview_id"]
                
        except Exception as e:
            logger.error(f"Failed to create/update summary: {str(e)}")
            raise
    
    def get_summary(self, interview_id: str) -> Optional[Dict[str, Any]]:
        """Get interview summary"""
        try:
            stmt = select(self.interview_summaries_table).where(
                self.interview_summaries_table.c.interview_id == interview_id
            )
            result = self.session.execute(stmt).fetchone()
            return dict(result._mapping) if result else None
        except Exception as e:
            logger.error(f"Failed to get summary: {str(e)}")
            return None

