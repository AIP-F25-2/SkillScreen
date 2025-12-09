from repository.base_repository import BaseRepository
from sqlalchemy import Table, Column, String, DateTime, MetaData, select
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

    # CREATE
    def create_organization(self, data: dict):
        query = organizations_table.insert().values(**data).returning(organizations_table.c.id)
        result = self.session.execute(query)
        return result.scalar()

    # GET ALL
    def get_all(self):
        query = (
            select(organizations_table)
            .where(organizations_table.c.deleted_at.is_(None))
            .order_by(organizations_table.c.created_at.desc())
        )
        return self.session.execute(query).mappings().all()

    # GET by DOMAIN  ✅ used in onboarding
    def get_org_by_domain(self, domain: str):
        query = (
            select(organizations_table)
            .where(
                organizations_table.c.domain == domain,
                organizations_table.c.deleted_at.is_(None),
            )
        )
        result = self.session.execute(query).mappings().fetchone()
        return dict(result) if result else None

    # GET by ID
    def get_by_id(self, org_id):
        query = (
            select(organizations_table)
            .where(
                organizations_table.c.id == org_id,
                organizations_table.c.deleted_at.is_(None),
            )
        )
        result = self.session.execute(query).fetchone()
        return dict(result) if result else None

    # UPDATE
    def update(self, org_id, updates: dict):
        updates["updated_at"] = datetime.utcnow()

        query = (
            organizations_table.update()
            .where(
                organizations_table.c.id == org_id,
                organizations_table.c.deleted_at.is_(None),
            )
            .values(**updates)
            .returning(organizations_table)
        )
        result = self.session.execute(query).fetchone()
        return dict(result) if result else None

    # SOFT DELETE
    def delete(self, org_id):
        query = (
            organizations_table.update()
            .where(
                organizations_table.c.id == org_id,
                organizations_table.c.deleted_at.is_(None),
            )
            .values(
                deleted_at=datetime.utcnow(),
                updated_at=datetime.utcnow(), # nosonar
            )
            .returning(organizations_table.c.id)
        )
        result = self.session.execute(query).scalar()
        return result
