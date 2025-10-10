from repository.base_repository import BaseRepository
from sqlalchemy import Table, Column, Integer, String, Boolean, DateTime, MetaData, select, insert, update, delete, func, text
from datetime import datetime
from typing import Optional, List, Dict, Any

metadata = MetaData()

users_table = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String, unique=True, nullable=False),
    Column("first_name", String),
    Column("last_name", String),
    Column("phone", String),
    Column("password_hash", String, nullable=False),
    Column("is_active", Boolean, default=True),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
)

class UserRepository(BaseRepository):

    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user"""
        query = insert(users_table).values(**user_data)
        result = self.session.execute(query)
        self.session.commit()
        
        # Return the created user
        user_id = result.inserted_primary_key[0]
        return self.get_user_by_id(user_id)

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        query = select(users_table).where(users_table.c.id == user_id)
        result = self.session.execute(query).fetchone()
        return dict(result._mapping) if result else None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        query = select(users_table).where(users_table.c.email == email)
        result = self.session.execute(query).fetchone()
        return dict(result._mapping) if result else None

    def get_all_users(self, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Get all users with pagination and optional filtering"""
        query = select(users_table)
        
        if is_active is not None:
            query = query.where(users_table.c.is_active == is_active)
            
        query = query.offset(skip).limit(limit).order_by(users_table.c.created_at.desc())
        
        result = self.session.execute(query)
        users = [dict(row._mapping) for row in result]
        return users

    def count_users(self, is_active: Optional[bool] = None) -> int:
        """Count total users with optional filtering"""
        query = select(func.count(users_table.c.id))
        
        if is_active is not None:
            query = query.where(users_table.c.is_active == is_active)
            
        result = self.session.execute(query)
        return result.scalar()

    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user by ID"""
        # Add updated_at timestamp
        user_data["updated_at"] = datetime.utcnow()
        
        query = (
            update(users_table)
            .where(users_table.c.id == user_id)
            .values(**user_data)
            .returning(users_table)
        )
        
        result = self.session.execute(query).fetchone()
        self.session.commit()
        
        return dict(result._mapping) if result else None

    def delete_user(self, user_id: int) -> bool:
        """Delete user by ID (soft delete by setting is_active=False)"""
        query = (
            update(users_table)
            .where(users_table.c.id == user_id)
            .values(is_active=False, updated_at=datetime.utcnow())
        )
        
        result = self.session.execute(query)
        self.session.commit()
        
        return result.rowcount > 0

    def hard_delete_user(self, user_id: int) -> bool:
        """Permanently delete user from database"""
        query = delete(users_table).where(users_table.c.id == user_id)
        result = self.session.execute(query)
        self.session.commit()
        
        return result.rowcount > 0

    def search_users(self, search_term: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Search users by email, first_name, or last_name"""
        search_pattern = f"%{search_term}%"
        
        query = select(users_table).where(
            (users_table.c.email.ilike(search_pattern)) |
            (users_table.c.first_name.ilike(search_pattern)) |
            (users_table.c.last_name.ilike(search_pattern))
        ).offset(skip).limit(limit).order_by(users_table.c.created_at.desc())
        
        result = self.session.execute(query)
        users = [dict(row._mapping) for row in result]
        return users
