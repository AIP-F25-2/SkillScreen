# from fastapi import APIRouter
# from datetime import datetime
# from repositories.user_repository import UserRepository
# from db import UnitOfWork
# from utils.response import create_response
# from utilities.logger import init_logger

# router = APIRouter()

# uow = UnitOfWork()
# user_repo = UserRepository(uow)
# log = init_logger("user-service")

# @router.get("/")
# def health_check():
#     return create_response({
#         "message": "User Service is running",
#         "status": "deployed",
#         "service": "user-service"
#     })

# @router.get("/health")
# def health():
#     return create_response({
#         "service": "user-service",
#         "status": "healthy",
#         "timestamp": datetime.utcnow().isoformat()
#     })

# @router.get("/users")
# def get_users():
#     users = user_repo.get_all_users()
#     log.info("hello_seq_no_api_key", extra={"ping":"pong"})
#     print("sent")
#     return create_response({"users": users})

# @router.get("/users/{user_id}")
# def get_user(user_id: int):
#     user = user_repo.get_user_by_id(user_id)
#     if user:
#         log.info("hello_seq_no_api_key", extra={"ping":"pong"})
#         print("sent")
#         return create_response({"user": user})
#     else:
#         return create_response({"error": "User not found"}, success=False)

from fastapi import APIRouter, Depends, HTTPException
from utils.response import create_response
from services.user_service import UserService
from database import get_db_session

router = APIRouter(prefix="/users", tags=["users"])

@router.post("")
def create_user(payload: dict, db=Depends(get_db_session)):
    service = UserService(db)
    user_id = service.create(payload)
    return create_response("User created successfully", {"id": user_id})

@router.get("")
def list_users(db=Depends(get_db_session)):
    service = UserService(db)
    return create_response("User list", service.get_all())

@router.get("/{user_id}")
def get_user(user_id: str, db=Depends(get_db_session)):
    service = UserService(db)
    user = service.get_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return create_response("User details", user)

@router.put("/{user_id}")
def update_user(user_id: str, payload: dict, db=Depends(get_db_session)):
    service = UserService(db)
    updated = service.update(user_id, payload)
    if not updated:
        raise HTTPException(404, "User not found")
    return create_response("User updated", updated)

@router.delete("/{user_id}")
def delete_user(user_id: str, db=Depends(get_db_session)):
    service = UserService(db)
    deleted = service.delete(user_id)
    if not deleted:
        raise HTTPException(404, "User not found")
    return create_response("User deleted", {"id": deleted})
