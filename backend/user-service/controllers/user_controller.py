from fastapi import APIRouter, HTTPException, Query, Path
from datetime import datetime
from typing import Optional
from repositories.user_repository import UserRepository
from services.user_service import UserService
from schemas.user_schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    AuthRequest,
)
from db import UnitOfWork
from utils.response import create_response
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

try:
    uow = UnitOfWork()
    user_repo = UserRepository(uow)
    user_service = UserService(user_repo)
except Exception as e:
    logger.error(f"Failed to initialize user service dependencies: {str(e)}")
    raise RuntimeError("Failed to initialize user service") from e

@router.get("/")
def health_check():
    return create_response({
        "message": "User Service is running",
        "status": "deployed",
        "service": "user-service"
    })

@router.get("/health")
def health():
    return create_response({
        "service": "user-service",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    })

# CREATE - Create a new user
@router.post("/users", response_model=UserResponse, status_code=201)
def create_user(user_data: UserCreate):
    try:
        user = user_service.create_user(user_data)
        return create_response({"user": user})
    except ValueError as e:
        logger.warning(f"Validation error creating user: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Runtime error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: Failed to create user")
    except Exception as e:
        logger.error(f"Unexpected error creating user: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while creating user")

# READ - Get all users with pagination and filtering
@router.get("/users", response_model=UserListResponse)
def get_users(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(100, ge=1, le=1000, description="Number of users per page"),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
):
    try:
        result = user_service.get_all_users(page=page, limit=limit, is_active=is_active)
        return result
    except RuntimeError as e:
        logger.error(f"Runtime error retrieving users: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: Failed to retrieve users")
    except Exception as e:
        logger.error(f"Unexpected error retrieving users: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while retrieving users")

# READ - Get user by ID
@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int = Path(..., description="User ID")):
    try:
        user = user_service.get_user_by_id(user_id)
        if user:
            return user
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except RuntimeError as e:
        logger.error(f"Runtime error retrieving user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: Failed to retrieve user")
    except Exception as e:
        logger.error(f"Unexpected error retrieving user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while retrieving user")

# READ - Get user by email
@router.get("/users/email/{email}")
def get_user_by_email(email: str = Path(..., description="User email")):
    try:
        user = user_service.get_user_by_email(email)
        if user:
            return user
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except RuntimeError as e:
        logger.error(f"Runtime error retrieving user by email {email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: Failed to retrieve user")
    except Exception as e:
        logger.error(f"Unexpected error retrieving user by email {email}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while retrieving user")

# UPDATE - Update user by ID
@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int = Path(..., description="User ID"),
    user_data: UserUpdate = None
):
    try:
        user = user_service.update_user(user_id, user_data)
        if user:
            return user
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except ValueError as e:
        logger.warning(f"Validation error updating user {user_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except RuntimeError as e:
        logger.error(f"Runtime error updating user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: Failed to update user")
    except Exception as e:
        logger.error(f"Unexpected error updating user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while updating user")

# DELETE - Soft delete user (set is_active=False)
@router.delete("/users/{user_id}")
def delete_user(user_id: int = Path(..., description="User ID")):
    try:
        success = user_service.delete_user(user_id)
        if success:
            return {"message": "User deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except RuntimeError as e:
        logger.error(f"Runtime error deleting user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: Failed to delete user")
    except Exception as e:
        logger.error(f"Unexpected error deleting user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while deleting user")

# DELETE - Hard delete user (permanently remove from database)
@router.delete("/users/{user_id}/permanent")
def hard_delete_user(user_id: int = Path(..., description="User ID")):
    try:
        success = user_service.hard_delete_user(user_id)
        if success:
            return {"message": "User permanently deleted"}
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to permanently delete user")

# SEARCH - Search users
@router.get("/users/search")
def search_users(
    q: str = Query(..., description="Search term"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(100, ge=1, le=1000, description="Number of users per page")
):
    try:
        users = user_service.search_users(q, page=page, limit=limit)
        return {
            "users": users,
            "search_term": q,
            "page": page,
            "limit": limit,
        }
    except RuntimeError as e:
        logger.error(f"Runtime error searching users: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: Failed to search users")
    except Exception as e:
        logger.error(f"Unexpected error searching users: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while searching users")

# ACTIVATE - Activate user
@router.patch("/users/{user_id}/activate")
def activate_user(user_id: int = Path(..., description="User ID")):
    try:
        success = user_service.activate_user(user_id)
        if success:
            return {"message": "User activated successfully"}
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to activate user")

# DEACTIVATE - Deactivate user
@router.patch("/users/{user_id}/deactivate")
def deactivate_user(user_id: int = Path(..., description="User ID")):
    try:
        success = user_service.deactivate_user(user_id)
        if success:
            return {"message": "User deactivated successfully"}
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to deactivate user")

# AUTHENTICATE - Authenticate user (for login)
@router.post("/users/authenticate")
def authenticate_user(payload: AuthRequest):
    try:
        user = user_service.authenticate_user(payload.email, payload.password)
        if user:
            return {"user": user, "authenticated": True}
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except HTTPException:
        raise
    except RuntimeError as e:
        logger.error(f"Runtime error authenticating user: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error: Authentication failed")
    except Exception as e:
        logger.error(f"Unexpected error authenticating user: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred during authentication")