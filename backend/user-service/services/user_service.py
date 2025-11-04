from repositories.user_repository import UserRepository
from schemas.user_schemas import UserCreate, UserUpdate, UserResponse, UserListResponse
from typing import Optional, List, Dict, Any
from datetime import datetime
import hashlib
import secrets
import logging

logger = logging.getLogger(__name__)

class UserService:
    
    def __init__(self, user_repository: UserRepository):
        self.user_repo = user_repository

    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"

    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            salt, stored_hash = hashed_password.split(":")
            password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return password_hash == stored_hash
        except:
            return False

    def create_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """Create a new user"""
        try:
            # Check if email already exists
            existing_user = self.user_repo.get_user_by_email(user_data.email)
            if existing_user:
                raise ValueError(f"User with email {user_data.email} already exists")

            # Hash password
            hashed_password = self._hash_password(user_data.password)
            
            # Prepare user data for database
            user_dict = user_data.model_dump(exclude={"password"})
            user_dict["password_hash"] = hashed_password
            user_dict["created_at"] = datetime.utcnow()
            user_dict["updated_at"] = datetime.utcnow()

            # Create user
            created_user = self.user_repo.create_user(user_dict)
            
            # Remove password hash from response
            if created_user:
                created_user.pop("password_hash", None)
            
            return created_user
        except ValueError:
            raise  # Re-raise validation errors
        except RuntimeError as e:
            logger.error(f"Runtime error creating user: {str(e)}")
            raise RuntimeError(f"Failed to create user: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating user: {str(e)}")
            raise RuntimeError(f"Unexpected error creating user: {str(e)}")

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            user = self.user_repo.get_user_by_id(user_id)
            if user:
                user.pop("password_hash", None)
            return user
        except RuntimeError:
            raise  # Re-raise database errors
        except Exception as e:
            logger.error(f"Unexpected error getting user by ID {user_id}: {str(e)}")
            raise RuntimeError(f"Unexpected error retrieving user: {str(e)}")

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            user = self.user_repo.get_user_by_email(email)
            if user:
                user.pop("password_hash", None)
            return user
        except RuntimeError:
            raise  # Re-raise database errors
        except Exception as e:
            logger.error(f"Unexpected error getting user by email {email}: {str(e)}")
            raise RuntimeError(f"Unexpected error retrieving user: {str(e)}")

    def get_all_users(self, page: int = 1, limit: int = 100, is_active: Optional[bool] = None) -> Dict[str, Any]:
        """Get all users with pagination"""
        try:
            skip = (page - 1) * limit
            
            users = self.user_repo.get_all_users(skip=skip, limit=limit, is_active=is_active)
            total = self.user_repo.count_users(is_active=is_active)
            
            # Remove password hashes
            for user in users:
                user.pop("password_hash", None)
            
            return {
                "users": users,
                "total": total,
                "page": page,
                "limit": limit,
                "has_next": (skip + limit) < total,
                "has_prev": page > 1
            }
        except RuntimeError:
            raise  # Re-raise database errors
        except Exception as e:
            logger.error(f"Unexpected error getting all users: {str(e)}")
            raise RuntimeError(f"Unexpected error retrieving users: {str(e)}")

    def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[Dict[str, Any]]:
        """Update user by ID"""
        try:
            # Check if user exists
            existing_user = self.user_repo.get_user_by_id(user_id)
            if not existing_user:
                return None

            # If email is being updated, check if it's already taken
            if user_data.email and user_data.email != existing_user["email"]:
                email_user = self.user_repo.get_user_by_email(user_data.email)
                if email_user and email_user["id"] != user_id:
                    raise ValueError(f"Email {user_data.email} is already taken")

            # Prepare update data (exclude None values)
            update_dict = user_data.model_dump(exclude_unset=True, exclude_none=True)
            
            # Update user
            updated_user = self.user_repo.update_user(user_id, update_dict)
            
            # Remove password hash from response
            if updated_user:
                updated_user.pop("password_hash", None)
            
            return updated_user
        except ValueError:
            raise  # Re-raise validation errors
        except RuntimeError:
            raise  # Re-raise database errors
        except Exception as e:
            logger.error(f"Unexpected error updating user {user_id}: {str(e)}")
            raise RuntimeError(f"Unexpected error updating user: {str(e)}")

    def delete_user(self, user_id: int) -> bool:
        """Soft delete user (set is_active=False)"""
        try:
            return self.user_repo.delete_user(user_id)
        except RuntimeError:
            raise  # Re-raise database errors
        except Exception as e:
            logger.error(f"Unexpected error deleting user {user_id}: {str(e)}")
            raise RuntimeError(f"Unexpected error deleting user: {str(e)}")

    def hard_delete_user(self, user_id: int) -> bool:
        """Permanently delete user"""
        try:
            return self.user_repo.hard_delete_user(user_id)
        except RuntimeError:
            raise  # Re-raise database errors
        except Exception as e:
            logger.error(f"Unexpected error hard deleting user {user_id}: {str(e)}")
            raise RuntimeError(f"Unexpected error deleting user: {str(e)}")

    def search_users(self, search_term: str, page: int = 1, limit: int = 100) -> List[Dict[str, Any]]:
        """Search users by email, first_name, or last_name"""
        try:
            skip = (page - 1) * limit
            
            users = self.user_repo.search_users(search_term, skip=skip, limit=limit)
            
            # Remove password hashes
            for user in users:
                user.pop("password_hash", None)
            
            return users
        except RuntimeError:
            raise  # Re-raise database errors
        except Exception as e:
            logger.error(f"Unexpected error searching users: {str(e)}")
            raise RuntimeError(f"Unexpected error searching users: {str(e)}")

    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password"""
        try:
            user = self.user_repo.get_user_by_email(email)
            if not user:
                return None
            
            if not user.get("is_active", True):
                return None
            
            if not self._verify_password(password, user["password_hash"]):
                return None
            
            # Remove password hash from response
            user.pop("password_hash", None)
            return user
        except RuntimeError:
            raise  # Re-raise database errors
        except Exception as e:
            logger.error(f"Unexpected error authenticating user: {str(e)}")
            raise RuntimeError(f"Unexpected error authenticating user: {str(e)}")

    def activate_user(self, user_id: int) -> bool:
        """Activate a user"""
        try:
            return self.user_repo.update_user(user_id, {"is_active": True}) is not None
        except RuntimeError:
            raise  # Re-raise database errors
        except Exception as e:
            logger.error(f"Unexpected error activating user {user_id}: {str(e)}")
            raise RuntimeError(f"Unexpected error activating user: {str(e)}")

    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate a user"""
        try:
            return self.user_repo.update_user(user_id, {"is_active": False}) is not None
        except RuntimeError:
            raise  # Re-raise database errors
        except Exception as e:
            logger.error(f"Unexpected error deactivating user {user_id}: {str(e)}")
            raise RuntimeError(f"Unexpected error deactivating user: {str(e)}")
