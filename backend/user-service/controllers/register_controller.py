from fastapi import APIRouter
from db import UnitOfWork
from services.register_service import RegisterService
from utils.response import create_response

router = APIRouter(prefix="/register", tags=["register"])

@router.post("")
def register(payload: dict):
    with UnitOfWork() as uow:
        service = RegisterService(uow)
        result = service.register(payload)
    return create_response(result)
