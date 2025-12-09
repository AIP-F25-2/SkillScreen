from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from db import UnitOfWork
from services.user_service import UserService
from repositories.user_repository import UserRepository
from utils.response import create_response
from utilities.logger import init_logger

router = APIRouter()

log = init_logger("user-service")


@router.get("/")
def health_check():
    return create_response({
        "message": "User Service is running",
        "status": "deployed",
        "service": "user-service",
    })


@router.get("/health")
def health():
    return create_response({
        "service": "user-service",
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@router.get("/ping")
def ping():
    log.info("ping", extra={"service": "user-service"})
    return create_response({"message": "pong"})


@router.get("/users")
def get_users():
    with UnitOfWork() as uow:
        repo = UserRepository(uow)
        users = repo.get_all_users()
    return create_response({"users": users})


@router.get("/users/{user_id}")
def get_user(user_id: str):
    with UnitOfWork() as uow:
        repo = UserRepository(uow)
        user = repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found") # nosonar
    return create_response({"user": user})


@router.post("/users")
def create_user(payload: dict):
    with UnitOfWork() as uow:
        service = UserService(uow)
        user_id = service.create(payload)
    return create_response({"id": user_id})


@router.put("/users/{user_id}")
def update_user(user_id: str, payload: dict):
    with UnitOfWork() as uow:
        service = UserService(uow)
        updated = service.update(user_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return create_response({"user": updated})


@router.delete("/users/{user_id}")
def delete_user(user_id: str):
    with UnitOfWork() as uow:
        service = UserService(uow)
        deleted_id = service.delete(user_id)
    if not deleted_id:
        raise HTTPException(status_code=404, detail="User not found")
    return create_response({"id": deleted_id})
