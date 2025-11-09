from fastapi import APIRouter
from datetime import datetime
from repositories.user_repository import UserRepository
from db import UnitOfWork
from utils.response import create_response
from utilities.logger import init_logger

router = APIRouter()

uow = UnitOfWork()
user_repo = UserRepository(uow)
log = init_logger("user-service")

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

@router.get("/users")
def get_users():
    users = user_repo.get_all_users()
    log.info("hello_seq_no_api_key", extra={"ping":"pong"})
    print("sent")
    return create_response({"users": users})

@router.get("/users/{user_id}")
def get_user(user_id: int):
    user = user_repo.get_user_by_id(user_id)
    if user:
        log.info("hello_seq_no_api_key", extra={"ping":"pong"})
        print("sent")
        return create_response({"user": user})
    else:
        return create_response({"error": "User not found"}, success=False)
