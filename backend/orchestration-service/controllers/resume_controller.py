from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional
from datetime import datetime
import uuid

from services.interview_service_client import InterviewServiceClient
from schemas.resume_schemas import ResumeUploadResponse
from config.logger import logger

router = APIRouter()
interview_client = InterviewServiceClient()


def create_response(data, success=True, message="Success", error=None):
    """Create standardized API response"""
    return {
        "success": success,
        "message": message,
        "data": data,
        "error": error,
        "meta": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": "v1",
            "request_id": f"req_{uuid.uuid4().hex[:8]}"
        }
    }


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resumes(
    files: List[UploadFile] = File(..., description="Resume files (PDF, DOCX, ZIP)"),
    organization_id: str = Form(..., description="Organization UUID"),
    job_position_id: str = Form(..., description="Job Position UUID"),
    mode: Optional[str] = Form(None, description="Interview mode: video, audio, chat (default: video)"),
    difficulty: Optional[str] = Form(None, description="Difficulty: easy, medium, hard (default: medium)"),
    max_questions: Optional[int] = Form(None, description="Max questions (default: 15)"),
    interview_type: Optional[str] = Form(None, description="Type: mixed, technical, behavioral (default: mixed)"),
    target_duration_minutes: Optional[int] = Form(None, description="Duration in minutes (default: 12)")
):
    """
    Upload resumes for interview scheduling

    Flow:
    1. Validate inputs
    2. Call Interview Service to process resumes
    3. Interview Service:
       - Parses resume files
       - Extracts candidate information
       - Creates candidate records in database
       - Gets template_id from interview_templates
       - Creates interview records (status: "scheduled")
       - Sends email invitations to candidates
    4. Return candidates + interviews created

    Response includes:
    - upload_id: batch identifier
    - candidates_created: count
    - interviews_scheduled: count
    - candidates: list with ids
    - interviews: list with interview_ids and links
    """
    start_time = datetime.utcnow()

    try:
        # Validate inputs
        if not files or len(files) == 0:
            logger.warning("❌ No files provided for resume upload")
            raise HTTPException(status_code=400, detail="No files provided")

        if len(files) > 10:
            logger.warning(f"❌ Too many files: {len(files)}")
            raise HTTPException(status_code=400, detail="Maximum 10 files allowed per upload")

        if not organization_id or not job_position_id:
            logger.warning("❌ Missing organization_id or job_position_id")
            raise HTTPException(status_code=400, detail="organization_id and job_position_id are required")

        logger.info(f"📤 STEP 1 - Resume Upload Started")
        logger.info(f"   Files: {len(files)}")
        logger.info(f"   Organization: {organization_id}")
        logger.info(f"   Job Position: {job_position_id}")
        logger.info(f"   Settings: mode={mode}, difficulty={difficulty}, max_questions={max_questions}")

        # Build interview settings
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

        # Call Interview Service
        logger.info(f"   Calling Interview Service...")
        result = await interview_client.upload_resumes(
            files=files,
            organization_id=organization_id,
            job_position_id=job_position_id,
            interview_settings=interview_settings if interview_settings else None
        )

        # Parse Interview Service response
        if not result.get("success"):
            logger.error(f"❌ Interview Service returned failure: {result.get('message')}")
            raise HTTPException(status_code=500, detail=result.get("message"))

        interview_data = result.get("data", {})

        # Build response
        processing_time = (datetime.utcnow() - start_time).total_seconds()

        # Interview Service returns candidates_saved (not candidates_created)
        # and creates interviews automatically, so interviews_scheduled = candidates_saved
        candidates_count = interview_data.get("candidates_saved", 0)

        upload_response_data = {
            "upload_id": interview_data.get("upload_id", str(uuid.uuid4())),
            "organization_id": organization_id,
            "job_position_id": job_position_id,
            "total_files_processed": interview_data.get("files_received", len(files)),
            "candidates_created": candidates_count,
            "interviews_scheduled": candidates_count,  # One interview per candidate
            "candidates": interview_data.get("candidates", []),
            "interviews": interview_data.get("interviews", []),
            "failed_files": interview_data.get("failed_files"),
            "files_processed": interview_data.get("files_processed", 0),
            "processing_time_seconds": processing_time
        }

        logger.info(f"✅ STEP 1 - Resume Upload Completed")
        logger.info(f"   Candidates created: {upload_response_data['candidates_created']}")
        logger.info(f"   Interviews scheduled: {upload_response_data['interviews_scheduled']}")
        logger.info(f"   Processing time: {processing_time:.2f}s")

        return create_response(
            data=upload_response_data,
            success=True,
            message=f"Successfully processed {len(files)} resume(s). {upload_response_data['candidates_created']} candidate(s) created, {upload_response_data['interviews_scheduled']} interview(s) scheduled."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Resume upload failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check for resume endpoints"""
    return create_response(
        data={"status": "healthy", "service": "resume-orchestration"},
        success=True,
        message="Resume orchestration endpoints are healthy"
    )