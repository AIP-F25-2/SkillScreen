from fastapi import APIRouter
from datetime import datetime
import psutil
import os

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint for orchestration service
    Returns service status and basic metrics
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "orchestration-service",
            "version": "1.0.0",
            "system_metrics": {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory.percent,
                "memory_available_mb": memory.available / (1024 * 1024)
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/health/ready")
async def readiness_check():
    """
    Readiness check - is the service ready to accept requests?
    """
    checks = {
        "service_running": True,
        "sufficient_memory": psutil.virtual_memory().available > 512 * 1024 * 1024  # >512MB
    }
    
    all_ready = all(checks.values())
    
    return {
        "ready": all_ready,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/live")
async def liveness_check():
    """
    Liveness check - is the service alive?
    """
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat()
    }

