from fastapi import APIRouter, HTTPException, Query, Path
from datetime import datetime
from typing import Optional
from repositories.user_repository import UserRepository
from services.user_service import UserService
from schemas.user_schemas import UserCreate, UserUpdate, UserResponse, UserListResponse
from db import UnitOfWork
from utils.response import create_response

router = APIRouter()

uow = UnitOfWork()
user_repo = UserRepository(uow)
user_service = UserService(user_repo)

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
        return create_response({"user": user}, status_code=201)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create user")

# READ - Get all users with pagination and filtering
@router.get("/users", response_model=UserListResponse)
def get_users(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(100, ge=1, le=1000, description="Number of users per page"),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
):
    try:
        result = user_service.get_all_users(page=page, limit=limit, is_active=is_active)
        return create_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve users")

# READ - Get user by ID
@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int = Path(..., description="User ID")):
    try:
        user = user_service.get_user_by_id(user_id)
        if user:
            return create_response({"user": user})
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve user")

# READ - Get user by email
@router.get("/users/email/{email}")
def get_user_by_email(email: str = Path(..., description="User email")):
    try:
        user = user_service.get_user_by_email(email)
        if user:
            return create_response({"user": user})
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve user")

# UPDATE - Update user by ID
@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int = Path(..., description="User ID"),
    user_data: UserUpdate = None
):
    try:
        user = user_service.update_user(user_id, user_data)
        if user:
            return create_response({"user": user})
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update user")

# DELETE - Soft delete user (set is_active=False)
@router.delete("/users/{user_id}")
def delete_user(user_id: int = Path(..., description="User ID")):
    try:
        success = user_service.delete_user(user_id)
        if success:
            return create_response({"message": "User deleted successfully"})
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete user")

# DELETE - Hard delete user (permanently remove from database)
@router.delete("/users/{user_id}/permanent")
def hard_delete_user(user_id: int = Path(..., description="User ID")):
    try:
        success = user_service.hard_delete_user(user_id)
        if success:
            return create_response({"message": "User permanently deleted"})
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
        return create_response({
            "users": users,
            "search_term": q,
            "page": page,
            "limit": limit
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to search users")

# ACTIVATE - Activate user
@router.patch("/users/{user_id}/activate")
def activate_user(user_id: int = Path(..., description="User ID")):
    try:
        success = user_service.activate_user(user_id)
        if success:
            return create_response({"message": "User activated successfully"})
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
            return create_response({"message": "User deactivated successfully"})
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to deactivate user")

# AUTHENTICATE - Authenticate user (for login)
@router.post("/users/authenticate")
def authenticate_user(email: str, password: str):
    try:
        user = user_service.authenticate_user(email, password)
        if user:
            return create_response({"user": user, "authenticated": True})
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Authentication failed")