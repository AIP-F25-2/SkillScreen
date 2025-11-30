from fastapi import APIRouter, HTTPException
from config import logger
from services import QuestionGenerationService, NLPEvaluationService
from schemas import QuestionGenerationRequest, QuestionEvaluationRequest

router = APIRouter()
question_gen_service = QuestionGenerationService()
nlp_service = NLPEvaluationService()


def create_response(success: bool, data=None, error=None, meta=None):
    """Standardized response format"""
    return {
        "success": success,
        "data": data,
        "error": error,
        "meta": meta or {}
    }


@router.post("/api/questions/generate")
async def generate_questions(request: QuestionGenerationRequest):
    """
    Generate interview questions using AI
    Called from STEP 2.2 after interview starts
    """
    try:
        logger.info(f"🔄 Generating {request.num_questions} questions for interview {request.interview_id}")

        result = question_gen_service.generate_interview_questions(
            interview_id=request.interview_id,
            candidate_id=request.candidate_id,
            job_position_id=request.job_position_id,
            num_questions=request.num_questions
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        logger.info(f"✅ Generated {len(result.get('data', {}).get('questions', []))} questions")

        return create_response(
            success=True,
            data=result.get("data"),
            meta={"interview_id": request.interview_id}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating questions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/questions/evaluate")
async def evaluate_response(request: QuestionEvaluationRequest):
    """
    Evaluate a candidate's response using NLP
    Called from STEP 3 after receiving response
    """
    try:
        # Support both session_id and question_id for backward compatibility
        session_id = request.session_id or request.question_id
        logger.info(f"🔍 Evaluating response for session {session_id}")

        result = nlp_service.evaluate_response(
            session_id=session_id,
            response_text=request.response_text,
            expected_answer_points=request.expected_answer_points
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        logger.info(f"✅ Evaluation complete - Score: {result.get('data', {}).get('score')}")

        return create_response(
            success=True,
            data=result.get("data"),
            meta={"session_id": session_id}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error evaluating response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/interviews/{interview_id}/evaluate")
async def evaluate_interview(interview_id: str):
    """
    Evaluate all responses for an interview and calculate overall score
    Called at end of interview
    """
    try:
        logger.info(f"📊 Evaluating interview {interview_id}")

        result = nlp_service.evaluate_interview(interview_id)

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        logger.info(f"✅ Interview evaluation complete - Overall Score: {result.get('data', {}).get('overall_score')}")

        return create_response(
            success=True,
            data=result.get("data"),
            meta={"interview_id": interview_id}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error evaluating interview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session (question) details"""
    try:
        from repositories import QuestionRepository
        question_repo = QuestionRepository()
        session = question_repo.get_session_by_id(session_id)

        if not session:
            raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

        return create_response(
            success=True,
            data=session,
            meta={"session_id": session_id}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
