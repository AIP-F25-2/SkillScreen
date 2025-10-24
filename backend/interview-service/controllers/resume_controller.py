from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Form
from typing import List
import logging
from datetime import datetime, timezone
import uuid

from services.resume_service import ResumeService
from schemas.resume_schemas import ResumeUploadResponse, APIResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resumes", tags=["resumes"])

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

@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resumes(
    files: List[UploadFile] = File(..., description="Resume files to upload (PDF, DOC, DOCX, ZIP)"),
    organization_id: str = Form(..., description="Organization ID for the candidates")
):
    """
    Upload single or multiple resume files for a specific organization
    
    Supports:
    - PDF files (.pdf)
    - Word documents (.doc, .docx)
    - ZIP archives containing multiple resumes
    
    Returns upload ID, processing status, and extracted information.
    """
    try:
        # Validate files
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        if len(files) > 10:  # Limit to 10 files per upload
            raise HTTPException(status_code=400, detail="Maximum 10 files allowed per upload")
        
        # organization_id is now passed as a form parameter
        
        logger.info(f"Received {len(files)} files for upload for organization: {organization_id}")
        
        # Initialize resume service
        resume_service = ResumeService()
        
        # Process files with organization_id
        result = await resume_service.process_resume_upload(files, organization_id)
        
        if result["success"]:
            return create_response(result["data"])
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in upload_resumes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check for resume endpoints"""
    return create_response({
        "message": "Resume endpoints are healthy",
        "service": "resume-controller"
    })
