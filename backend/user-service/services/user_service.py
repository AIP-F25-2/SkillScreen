from repositories.user_repository import UserRepository
from schemas.user_schemas import UserCreate, UserUpdate, UserResponse, UserListResponse
from typing import Optional, List, Dict, Any
from datetime import datetime
import hashlib
import secrets

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

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        user = self.user_repo.get_user_by_id(user_id)
        if user:
            user.pop("password_hash", None)
        return user

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        user = self.user_repo.get_user_by_email(email)
        if user:
            user.pop("password_hash", None)
        return user

    def get_all_users(self, page: int = 1, limit: int = 100, is_active: Optional[bool] = None) -> Dict[str, Any]:
        """Get all users with pagination"""
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

    def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[Dict[str, Any]]:
        """Update user by ID"""
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

    def delete_user(self, user_id: int) -> bool:
        """Soft delete user (set is_active=False)"""
        return self.user_repo.delete_user(user_id)

    def hard_delete_user(self, user_id: int) -> bool:
        """Permanently delete user"""
        return self.user_repo.hard_delete_user(user_id)

    def search_users(self, search_term: str, page: int = 1, limit: int = 100) -> List[Dict[str, Any]]:
        """Search users by email, first_name, or last_name"""
        skip = (page - 1) * limit
        
        users = self.user_repo.search_users(search_term, skip=skip, limit=limit)
        
        # Remove password hashes
        for user in users:
            user.pop("password_hash", None)
        
        return users

    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password"""
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

    def activate_user(self, user_id: int) -> bool:
        """Activate a user"""
        return self.user_repo.update_user(user_id, {"is_active": True}) is not None

    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate a user"""
        return self.user_repo.update_user(user_id, {"is_active": False}) is not None
