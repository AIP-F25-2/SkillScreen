from repository.base_repository import BaseRepository
from sqlalchemy import Table, Column, Integer, String, MetaData, select, Text, DateTime, JSON, update
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from typing import Optional, Dict

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
            .values(status=status, updated_at=datetime.utcnow())
        )
        self.session.execute(stmt)
        self.session.commit()
