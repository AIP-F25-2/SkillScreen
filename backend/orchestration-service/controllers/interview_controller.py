from fastapi import APIRouter, HTTPException

from schemas.interview_schemas import (
   
    ValidateTokenRequest,
    StartInterviewRequest,
    StartInterviewResponse
)
from services.interview_service_client import InterviewServiceClient
from services.text_service_client import TextServiceClient
from services.audio_service_client import AudioServiceClient
from config.logger import logger

router = APIRouter()
interview_client = InterviewServiceClient()
text_client = TextServiceClient()
audio_client = AudioServiceClient()

@router.post("/validate-token")
async def validate_token(request: ValidateTokenRequest):
    """Validate interview token when candidate clicks link"""
    logger.info(f"🔑 Validating token")
    
    try:
        result = await interview_client.validate_token(request.token)
        logger.info(f"✅ Token validated")
        return result
    except Exception as e:
        logger.error(f"❌ Token validation failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

@router.post("/start", response_model=StartInterviewResponse)
async def start_interview(request: StartInterviewRequest):
    """
    Start interview
    
    Flow:
    1. Text Service: start interview, get first question
    2. Audio-AI: generate TTS for first question
    3. Return question + audio
    """
    logger.info(f"🎬 Starting interview for candidate {request.candidate_id}")
    
    try:
        # Get first question from text service
        text_result = await text_client.start_interview(
            candidate_id=request.candidate_id,
            job_id=request.job_id,
            interview_type=request.interview_type,
            difficulty=request.difficulty,
            max_questions=request.max_questions
        )
        
        session_id = text_result["session_id"]
        interview_id = text_result["interview_id"]
        initial_question = text_result["initial_question"]
        
        # Generate TTS
        audio_result = await audio_client.generate_speech(
            text=initial_question["question_text"],
            session_id=session_id
        )
        
        logger.info(f"✅ Interview started: {session_id}")
        
        return StartInterviewResponse(
            session_id=session_id,
            interview_id=interview_id,
            initial_question=initial_question["question_text"],
            question_id=initial_question["id"],
            audio_download_url=audio_result["download_url"],
            status="started"
        )
    except Exception as e:
        logger.error(f"❌ Start interview failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))