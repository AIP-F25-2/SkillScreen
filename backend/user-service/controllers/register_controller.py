from fastapi import APIRouter, Depends
from database import get_db_session
from services.register_service import RegisterService
from utils.response import create_response

router = APIRouter(prefix="/register", tags=["registration"])

@router.post("")
def register(payload: dict, db=Depends(get_db_session)):
    service = RegisterService(db)
    result = service.register(payload)
    return create_response("Organization and admin registered successfully", result)
