from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional
from services.interview_service_client import InterviewServiceClient
from config.logger import logger

router = APIRouter()
interview_client = InterviewServiceClient()

@router.post("/upload")
async def upload_resumes(
    files: List[UploadFile] = File(...),
    organization_id: str = Form(...),
    job_position_id: str = Form(...),
    mode: Optional[str] = Form(None, description="Interview mode: chat, audio, video, hybrid (default: video)"),
    difficulty: Optional[str] = Form(None, description="Difficulty level: easy, medium, hard (default: medium)"),
    max_questions: Optional[int] = Form(None, description="Maximum number of questions (default: 15)"),
    interview_type: Optional[str] = Form(None, description="Interview type: mixed, technical, behavioral (default: mixed)"),
    target_duration_minutes: Optional[int] = Form(None, description="Target duration in minutes (default: 12)")
):
    """
    Upload resumes - Interview service auto-schedules interviews
    
    Flow:
    1. Forward files to Interview Service
    2. Interview Service: parse, create candidates, auto-schedule, send emails
    3. Return result
    
    Optional parameters for interview settings (uses defaults if not provided):
    - mode: Interview mode (default: video)
    - difficulty: Difficulty level (default: medium)
    - max_questions: Maximum questions (default: 15)
    - interview_type: Interview type (default: mixed)
    - target_duration_minutes: Target duration (default: 12)
    """
    logger.info(f"📤 Uploading {len(files)} resumes for org {organization_id}, job {job_position_id}")
    
    # Prepare optional interview settings
    interview_settings = {}
    if mode:
        interview_settings['mode'] = mode
    if difficulty:
        interview_settings['difficulty'] = difficulty
    if max_questions:
        interview_settings['max_questions'] = max_questions
    if interview_type:
        interview_settings['interview_type'] = interview_type
    if target_duration_minutes:
        interview_settings['target_duration_minutes'] = target_duration_minutes
    
    try:
        result = await interview_client.upload_resumes(
            files, 
            organization_id, 
            job_position_id,
            interview_settings if interview_settings else None
        )
        logger.info(f"✅ Resumes uploaded successfully")
        return result
    except Exception as e:
        logger.error(f"❌ Resume upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))