from fastapi import APIRouter, Depends
from utils.response import create_response
from services.register_service import RegisterService
from database import get_db_session

router = APIRouter(prefix="/register", tags=["registration"])

@router.post("")
def register(payload: dict, db=Depends(get_db_session)):
    service = RegisterService(db)
    result = service.register_org_and_user(payload)
    return create_response("Organization and admin user registered", result)
