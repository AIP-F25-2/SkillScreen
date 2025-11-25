from fastapi import APIRouter, HTTPException
from services.assessment_service_client import AssessmentServiceClient
from config.logger import logger

router = APIRouter()
assessment_client = AssessmentServiceClient()

@router.get("/{interview_id}")
async def get_assessment(interview_id: str):
    """Get final assessment for interview"""
    logger.info(f"📊 Getting assessment for {interview_id}")
    
    try:
        result = await assessment_client.get_assessment(interview_id)
        logger.info(f"✅ Assessment retrieved")
        return result
    except Exception as e:
        logger.error(f"❌ Get assessment failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))