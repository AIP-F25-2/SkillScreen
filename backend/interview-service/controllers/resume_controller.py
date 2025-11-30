from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Form
from typing import List, Optional
import logging
from datetime import datetime, timezone
import uuid

from services.resume_service import ResumeService
from schemas.resume_schemas import ResumeUploadResponse, APIResponse

# Note: email_service is passed as a parameter during router setup in interview.py
_email_service_instance = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resumes", tags=["resumes"])

def set_email_service(email_service_instance):
    """Inject email_service instance (called from interview.py)"""
    global _email_service_instance
    _email_service_instance = email_service_instance

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
    organization_id: str = Form(..., description="Organization ID for the candidates"),
    job_position_id: str = Form(..., description="Job Position ID for the interviews"),
    mode: Optional[str] = Form(None, description="Interview mode: chat, audio, video, hybrid (default: video)"),
    difficulty: Optional[str] = Form(None, description="Difficulty level: easy, medium, hard (default: medium)"),
    max_questions: Optional[int] = Form(None, description="Maximum number of questions (default: 15)"),
    interview_type: Optional[str] = Form(None, description="Interview type: mixed, technical, behavioral (default: mixed)"),
    target_duration_minutes: Optional[int] = Form(None, description="Target duration in minutes (default: 12)")
):
    """
    Upload single or multiple resume files for a specific organization
    
    Supports:
    - PDF files (.pdf)
    - Word documents (.doc, .docx)
    - ZIP archives containing multiple resumes
    
    Optional parameters for interview settings (uses defaults if not provided):
    - mode: Interview mode (default: video)
    - difficulty: Difficulty level (default: medium)
    - max_questions: Maximum questions (default: 15)
    - interview_type: Interview type (default: mixed)
    - target_duration_minutes: Target duration (default: 12)
    
    Returns upload ID, processing status, and extracted information.
    """
    try:
        # Validate files
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        if len(files) > 10:  # Limit to 10 files per upload
            raise HTTPException(status_code=400, detail="Maximum 10 files allowed per upload")
        
        logger.info(f"Received {len(files)} files for upload for organization: {organization_id}, job_position: {job_position_id}")

        # Prepare optional interview settings
        interview_settings = {}
        if mode:
            interview_settings['mode'] = mode
        if difficulty:
            interview_settings['difficulty'] = difficulty
        if max_questions is not None:
            interview_settings['max_questions'] = max_questions
        if interview_type:
            interview_settings['interview_type'] = interview_type
        if target_duration_minutes is not None:
            interview_settings['target_duration_minutes'] = target_duration_minutes

        # Initialize resume service with the injected email_service instance
        resume_service = ResumeService(email_service_instance=_email_service_instance)
        
        # Process files with organization_id, job_position_id, and optional settings
        result = await resume_service.process_resume_upload(
            files, 
            organization_id, 
            job_position_id,
            interview_settings if interview_settings else None
        )
        
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
