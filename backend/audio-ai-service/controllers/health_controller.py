from fastapi import APIRouter
from config import settings, logger
import psutil
import os
from datetime import datetime

router = APIRouter()

@router.get("")
async def health_check():
    """
    Health check endpoint for container orchestration
    Returns service status and basic metrics
    """
    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(os.getcwd())
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "system_metrics": {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory.percent,
                "memory_available_mb": memory.available / (1024 * 1024),
                "disk_usage_percent": disk.percent
            },
            "config": {
                "whisper_model": settings.WHISPER_MODEL_SIZE,
                "whisper_device": settings.WHISPER_DEVICE,
                "temp_dir": settings.TEMP_AUDIO_DIR
            }
        }
        
        logger.debug("Health check successful")
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/ready")
async def readiness_check():
    """
    Readiness check - is the service ready to accept requests?
    Checks if models are loaded, directories exist, etc.
    """
    checks = {
        "temp_dir_exists": os.path.exists(settings.TEMP_AUDIO_DIR),
        "models_dir_exists": os.path.exists(settings.MODEL_CACHE_DIR),
        "sufficient_memory": psutil.virtual_memory().available > 1024 * 1024 * 1024  # >1GB
    }
    
    all_ready = all(checks.values())
    
    return {
        "ready": all_ready,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/live")
async def liveness_check():
    """
    Liveness check - is the service alive?
    Simple check that returns 200 OK
    """
    return {"alive": True, "timestamp": datetime.utcnow().isoformat()}