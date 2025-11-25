from fastapi import APIRouter
from config.settings import settings
from datetime import datetime

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "timestamp": datetime.utcnow().isoformat()
    }