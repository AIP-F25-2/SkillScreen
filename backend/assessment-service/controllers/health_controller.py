from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from config.settings import settings
import sys


router = APIRouter(tags=["Health"])


# ==========================================
# RESPONSE MODELS
# ==========================================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    timestamp: str
    environment: str


class SchedulerStatusResponse(BaseModel):
    """Scheduler status response"""
    running: bool
    next_run: Optional[str]
    interval_minutes: int
    job_id: Optional[str] = None
    job_name: Optional[str] = None


# ==========================================
# ENDPOINTS
# ==========================================

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Service health check endpoint
    
    Returns basic service information and health status
    """
    return HealthResponse(
        status="healthy",
        service=settings.service_name,
        version="1.0.0",
        timestamp=datetime.now().isoformat(),
        environment=settings.environment
    )


@router.get("/v1/scheduler/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status():
    """
    Get assessment scheduler status
    
    Returns information about the background scheduler:
    - Whether it's running
    - Next scheduled run time
    - Interval configuration
    """
    try:
        from scheduler.scheduler import assessment_scheduler
        
        status = assessment_scheduler.get_status()
        
        return SchedulerStatusResponse(
            running=status['running'],
            next_run=status.get('next_run'),
            interval_minutes=status['interval_minutes'],
            job_id=status.get('job_id'),
            job_name=status.get('job_name')
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving scheduler status: {str(e)}"
        )


@router.post("/v1/scheduler/manual-check")
async def trigger_manual_check():
    """
    Manually trigger an assessment check (for testing/debugging)
    
    This bypasses the scheduled interval and runs the check immediately
    """
    try:
        from scheduler.scheduler import assessment_scheduler
        
        # Run manual check
        await assessment_scheduler.run_manual_check()
        
        return {
            "status": "success",
            "message": "Manual assessment check completed",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error running manual check: {str(e)}"
        )