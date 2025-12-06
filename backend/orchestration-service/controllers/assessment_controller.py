from fastapi import APIRouter, HTTPException
from services.assessment_service_client import AssessmentServiceClient
from services.text_service_client import TextServiceClient
from config.logger import logger
from datetime import datetime, timezone
import uuid

router = APIRouter()
assessment_client = AssessmentServiceClient()
text_client = TextServiceClient()


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


@router.post("/{interview_id}/evaluate")
async def evaluate_interview(interview_id: str):
    """
    Evaluate completed interview and get final scores from text-ai-service

    Called after interview is completed to get:
    - Overall score (average of all question evaluations)
    - Strengths (collected from all responses)
    - Areas for improvement
    - Individual question evaluations
    """
    logger.info(f"📊 Evaluating completed interview {interview_id}")

    try:
        # Call text-service to get comprehensive evaluation
        evaluation_result = await text_client.evaluate_interview(interview_id)

        if not evaluation_result.get("success"):
            logger.error(f"❌ Interview evaluation failed: {evaluation_result.get('error')}")
            raise HTTPException(status_code=400, detail=evaluation_result.get("error"))

        evaluation_data = evaluation_result.get("data", {})

        logger.info(f"✅ Interview evaluation complete - Overall Score: {evaluation_data.get('overall_score')}")

        return create_response(
            data={
                "interview_id": interview_id,
                "overall_score": evaluation_data.get("overall_score", 0),
                "total_evaluations": evaluation_data.get("total_evaluations", 0),
                "strengths": evaluation_data.get("strengths", []),
                "areas_for_improvement": evaluation_data.get("areas_for_improvement", []),
                "analyses": evaluation_data.get("analyses", [])
            },
            success=True,
            message="Interview evaluation complete"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Evaluate interview failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))