from fastapi import APIRouter, HTTPException
from schemas.orchestration_schemas import (
    NextQuestionRequest,
    NextQuestionResponse,
    GetAssessmentRequest
)
from services.orchestration_service import OrchestrationService
from config.logger import logger
import httpx
from config.settings import settings

router = APIRouter(prefix="/api/orchestration", tags=["Orchestration"])

orchestration_service = OrchestrationService()


@router.post("/next-question", response_model=NextQuestionResponse)
async def handle_next_question(request: NextQuestionRequest):
    """
    Handle 'Next Question' button click
    
    Flow:
    1. Evaluate current response (text-service)
    2. Generate next question (text-service)
    3. Generate TTS audio (audio-service)
    4. Trigger background AI analysis (audio-ai + video-ai)
    5. Return next question + audio to frontend
    """
    logger.info(f"📥 Received next-question request for interview {request.interview_id}")
    
    try:
        result = await orchestration_service.process_next_question(
            interview_id=str(request.interview_id),
            session_id=str(request.session_id),
            media_file_id=str(request.media_file_id),
            candidate_response=request.candidate_response
        )
        
        if result.status == "error":
            raise HTTPException(status_code=500, detail=result.error)
        
        return result
    
    except Exception as e:
        logger.error(f"❌ Next question failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assessment/{interview_id}")
async def get_assessment(interview_id: str):
    """
    Get final assessment for completed interview
    
    Calls assessment-service to get/generate assessment
    """
    url = f"{settings.ASSESSMENT_SERVICE_URL}/v1/assessment/interview/{interview_id}"
    
    try:
        logger.info(f"📤 Fetching assessment for interview {interview_id}")
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ Assessment retrieved successfully")
            return data
    
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Assessment not found or interview not completed")
        elif e.response.status_code == 202:
            raise HTTPException(status_code=202, detail="Assessment is still being generated")
        else:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    
    except Exception as e:
        logger.error(f"❌ Failed to get assessment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
