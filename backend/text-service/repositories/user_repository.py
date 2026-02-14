"""
Repository for User entity operations
"""

import sys
sys.path.append("/common-service")

from repository.base_repository import BaseRepository
from sqlalchemy import select, text
from database.models import User, UserRole
from typing import Optional
import uuid


class UserRepository(BaseRepository):
    """Repository for User database operations"""
    
    def create(self, organization_id: str, email: str, first_name: str, last_name: str, 
               role: UserRole, password_hash: Optional[str] = None) -> User:
        """Create a new user"""
        # Database enum might not have CANDIDATE - use INTERVIEWER as fallback
        role_mapping = {
            UserRole.ADMIN: "ADMIN",
            UserRole.RECRUITER: "RECRUITER",
            UserRole.INTERVIEWER: "INTERVIEWER",
            UserRole.CANDIDATE: "INTERVIEWER",  # Use INTERVIEWER if CANDIDATE doesn't exist in DB
            UserRole.TECHNICAL_EVALUATOR: "TECHNICAL_EVALUATOR",
            UserRole.COMPLIANCE_OFFICER: "COMPLIANCE_OFFICER"
        }
        role_value = role_mapping.get(role, role.name if hasattr(role, 'name') else str(role).upper())
        
        user_id = uuid.uuid4()
        
        # Insert using raw SQL with explicit enum casting (uppercase)
        self.session.execute(
            text("""
                INSERT INTO users (id, organization_id, email, password_hash, first_name, last_name, role, is_active, deleted_at, created_at, updated_at)
                VALUES (:id::UUID, :org_id::UUID, :email, :password_hash, :first_name, :last_name, :role::user_role, :is_active, NULL, NOW(), NOW())
            """),
            {
                "id": str(user_id),
                "org_id": organization_id,
                "email": email,
                "password_hash": password_hash,
                "first_name": first_name,
                "last_name": last_name,
                "role": role_value,
                "is_active": True
            }
        )
        self.session.commit()
        
        # Fetch the created user
        return self.get_by_id(str(user_id))
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        query = select(User).where(User.id == user_id)
        result = self.session.execute(query).scalar_one_or_none()
        return result
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        query = select(User).where(User.email == email)
        result = self.session.execute(query).scalar_one_or_none()
        return result
    
    def get_or_create_demo(self, email: str = "demo@skillscreen.com", organization_id: Optional[str] = None) -> User:
        """Get or create a demo user"""
        user = self.get_by_email(email)
        if not user:
            if not organization_id:
                # Import here to avoid circular dependency
                from .organization_repository import OrganizationRepository
                from db import UnitOfWork
                uow = UnitOfWork()
                org_repo = OrganizationRepository(uow)
                org = org_repo.get_or_create_default()
                organization_id = str(org.id)
            
            user = self.create(
                organization_id=organization_id,
                email=email,
                first_name="Demo",
                last_name="User",
                role=UserRole.CANDIDATE
            )
        return user

