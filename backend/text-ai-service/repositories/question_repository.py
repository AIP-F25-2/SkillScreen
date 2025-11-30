import sys
sys.path.append('/common-service')

from sqlalchemy import Table, Column, String, Text, Integer, DateTime, MetaData, select, insert, update, and_
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timezone
from typing import List, Dict, Optional
from config import logger
from database import DBFactory


metadata = MetaData()

# ==========================================
# TABLE DEFINITIONS
# ==========================================

interview_sessions_table = Table(
    "interview_sessions",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("interview_id", UUID),
    Column("question_id", String),
    Column("question_text", Text),
    Column("question_type", String),  # technical, behavioral, situational, instruction
    Column("candidate_response", Text),
    Column("response_duration", Integer),  # seconds
    Column("started_at", DateTime),
    Column("completed_at", DateTime),
    Column("metadata", JSONB),
    Column("created_at", DateTime),
)

ai_analysis_table = Table(
    "ai_analysis",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("interview_id", UUID),
    Column("session_id", UUID),  # references interview_sessions
    Column("analysis_type", String),  # video, audio, text
    Column("service_name", String),  # gemini, whisper, video_analyzer, etc.
    Column("raw_results", JSONB),  # Contains evaluation_score, feedback, keywords_matched, etc.
    Column("confidence_score", String),
    Column("processing_time", Integer),
    Column("version", String),
    Column("created_at", DateTime),
)

responses_table = Table(
    "responses",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("interview_id", UUID),
    Column("session_id", UUID),  # references interview_sessions
    Column("responder_id", UUID),
    Column("response_text", Text),
    Column("response_json", JSONB),
    Column("latency_ms", Integer),
    Column("duration_ms", Integer),
    Column("started_at", DateTime),
    Column("completed_at", DateTime),
    Column("created_at", DateTime),
)


# ==========================================
# QUESTION REPOSITORY
# ==========================================

class QuestionRepository:
    """Repository for interview sessions and AI analysis operations"""

    def __init__(self, session_or_uow=None):
        """
        Initialize repository with session or UnitOfWork

        Args:
            session_or_uow: Either a SQLAlchemy Session or UnitOfWork object
        """
        if session_or_uow is None:
            self.session = DBFactory.get_session()
        elif hasattr(session_or_uow, 'session'):
            self.session = session_or_uow.session
        else:
            self.session = session_or_uow

    def create_session(self, data: Dict) -> str:
        """Create new interview session (question + metadata)"""
        if 'created_at' not in data:
            data['created_at'] = datetime.now(timezone.utc)

        # Remove updated_at if present (interview_sessions table doesn't have it)
        data.pop('updated_at', None)

        query = insert(interview_sessions_table).values(**data)
        result = self.session.execute(query)
        self.session.commit()

        session_id = result.inserted_primary_key[0]
        logger.info(f"✅ Created interview session: {session_id}")
        return str(session_id)

    def get_session_by_id(self, session_id: str) -> Optional[Dict]:
        """Get interview session by ID"""
        query = select(interview_sessions_table).where(
            interview_sessions_table.c.id == session_id
        )

        result = self.session.execute(query).fetchone()

        if result:
            return dict(result._mapping)

        return None

    def get_sessions_by_interview(self, interview_id: str) -> List[Dict]:
        """Get all sessions (questions) for an interview"""
        query = select(interview_sessions_table).where(
            interview_sessions_table.c.interview_id == interview_id
        ).order_by(interview_sessions_table.c.created_at)

        results = self.session.execute(query).fetchall()
        return [dict(row._mapping) for row in results]

    def get_next_unanswered_session(self, interview_id: str) -> Optional[Dict]:
        """Get the next session without a candidate response"""
        query = select(interview_sessions_table).where(
            and_(
                interview_sessions_table.c.interview_id == interview_id,
                interview_sessions_table.c.candidate_response == None
            )
        ).order_by(interview_sessions_table.c.created_at).limit(1)

        result = self.session.execute(query).fetchone()

        if result:
            return dict(result._mapping)

        return None

    def update_session_response(self, session_id: str, candidate_response: str, response_duration: int = None):
        """Update session with candidate response"""
        data = {
            'candidate_response': candidate_response,
            'completed_at': datetime.now(timezone.utc)
        }

        if response_duration:
            data['response_duration'] = response_duration

        query = update(interview_sessions_table).where(
            interview_sessions_table.c.id == session_id
        ).values(**data)

        self.session.execute(query)
        self.session.commit()

        logger.info(f"📝 Updated session {session_id} with response")

    def save_response(self, data: Dict) -> str:
        """Save candidate response details"""
        if 'created_at' not in data:
            data['created_at'] = datetime.now(timezone.utc)

        query = insert(responses_table).values(**data)
        result = self.session.execute(query)
        self.session.commit()

        response_id = result.inserted_primary_key[0]
        logger.info(f"💾 Saved response: {response_id}")
        return str(response_id)

    def save_analysis(self, data: Dict) -> str:
        """Save AI analysis results"""
        if 'created_at' not in data:
            data['created_at'] = datetime.now(timezone.utc)

        query = insert(ai_analysis_table).values(**data)
        result = self.session.execute(query)
        self.session.commit()

        analysis_id = result.inserted_primary_key[0]
        logger.info(f"💾 Saved analysis: {analysis_id}")
        return str(analysis_id)

    def get_analysis_by_session(self, session_id: str) -> Optional[Dict]:
        """Get AI analysis for a session"""
        query = select(ai_analysis_table).where(
            ai_analysis_table.c.session_id == session_id
        )

        result = self.session.execute(query).fetchone()

        if result:
            return dict(result._mapping)

        return None

    def get_interview_analyses(self, interview_id: str) -> List[Dict]:
        """Get all analyses for an interview"""
        query = select(ai_analysis_table).where(
            ai_analysis_table.c.interview_id == interview_id
        )

        results = self.session.execute(query).fetchall()
        return [dict(row._mapping) for row in results]
