from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
from services.interview_service_client import InterviewServiceClient
from config.logger import logger

router = APIRouter()
interview_client = InterviewServiceClient()

@router.post("/upload")
async def upload_resumes(
    files: List[UploadFile] = File(...),
    organization_id: str = Form(...)
):
    """
    Upload resumes - Interview service auto-schedules interviews
    
    Flow:
    1. Forward files to Interview Service
    2. Interview Service: parse, create candidates, auto-schedule, send emails
    3. Return result
    """
    logger.info(f"📤 Uploading {len(files)} resumes for org {organization_id}")
    
    try:
        result = await interview_client.upload_resumes(files, organization_id)
        logger.info(f"✅ Resumes uploaded successfully")
        return result
    except Exception as e:
        logger.error(f"❌ Resume upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))