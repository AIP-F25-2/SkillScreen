from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import logging
from datetime import datetime, timezone
import uuid

from services.job_position_service import JobPositionService
from schemas.job_position_schemas import (
    JobPositionCreate,
    JobPositionUpdate,
    APIResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/job-positions", tags=["job-positions"])

def create_response(data, success=True, error=None):
    """Create standardized API response"""
    return {
        "success": success,
        "data": data,
        "error": error,
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "request_id": f"req_{uuid.uuid4().hex[:8]}",
            "version": "v1"
        }
    }

@router.post("", response_model=APIResponse)
async def create_job_position(job_position: JobPositionCreate):
    """
    Create a new job position
    
    Required fields:
    - organization_id: UUID of the organization
    - title: Job title (required)
    
    Optional fields:
    - description: Job description
    - required_skills: List of required skills
    - department: Department name
    - is_active: Whether the position is active (default: true)
    - created_by: UUID of the user creating the position
    """
    try:
        job_position_service = JobPositionService()
        
        job_position_data = job_position.dict(exclude_none=True)
        result = job_position_service.create_job_position(job_position_data)
        
        if result["success"]:
            return create_response(result["data"])
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_job_position: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/{job_position_id}", response_model=APIResponse)
async def get_job_position(job_position_id: str):
    """
    Get a specific job position by ID
    """
    try:
        job_position_service = JobPositionService()
        result = job_position_service.get_job_position_by_id(job_position_id)
        
        if result["success"]:
            return create_response(result["data"])
        else:
            if "not found" in result["error"].lower():
                raise HTTPException(status_code=404, detail=result["error"])
            else:
                raise HTTPException(status_code=400, detail=result["error"])
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_job_position: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("", response_model=APIResponse)
async def list_job_positions(
    organization_id: str = Query(..., description="Organization ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
):
    """
    List job positions for an organization
    
    Query parameters:
    - organization_id: Required - UUID of the organization
    - limit: Maximum number of results (default: 100, max: 1000)
    - offset: Number of results to skip (default: 0)
    - is_active: Optional filter for active/inactive positions
    """
    try:
        job_position_service = JobPositionService()
        result = job_position_service.get_job_positions(
            organization_id=organization_id,
            limit=limit,
            offset=offset,
            is_active=is_active
        )
        
        if result["success"]:
            return create_response(result["data"])
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in list_job_positions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.put("/{job_position_id}", response_model=APIResponse)
async def update_job_position(
    job_position_id: str,
    job_position: JobPositionUpdate
):
    """
    Update a job position
    
    All fields are optional - only provided fields will be updated
    """
    try:
        job_position_service = JobPositionService()
        
        update_data = job_position.dict(exclude_none=True)
        result = job_position_service.update_job_position(job_position_id, update_data)
        
        if result["success"]:
            return create_response(result["data"])
        else:
            if "not found" in result["error"].lower():
                raise HTTPException(status_code=404, detail=result["error"])
            else:
                raise HTTPException(status_code=400, detail=result["error"])
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in update_job_position: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.patch("/{job_position_id}", response_model=APIResponse)
async def partial_update_job_position(
    job_position_id: str,
    job_position: JobPositionUpdate
):
    """
    Partially update a job position (same as PUT)
    
    All fields are optional - only provided fields will be updated
    """
    return await update_job_position(job_position_id, job_position)

@router.delete("/{job_position_id}", response_model=APIResponse)
async def delete_job_position(job_position_id: str):
    """
    Soft delete a job position
    
    This sets the deleted_at timestamp but does not remove the record from the database
    """
    try:
        job_position_service = JobPositionService()
        result = job_position_service.delete_job_position(job_position_id)
        
        if result["success"]:
            return create_response(result["data"])
        else:
            if "not found" in result["error"].lower():
                raise HTTPException(status_code=404, detail=result["error"])
            else:
                raise HTTPException(status_code=400, detail=result["error"])
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in delete_job_position: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check for job position endpoints"""
    return create_response({
        "message": "Job position endpoints are healthy",
        "service": "job-position-controller"
    })

