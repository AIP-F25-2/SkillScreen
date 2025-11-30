import sys
sys.path.append('/common-service')

from sqlalchemy import Table, Column, String, Integer, DateTime, MetaData, select, insert, update, and_
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timezone
from typing import List, Dict, Optional
from config import logger
from database import DBFactory


metadata = MetaData()

# ==========================================
# TABLE DEFINITIONS
# ==========================================

interviews_table = Table(
    "interviews",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("organization_id", UUID),
    Column("job_position_id", UUID),
    Column("candidate_id", UUID),
    Column("interviewer_id", UUID),
    Column("template_id", UUID),
    Column("status", String),  # scheduled, in_progress, completed, cancelled
    Column("mode", String),
    Column("scheduled_at", DateTime),
    Column("started_at", DateTime),
    Column("completed_at", DateTime),
    Column("settings", JSONB),
    Column("created_at", DateTime),
    Column("updated_at", DateTime),
    Column("deleted_at", DateTime),
)

candidates_table = Table(
    "candidates",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("organization_id", UUID),
    Column("full_name", String),
    Column("email", String),
    Column("phone", String),
    Column("location", String),
    Column("resume_url", String),
    Column("skills", JSONB),
    Column("experience", JSONB),
    Column("education", JSONB),
    Column("projects", JSONB),
    Column("created_at", DateTime),
    Column("updated_at", DateTime),
    Column("deleted_at", DateTime),
)

job_positions_table = Table(
    "job_positions",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("organization_id", UUID),
    Column("title", String),
    Column("description", String),
    Column("required_skills", JSONB),
    Column("department", String),
    Column("is_active", String),
    Column("created_by", UUID),
    Column("created_at", DateTime),
    Column("updated_at", DateTime),
    Column("deleted_at", DateTime),
)

interview_responses_table = Table(
    "interview_responses",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("interview_id", UUID),
    Column("question_id", UUID),
    Column("question_text", String),
    Column("response_text", String),
    Column("response_audio_url", String),
    Column("duration_seconds", Integer),
    Column("confidence_score", String),
    Column("created_at", DateTime),
)

scores_table = Table(
    "scores",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("interview_id", UUID),
    Column("candidate_id", UUID),
    Column("technical_score", String),
    Column("communication_score", String),
    Column("problem_solving_score", String),
    Column("overall_score", String),
    Column("feedback", String),
    Column("recommendations", JSONB),
    Column("created_at", DateTime),
)


# ==========================================
# INTERVIEW REPOSITORY
# ==========================================

class InterviewRepository:
    """Repository for interview database operations"""

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

    def create_interview(self, data: Dict) -> str:
        """Create new interview"""
        if 'created_at' not in data:
            data['created_at'] = datetime.now(timezone.utc)
        if 'updated_at' not in data:
            data['updated_at'] = datetime.now(timezone.utc)

        query = insert(interviews_table).values(**data)
        result = self.session.execute(query)
        self.session.commit()

        interview_id = result.inserted_primary_key[0]
        logger.info(f"✅ Created interview: {interview_id}")
        return str(interview_id)

    def get_interview_by_id(self, interview_id: str) -> Optional[Dict]:
        """Get interview by ID"""
        query = select(interviews_table).where(
            interviews_table.c.id == interview_id
        )

        result = self.session.execute(query).fetchone()

        if result:
            return dict(result._mapping)

        logger.warning(f"⚠️ Interview not found: {interview_id}")
        return None

    def get_interview_by_candidate_and_status(
        self,
        candidate_id: str,
        status: str = "scheduled"
    ) -> Optional[Dict]:
        """Get interview by candidate and status"""
        query = select(interviews_table).where(
            and_(
                interviews_table.c.candidate_id == candidate_id,
                interviews_table.c.status == status
            )
        )

        result = self.session.execute(query).fetchone()

        if result:
            return dict(result._mapping)

        return None

    def update_interview_status(self, interview_id: str, status: str):
        """Update interview status"""
        query = update(interviews_table).where(
            interviews_table.c.id == interview_id
        ).values(
            status=status,
            updated_at=datetime.now(timezone.utc)
        )

        self.session.execute(query)
        self.session.commit()

        logger.info(f"📝 Updated interview {interview_id} status to: {status}")

    def update_interview(self, interview_id: str, data: Dict):
        """Update interview with multiple fields"""
        data['updated_at'] = datetime.now(timezone.utc)

        query = update(interviews_table).where(
            interviews_table.c.id == interview_id
        ).values(**data)

        self.session.execute(query)
        self.session.commit()

        logger.info(f"📝 Updated interview: {interview_id}")

    def get_interviews_by_candidate(self, candidate_id: str) -> List[Dict]:
        """Get all interviews for a candidate"""
        query = select(interviews_table).where(
            interviews_table.c.candidate_id == candidate_id
        )

        results = self.session.execute(query).fetchall()
        return [dict(row._mapping) for row in results]

    def get_interviews_by_job(self, job_position_id: str) -> List[Dict]:
        """Get all interviews for a job position"""
        query = select(interviews_table).where(
            interviews_table.c.job_position_id == job_position_id
        )

        results = self.session.execute(query).fetchall()
        return [dict(row._mapping) for row in results]

    def get_candidate_by_id(self, candidate_id: str) -> Optional[Dict]:
        """Get candidate by ID"""
        query = select(candidates_table).where(
            candidates_table.c.id == candidate_id
        )

        result = self.session.execute(query).fetchone()

        if result:
            return dict(result._mapping)

        return None

    def get_job_position_by_id(self, job_position_id: str) -> Optional[Dict]:
        """Get job position by ID"""
        query = select(job_positions_table).where(
            job_positions_table.c.id == job_position_id
        )

        result = self.session.execute(query).fetchone()

        if result:
            return dict(result._mapping)

        return None
