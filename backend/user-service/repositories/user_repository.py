from repository.base_repository import BaseRepository
from sqlalchemy import (
    Table, Column, String, Boolean, DateTime, MetaData, ForeignKey, select
)
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone

metadata = MetaData()

users_table = Table(
    "users",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("organization_id", UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False),
    Column("email", String, nullable=False),
    Column("password_hash", String),
    Column("first_name", String),
    Column("last_name", String),
    Column("role", String, nullable=False),
    Column("is_active", Boolean, default=True),
    Column("profile_data", String),
    Column("created_at", DateTime, default=lambda: datetime.now(timezone.utc)),
    Column("updated_at", DateTime, default=lambda: datetime.now(timezone.utc)),
    Column("deleted_at", DateTime),
)


class UserRepository(BaseRepository):

    # CREATE
    def create_user(self, data: dict):
        query = users_table.insert().values(**data).returning(users_table.c.id)
        result = self.session.execute(query)
        return result.scalar()

    # READ ALL
    def get_all_users(self):
        query = (
            select(users_table)
            .where(users_table.c.deleted_at.is_(None))
            .order_by(users_table.c.created_at.desc())
        )
        result = self.session.execute(query).mappings().all()
        return result

    # READ BY ID
    def get_user_by_id(self, user_id):
        query = (
            select(users_table)
            .where(
                users_table.c.id == user_id,
                users_table.c.deleted_at.is_(None),
            )
        )
        result = self.session.execute(query).mappings().fetchone()
        return dict(result) if result else None

    # READ BY EMAIL
    def get_user_by_email(self, email: str):
        query = (
            select(users_table)
            .where(
                users_table.c.email == email,
                users_table.c.deleted_at.is_(None),
            )
        )
        result = self.session.execute(query).mappings().fetchone()
        return dict(result) if result else None

    # UPDATE
    def update_user(self, user_id, updates: dict):
        updates["updated_at"] = datetime.now(timezone.utc)

        query = (
            users_table.update()
            .where(
                users_table.c.id == user_id,
                users_table.c.deleted_at.is_(None),
            )
            .values(**updates)
            .returning(users_table)
        )
        result = self.session.execute(query).mappings().fetchone()
        return dict(result) if result else None

    # SOFT DELETE
    def delete_user(self, user_id):
        query = (
            users_table.update()
            .where(
                users_table.c.id == user_id,
                users_table.c.deleted_at.is_(None),
            )
            .values(
                is_active=False,
                deleted_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            .returning(users_table.c.id)
        )
        result = self.session.execute(query).scalar()
        return result
