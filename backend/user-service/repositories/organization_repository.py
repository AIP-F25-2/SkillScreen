from repository.base_repository import BaseRepository
from sqlalchemy import (
    Table, Column, String, DateTime, MetaData, select
)
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

metadata = MetaData()

organizations_table = Table(
    "organizations",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("name", String, nullable=False),
    Column("domain", String),
    Column("settings", String),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow),
    Column("deleted_at", DateTime),
)


class OrganizationRepository(BaseRepository):

    def create(self, data: dict):
        query = organizations_table.insert().values(**data).returning(organizations_table.c.id)
        result = self.session.execute(query)
        self.session.commit()
        return result.scalar()

    def get_all(self):
        query = (
            select(organizations_table)
            .where(organizations_table.c.deleted_at.is_(None))
            .order_by(organizations_table.c.created_at.desc())
        )
        return self.session.execute(query).mappings().all()

    def get_by_id(self, org_id):
        query = (
            select(organizations_table)
            .where(
                organizations_table.c.id == org_id,
                organizations_table.c.deleted_at.is_(None)
            )
        )
        result = self.session.execute(query).fetchone()
        return dict(result) if result else None

    def update(self, org_id, updates: dict):
        updates["updated_at"] = datetime.utcnow()

        query = (
            organizations_table.update()
            .where(
                organizations_table.c.id == org_id,
                organizations_table.c.deleted_at.is_(None)
            )
            .values(**updates)
            .returning(organizations_table)
        )
        result = self.session.execute(query).fetchone()
        self.session.commit()
        return dict(result) if result else None

    def delete(self, org_id):
        query = (
            organizations_table.update()
            .where(
                organizations_table.c.id == org_id,
                organizations_table.c.deleted_at.is_(None)
            )
            .values(
                deleted_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            .returning(organizations_table.c.id)
        )
        result = self.session.execute(query).scalar()
        self.session.commit()
        return result
