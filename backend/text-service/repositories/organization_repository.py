"""
Repository for Organization entity operations
"""

import sys
sys.path.append("/common-service")

from repository.base_repository import BaseRepository
from sqlalchemy import select
from database.models import Organization
from typing import Optional, Dict, Any


class OrganizationRepository(BaseRepository):
    """Repository for Organization database operations"""
    
    def create(self, name: str, domain: Optional[str] = None, settings: Optional[Dict] = None) -> Organization:
        """Create a new organization"""
        org = Organization(
            name=name,
            domain=domain,
            settings=settings or {}
        )
        self.session.add(org)
        self.session.commit()
        self.session.refresh(org)
        return org
    
    def get_by_id(self, org_id: str) -> Optional[Organization]:
        """Get organization by ID"""
        query = select(Organization).where(Organization.id == org_id)
        result = self.session.execute(query).scalar_one_or_none()
        return result
    
    def get_by_name(self, name: str) -> Optional[Organization]:
        """Get organization by name"""
        query = select(Organization).where(Organization.name == name)
        result = self.session.execute(query).scalar_one_or_none()
        return result
    
    def get_or_create_default(self) -> Organization:
        """Get or create a default organization for testing"""
        org = self.get_by_name("SkillScreen Demo")
        if not org:
            org = self.create(
                name="SkillScreen Demo",
                domain="skillscreen.demo",
                settings={"demo": True}
            )
        return org

