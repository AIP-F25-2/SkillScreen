from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from config import logger
from services import InterviewService
from schemas import InterviewStartRequest, InterviewResponseRequest, NextQuestionRequest

router = APIRouter()
interview_service = InterviewService()


def create_response(success: bool, data=None, error=None, meta=None):
    """Standardized response format"""
    return {
        "success": success,
        "data": data,
        "error": error,
        "meta": meta or {}
    }


@router.get("/api/interviews/{interview_id}")
async def get_interview(interview_id: str):
    """
    Get interview details
    STEP 2.2.1: Get interview and first question
    """
    try:
        result = interview_service.get_interview_with_questions(interview_id)

        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error"))

        return create_response(
            success=True,
            data=result.get("data"),
            meta={"interview_id": interview_id}
        )

    except Exception as e:
        logger.error(f"❌ Error getting interview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/interviews/start")
async def start_interview(request: InterviewStartRequest):
    """
    Start an interview and get first question
    STEP 2.2: Interview Start (get first question + TTS audio)

    Expected flow:
    1. Receive interview_id from STEP 2.1 token validation
    2. Transition interview from "scheduled" to "in_progress"
    3. Generate questions using Gemini if not already generated
    4. Return first question
    5. Client calls audio-ai-service to generate TTS audio for question
    """
    try:
        # Start the interview
        result = interview_service.start_interview(
            interview_id=request.interview_id,
            candidate_id=request.candidate_id
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        logger.info(f"✅ Interview {request.interview_id} started successfully")

        return create_response(
            success=True,
            data=result.get("data"),
            meta={"interview_id": request.interview_id}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error starting interview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/interviews/{interview_id}/next-question")
async def get_next_question(interview_id: str, request: NextQuestionRequest = None):
    """
    Get next question for interview - generates dynamically if needed
    STEP 3.1: Get next question (called after submitting response)

    Request body (optional):
    {
        "candidate_id": "uuid" (optional if already in interview context),
        "job_position_id": "uuid" (optional if already in interview context)
    }
    """
    try:
        # Get interview to extract candidate and job info if not provided
        from repositories import InterviewRepository
        interview_repo = InterviewRepository()
        interview = interview_repo.get_interview_by_id(interview_id)

        if not interview:
            raise HTTPException(status_code=404, detail=f"Interview not found: {interview_id}")

        candidate_id = request.candidate_id if request and request.candidate_id else interview.get("candidate_id")
        job_position_id = request.job_position_id if request and request.job_position_id else interview.get("job_position_id")

        result = interview_service.get_next_question(
            interview_id=interview_id,
            candidate_id=candidate_id,
            job_position_id=job_position_id
        )

        # Check if interview is completed (success=False but completed=True)
        if not result.get("success"):
            if result.get("completed"):
                # Interview has reached max questions - this is expected behavior
                logger.info(f"⛔ Interview completed - max questions reached")
                logger.info(f"   Questions asked: {result.get('questions_asked')} / {result.get('max_questions')}")
                # Return completion signal with 'completed' at root level for orchestration-service
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": False,
                        "error": result.get("error"),
                        "completed": True,  # Root level for easy access by orchestration-service
                        "questions_asked": result.get("questions_asked"),
                        "max_questions": result.get("max_questions"),
                        "data": None,
                        "meta": {
                            "interview_id": interview_id
                        }
                    }
                )
            else:
                # Actual error occurred
                logger.error(f"❌ Next question generation error: {result.get('error')}")
                raise HTTPException(status_code=400, detail=result.get("error"))

        return create_response(
            success=True,
            data=result.get("data"),
            meta={"interview_id": interview_id}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting next question: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/interviews/{interview_id}/respond")
async def submit_response(interview_id: str, request: InterviewResponseRequest):
    """
    Submit response to a question
    STEP 3: Answer Submission & Question Generation

    Expected flow:
    1. Receive response text from candidate
    2. Save response to database
    3. Evaluate response using NLP (Gemini)
    4. Return evaluation results
    5. Client calls /next-question to get next question
    """
    try:
        # Support both session_id and question_id for backward compatibility
        session_id = request.session_id or request.question_id
        logger.info(f"📝 Receiving response for session {session_id}")

        from services import NLPEvaluationService
        nlp_service = NLPEvaluationService()

        # Evaluate response using NLP
        evaluation_result = nlp_service.evaluate_response(
            session_id=session_id,
            response_text=request.response_text,
            expected_answer_points=request.expected_answer_points
        )

        if not evaluation_result.get("success"):
            raise HTTPException(status_code=400, detail=evaluation_result.get("error"))

        logger.info(f"✅ Response evaluated - Score: {evaluation_result.get('data', {}).get('score')}")

        return create_response(
            success=True,
            data={
                "message": "Response received and evaluated",
                "interview_id": interview_id,
                "session_id": session_id,
                "evaluation": evaluation_result.get("data")
            },
            meta={"interview_id": interview_id, "session_id": session_id}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error submitting response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/interviews/candidate/{candidate_id}")
async def get_candidate_interviews(candidate_id: str):
    """
    Get all interviews for a candidate
    """
    try:
        result = interview_service.get_candidates_interviews(candidate_id)

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        return create_response(
            success=True,
            data=result.get("data"),
            meta={"candidate_id": candidate_id}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting candidate interviews: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/interviews/{interview_id}/status")
async def get_interview_status(interview_id: str):
    """Get current interview status"""
    try:
        result = interview_service.get_interview(interview_id)

        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error"))

        interview = result.get("data")

        return create_response(
            success=True,
            data={
                "interview_id": interview_id,
                "status": interview.get("status"),
                "started_at": interview.get("started_at"),
                "completed_at": interview.get("completed_at")
            },
            meta={"interview_id": interview_id}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting interview status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
