from repository.base_repository import BaseRepository
from sqlalchemy import Table, Column, Integer, String, MetaData, select, Text, DateTime, JSON, update, insert
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timezone
from typing import Optional, Dict
import uuid

metadata = MetaData()

users_table = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String),
)

# Candidates table structure
candidates_table = Table(
    "candidates",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("organization_id", UUID),
    Column("full_name", String),
    Column("email", String),
    Column("phone", String),
    Column("resume_url", Text),
    Column("skills", JSON),
    Column("experience", JSON),
    Column("education", JSON),
    Column("projects", JSON),
    Column("created_at", DateTime),
    Column("updated_at", DateTime),
)

# Interviews table structure
interviews_table = Table(
    "interviews",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("organization_id", UUID),
    Column("candidate_id", UUID),
    Column("job_position_id", UUID),
    Column("template_id", UUID),
    Column("status", String),
    Column("mode", String),
    Column("scheduled_at", DateTime),
    Column("started_at", DateTime),
    Column("completed_at", DateTime),
    Column("settings", JSON),
    Column("created_at", DateTime),
    Column("updated_at", DateTime),
)

# Interview Sessions table structure
interview_sessions_table = Table(
    "interview_sessions",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("interview_id", UUID),
    Column("question_id", String),
    Column("question_text", Text),
    Column("question_type", String),
    Column("candidate_response", Text),
    Column("response_duration", Integer),
    Column("started_at", DateTime),
    Column("completed_at", DateTime),
    Column("metadata", JSONB),
    Column("created_at", DateTime),
)

class OrchestrationRepository(BaseRepository):

    def get_all_users(self):
        query = select(users_table)
        result = self.session.execute(query)
        users = result.mappings().all()
        return users

    def get_user_by_id(self, user_id: int):
        query = select(users_table).where(users_table.c.id == user_id)
        result = self.session.execute(query).fetchone()
        return dict(result) if result else None
    
    def get_candidate_by_id(self, candidate_id: str) -> Optional[Dict]:
        """Get candidate data by ID"""
        query = select(candidates_table).where(candidates_table.c.id == candidate_id)
        result = self.session.execute(query).fetchone()
        if result:
            return dict(result._mapping)
        return None
    
    def get_interview_by_id(self, interview_id: str) -> Optional[Dict]:
        """Get interview data by ID"""
        query = select(interviews_table).where(interviews_table.c.id == interview_id)
        result = self.session.execute(query).fetchone()
        if result:
            return dict(result._mapping)
        return None
    
    def get_interview_by_token(self, token: str) -> Optional[Dict]:
        """Get interview by token from settings JSON"""
        query = select(interviews_table)
        result = self.session.execute(query)
        
        for row in result:
            interview = dict(row._mapping)
            settings = interview.get("settings") or {}
            if isinstance(settings, dict) and settings.get("token") == token:
                return interview
        return None
    
    def update_interview_status(self, interview_id: str, status: str):
        """Update interview status"""
        stmt = (
            update(interviews_table)
            .where(interviews_table.c.id == interview_id)
            .values(status=status, updated_at=datetime.now(timezone.utc))
        )
        self.session.execute(stmt)
        self.session.commit()
    
    def create_interview_session(
        self,
        interview_id: str,
        question_id: str,
        question_text: str,
        question_type: str = "general",
        metadata: Optional[Dict] = None
    ) -> str:
        """Create a new interview session record"""
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        stmt = insert(interview_sessions_table).values(
            id=session_id,
            interview_id=interview_id,
            question_id=question_id,
            question_text=question_text,
            question_type=question_type,
            candidate_response=None,
            response_duration=None,
            started_at=now,
            completed_at=None,
            metadata=metadata,
            created_at=now
        )
        self.session.execute(stmt)
        self.session.commit()
        return session_id
    
    def update_interview_session_response(
        self,
        session_id: str,
        candidate_response: str,
        response_duration: Optional[int] = None
    ):
        """Update interview session with candidate response"""
        now = datetime.now(timezone.utc)
        
        stmt = (
            update(interview_sessions_table)
            .where(interview_sessions_table.c.id == session_id)
            .values(
                candidate_response=candidate_response,
                response_duration=response_duration,
                completed_at=now
            )
        )
        self.session.execute(stmt)
        self.session.commit()
    
    def get_latest_interview_session(self, interview_id: str) -> Optional[Dict]:
        """Get the most recent interview session for an interview"""
        query = (
            select(interview_sessions_table)
            .where(interview_sessions_table.c.interview_id == interview_id)
            .order_by(interview_sessions_table.c.created_at.desc())
            .limit(1)
        )
        result = self.session.execute(query).fetchone()
        if result:
            return dict(result._mapping)
        return None
    
    def get_media_file_by_interview_id(self, interview_id: str) -> Optional[Dict]:
        """Get media file (video) by interview_id from media_files table"""
        # Query media_files table directly
        from sqlalchemy import text
        
        query = text("""
            SELECT id, interview_id, session_id, file_type, storage_uri, 
                   file_size, status, created_at, updated_at
            FROM media_files
            WHERE interview_id = CAST(:interview_id AS uuid)
              AND file_type = 'video'
              AND status = 'completed'
            ORDER BY created_at DESC
            LIMIT 1
        """)
        
        result = self.session.execute(query, {"interview_id": interview_id}).fetchone()
        if result:
            return dict(result._mapping)
        return None
