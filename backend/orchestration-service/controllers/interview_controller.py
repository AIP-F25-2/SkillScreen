from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
import uuid
import httpx

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


def create_response(data, success=True, message="Success", error=None):
    """Create standardized API response"""
    return {
        "success": success,
        "message": message,
        "data": data,
        "error": error,
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "v1",
            "request_id": f"req_{uuid.uuid4().hex[:8]}"
        }
    }

# ========================================
# STEP 2: Token Validation & Interview Start
# ========================================

@router.get("/validate-token")
async def validate_token_query(token: str):
    """
    STEP 2.1: Validate interview token (candidate clicks email link)

    Flow:
    1. Candidate clicks email link with token: /interview?token=xxx
    2. Frontend calls GET /api/interviews/validate-token?token=xxx
    3. Orchestration validates token via Interview Service
    4. Returns interview details if valid

    Response: { interview_id, candidate_id, candidate_name, status }
    """
    logger.info(f"🔑 STEP 2.1 - Validating token")

    try:
        # Call Interview Service to validate token
        result = await interview_client.validate_token(token)

        if not result.get("success"):
            logger.warning(f"❌ Token validation failed: {result.get('message')}")
            raise HTTPException(status_code=401, detail=result.get("message"))

        interview_data = result.get("data", {})

        logger.info(f"✅ STEP 2.1 - Token validated for candidate {interview_data.get('candidate_id')}")

        return create_response(
            data=interview_data,
            success=True,
            message="Token validated. Interview ready to start."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Token validation failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@router.post("/start/{interview_id}")
async def start_interview_step2(interview_id: str):
    """
    STEP 2.2: Get first question + TTS

    Flow:
    1. Candidate clicks "Start Interview" button
    2. Frontend calls POST /api/interviews/start/{interview_id}
    3. Orchestration:
       - Interview status is already "in_progress" (set during STEP 2.1 token validation)
       - Gets first unanswered question from Text Service
       - Calls Audio Service to generate TTS
    4. Returns question + audio URL

    Response: { interview_id, question_number, question_text, audio_url }
    """
    logger.info(f"🎬 STEP 2.2 - Getting first question for interview {interview_id}")

    try:
        # Note: Interview status was already updated to in_progress during token validation (STEP 2.1)
        # Do NOT call text_client.start_interview() - it will fail because status is already in_progress

        # Step 1: Get interview details
        logger.info(f"   Fetching interview details...")
        interview_info = await interview_client.get_interview(interview_id)
        if not interview_info.get("success"):
            raise HTTPException(status_code=404, detail="Interview not found")

        interview_data = interview_info.get("data", {})
        candidate_id = interview_data.get("candidate_id")
        job_position_id = interview_data.get("job_position_id")

        # Step 2: Generate initial questions from Text Service
        logger.info(f"   Generating initial questions for interview...")
        question_result = await text_client.generate_questions(
            interview_id=interview_id,
            candidate_id=candidate_id,
            job_position_id=job_position_id,
            num_questions=5
        )

        if not question_result.get("success"):
            logger.error(f"❌ Failed to generate questions: {question_result.get('error')}")
            raise HTTPException(status_code=500, detail="Failed to generate questions")

        # Response has "sessions" not "questions"
        sessions_data = question_result.get("data", {}).get("sessions", [])
        if not sessions_data:
            raise HTTPException(status_code=500, detail="No questions generated")

        # Get the first question
        question_data = sessions_data[0]
        question_text = question_data.get("question_text", "")
        session_id = question_data.get("id", "")
        question_number = 1  # First question is always 1

        logger.info(f"✅ First question retrieved")
        logger.info(f"   Session ID: {session_id}")
        logger.info(f"   Question: {question_text[:80]}...")

        # Step 3: Generate TTS for question
        logger.info(f"   Generating TTS audio for question...")
        audio_result = await audio_client.generate_speech(
            text=question_text,
            interview_id=interview_id
        )

        if not audio_result.get("success"):
            logger.warning(f"⚠️ TTS generation failed, continuing without audio: {audio_result.get('message')}")
            audio_url = None
        else:
            audio_url = audio_result.get("data", {}).get("audio_url")

        # Step 4: Build response
        response_data = {
            "interview_id": interview_id,
            "session_id": session_id,
            "question_number": question_number,
            "question_text": question_text,
            "audio_url": audio_url,
            "estimated_answer_time": question_data.get("estimated_answer_time", 60)
        }

        logger.info(f"✅ STEP 2.2 - First question ready")

        return create_response(
            data=response_data,
            success=True,
            message="Interview started. First question retrieved."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Start interview failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {str(e)}")


# ========================================
# Legacy Endpoints
# ========================================

@router.get("/{interview_id}")
async def get_interview(interview_id: str):
    """Get interview details by ID"""
    logger.info(f"📋 Getting interview {interview_id}")

    try:
        result = await interview_client.get_interview(interview_id)
        logger.info(f"✅ Interview retrieved")
        return result
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Interview not found")
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error(f"❌ Get interview failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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