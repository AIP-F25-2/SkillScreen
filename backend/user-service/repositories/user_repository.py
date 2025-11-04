from repository.base_repository import BaseRepository
from sqlalchemy import Table, Column, Integer, String, Boolean, DateTime, MetaData, select, insert, update, delete, func, text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

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
        try:
            query = insert(users_table).values(**user_data)
            result = self.session.execute(query)
            self.session.commit()
            
            # Return the created user
            user_id = result.inserted_primary_key[0]
            return self.get_user_by_id(user_id)
        except IntegrityError as e:
            self.session.rollback()
            logger.error(f"Integrity error creating user: {str(e)}")
            raise ValueError(f"User with email {user_data.get('email')} already exists or constraint violation")
        except OperationalError as e:
            self.session.rollback()
            logger.error(f"Database operational error creating user: {str(e)}")
            raise RuntimeError("Database connection error while creating user")
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error creating user: {str(e)}")
            raise RuntimeError(f"Failed to create user: {str(e)}")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Unexpected error creating user: {str(e)}")
            raise RuntimeError(f"Unexpected error creating user: {str(e)}")

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            query = select(users_table).where(users_table.c.id == user_id)
            result = self.session.execute(query).fetchone()
            return dict(result._mapping) if result else None
        except OperationalError as e:
            logger.error(f"Database operational error getting user by ID {user_id}: {str(e)}")
            raise RuntimeError("Database connection error while retrieving user")
        except SQLAlchemyError as e:
            logger.error(f"Database error getting user by ID {user_id}: {str(e)}")
            raise RuntimeError(f"Failed to retrieve user: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error getting user by ID {user_id}: {str(e)}")
            raise RuntimeError(f"Unexpected error retrieving user: {str(e)}")

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            query = select(users_table).where(users_table.c.email == email)
            result = self.session.execute(query).fetchone()
            return dict(result._mapping) if result else None
        except OperationalError as e:
            logger.error(f"Database operational error getting user by email {email}: {str(e)}")
            raise RuntimeError("Database connection error while retrieving user")
        except SQLAlchemyError as e:
            logger.error(f"Database error getting user by email {email}: {str(e)}")
            raise RuntimeError(f"Failed to retrieve user: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error getting user by email {email}: {str(e)}")
            raise RuntimeError(f"Unexpected error retrieving user: {str(e)}")

    def get_all_users(self, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Get all users with pagination and optional filtering"""
        try:
            query = select(users_table)
            
            if is_active is not None:
                query = query.where(users_table.c.is_active == is_active)
                
            query = query.offset(skip).limit(limit).order_by(users_table.c.created_at.desc())
            
            result = self.session.execute(query)
            users = [dict(row._mapping) for row in result]
            return users
        except OperationalError as e:
            logger.error(f"Database operational error getting all users: {str(e)}")
            raise RuntimeError("Database connection error while retrieving users")
        except SQLAlchemyError as e:
            logger.error(f"Database error getting all users: {str(e)}")
            raise RuntimeError(f"Failed to retrieve users: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error getting all users: {str(e)}")
            raise RuntimeError(f"Unexpected error retrieving users: {str(e)}")

    def count_users(self, is_active: Optional[bool] = None) -> int:
        """Count total users with optional filtering"""
        try:
            query = select(func.count(users_table.c.id))
            
            if is_active is not None:
                query = query.where(users_table.c.is_active == is_active)
                
            result = self.session.execute(query)
            return result.scalar() or 0
        except OperationalError as e:
            logger.error(f"Database operational error counting users: {str(e)}")
            raise RuntimeError("Database connection error while counting users")
        except SQLAlchemyError as e:
            logger.error(f"Database error counting users: {str(e)}")
            raise RuntimeError(f"Failed to count users: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error counting users: {str(e)}")
            raise RuntimeError(f"Unexpected error counting users: {str(e)}")

    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user by ID"""
        try:
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
        except IntegrityError as e:
            self.session.rollback()
            logger.error(f"Integrity error updating user {user_id}: {str(e)}")
            raise ValueError(f"Constraint violation while updating user: {str(e)}")
        except OperationalError as e:
            self.session.rollback()
            logger.error(f"Database operational error updating user {user_id}: {str(e)}")
            raise RuntimeError("Database connection error while updating user")
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error updating user {user_id}: {str(e)}")
            raise RuntimeError(f"Failed to update user: {str(e)}")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Unexpected error updating user {user_id}: {str(e)}")
            raise RuntimeError(f"Unexpected error updating user: {str(e)}")

    def delete_user(self, user_id: int) -> bool:
        """Delete user by ID (soft delete by setting is_active=False)"""
        try:
            query = (
                update(users_table)
                .where(users_table.c.id == user_id)
                .values(is_active=False, updated_at=datetime.utcnow())
            )
            
            result = self.session.execute(query)
            self.session.commit()
            
            return result.rowcount > 0
        except OperationalError as e:
            self.session.rollback()
            logger.error(f"Database operational error deleting user {user_id}: {str(e)}")
            raise RuntimeError("Database connection error while deleting user")
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error deleting user {user_id}: {str(e)}")
            raise RuntimeError(f"Failed to delete user: {str(e)}")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Unexpected error deleting user {user_id}: {str(e)}")
            raise RuntimeError(f"Unexpected error deleting user: {str(e)}")

    def hard_delete_user(self, user_id: int) -> bool:
        """Permanently delete user from database"""
        try:
            query = delete(users_table).where(users_table.c.id == user_id)
            result = self.session.execute(query)
            self.session.commit()
            
            return result.rowcount > 0
        except OperationalError as e:
            self.session.rollback()
            logger.error(f"Database operational error hard deleting user {user_id}: {str(e)}")
            raise RuntimeError("Database connection error while deleting user")
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error hard deleting user {user_id}: {str(e)}")
            raise RuntimeError(f"Failed to delete user: {str(e)}")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Unexpected error hard deleting user {user_id}: {str(e)}")
            raise RuntimeError(f"Unexpected error deleting user: {str(e)}")

    def search_users(self, search_term: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Search users by email, first_name, or last_name"""
        try:
            search_pattern = f"%{search_term}%"
            
            query = select(users_table).where(
                (users_table.c.email.ilike(search_pattern)) |
                (users_table.c.first_name.ilike(search_pattern)) |
                (users_table.c.last_name.ilike(search_pattern))
            ).offset(skip).limit(limit).order_by(users_table.c.created_at.desc())
            
            result = self.session.execute(query)
            users = [dict(row._mapping) for row in result]
            return users
        except OperationalError as e:
            logger.error(f"Database operational error searching users: {str(e)}")
            raise RuntimeError("Database connection error while searching users")
        except SQLAlchemyError as e:
            logger.error(f"Database error searching users: {str(e)}")
            raise RuntimeError(f"Failed to search users: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error searching users: {str(e)}")
            raise RuntimeError(f"Unexpected error searching users: {str(e)}")
