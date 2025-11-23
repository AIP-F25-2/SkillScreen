from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Optional, Dict
from services.assessment_service import AssessmentService
from repositories.assessment_repository import AssessmentRepository
import sys
sys.path.append('/common-service')
from db import UnitOfWork


router = APIRouter(prefix="/v1/assessment", tags=["Assessment"])
assessment_service = AssessmentService()


# ==========================================
# REQUEST/RESPONSE MODELS
# ==========================================

class CustomWeightsRequest(BaseModel):
    """Request model for custom scoring weights"""
    interview_id: str = Field(..., description="Interview UUID")
    weights: Dict[str, float] = Field(
        ..., 
        description="Custom weights (must sum to 1.0)",
        example={"coding": 0.5, "text": 0.2, "audio": 0.15, "video": 0.15}
    )


class AssessmentStatusResponse(BaseModel):
    """Response model for assessment status"""
    interview_id: str
    status: str  # 'not_started', 'processing', 'completed', 'incomplete', 'error'
    has_assessment: bool
    all_services_completed: bool
    message: Optional[str] = None


class AssessmentResultResponse(BaseModel):
    """Response model for assessment results"""
    interview_id: str
    assessment_id: str
    overall_score: float
    soft_skills_score: float
    communication_score: float
    technical_score: Optional[float]
    proctoring_risk_score: float
    recommendation: str
    summary: str
    reviewer_notes: Optional[str]
    evidence_clips: dict
    created_at: str


class ScoreBreakdownResponse(BaseModel):
    """Response model for detailed score breakdown"""
    interview_id: str
    overall_score: float
    component_scores: Dict[str, float]
    service_scores: Dict[str, Dict]
    weights_used: Dict[str, float]


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def _build_assessment_response(assessment: dict) -> AssessmentResultResponse:
    """Convert assessment dict to AssessmentResultResponse"""
    return AssessmentResultResponse(
        interview_id=str(assessment['interview_id']),
        assessment_id=str(assessment['id']),
        overall_score=float(assessment['overall_score']),
        soft_skills_score=float(assessment['soft_skills_score']),
        communication_score=float(assessment['communication_score']),
        technical_score=float(assessment['technical_score']) if assessment['technical_score'] else None,
        proctoring_risk_score=float(assessment['proctoring_risk_score']),
        recommendation=assessment['recommendation'],
        summary=assessment['summary'],
        reviewer_notes=assessment['reviewer_notes'],
        evidence_clips=assessment['evidence_clips'] or {},
        created_at=assessment['created_at'].isoformat()
    )


def _build_generation_response(status: str, interview_id: str, result: dict = None) -> dict:
    """Build assessment generation status response"""
    response = {
        "status": status,
        "interview_id": interview_id,
    }

    if status == 'success':
        response.update({
            "message": "Assessment generated successfully",
            "assessment_id": result['assessment_id'],
            "overall_score": result['overall_score'],
            "recommendation": result['recommendation']
        })
    elif status == 'incomplete':
        response["message"] = "AI services have not completed analysis for all sessions yet"
    elif status == 'already_exists':
        response["message"] = "Assessment already exists for this interview"

    return response


async def _get_or_generate_assessment(interview_id: str) -> AssessmentResultResponse:
    """Get existing assessment or generate new one"""
    with UnitOfWork() as uow:
        repo = AssessmentRepository(uow)
        assessment = repo.get_assessment(interview_id)

        if assessment:
            return _build_assessment_response(assessment)

    # Assessment doesn't exist - generate on-demand
    result = await assessment_service.generate_assessment(interview_id)

    if result['status'] in ['success', 'rejected_cheating']:
        # Fetch the newly created assessment
        with UnitOfWork() as uow:
            repo = AssessmentRepository(uow)
            assessment = repo.get_assessment(interview_id)
            return _build_assessment_response(assessment)
    elif result['status'] == 'incomplete':
        raise HTTPException(
            status_code=202,
            detail="Interview is still being processed by AI services. Please try again in a few minutes."
        )
    else:
        raise HTTPException(
            status_code=500,
            detail=result.get('message', 'Failed to generate assessment')
        )


# ==========================================
# ENDPOINTS
# ==========================================

@router.post("/start/{interview_id}")
async def start_assessment(interview_id: str):
    """
    Manually trigger assessment generation for a completed interview

    - **interview_id**: UUID of the interview

    Returns assessment result or status
    """
    try:
        result = await assessment_service.generate_assessment(interview_id)

        if result['status'] in ['success', 'incomplete', 'already_exists']:
            return _build_generation_response(result['status'], interview_id, result if result['status'] == 'success' else None)
        else:
            raise HTTPException(status_code=400, detail=result.get('message', 'Unknown error'))

    except Exception as e:
        import traceback
        from config.logger import logger
        logger.error("assessment_start_error", interview_id=interview_id, error=str(e), traceback=traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error generating assessment: {str(e)}")


@router.get("/status/{interview_id}", response_model=AssessmentStatusResponse)
async def get_assessment_status(interview_id: str):
    """
    Check assessment status for an interview
    
    - **interview_id**: UUID of the interview
    
    Returns current status of assessment
    """
    try:
        with UnitOfWork() as uow:
            repo = AssessmentRepository(uow)
            
            # Check if assessment exists
            has_assessment = repo.assessment_exists(interview_id)
            
            # Check if all services completed
            all_services_completed = repo.all_services_completed(interview_id)
            
            # Determine status
            if has_assessment:
                status = "completed"
                message = "Assessment has been generated"
            elif all_services_completed:
                status = "processing"
                message = "All AI services completed, assessment will be generated in next scheduled run"
            else:
                status = "incomplete"
                message = "AI services are still processing"
            
            return AssessmentStatusResponse(
                interview_id=interview_id,
                status=status,
                has_assessment=has_assessment,
                all_services_completed=all_services_completed,
                message=message
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking status: {str(e)}")


@router.get("/interview/{interview_id}", response_model=AssessmentResultResponse)
async def get_assessment_by_interview(interview_id: str):
    """
    Get assessment results for a specific interview - generates on-demand if not exists

    **Use Case:** Get assessment for any interview
    - If assessment exists: Returns immediately from database
    - If not exists: Generates assessment and saves to database

    - **interview_id**: UUID of the interview

    Returns complete assessment data
    """
    try:
        return await _get_or_generate_assessment(interview_id)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        from config.logger import logger
        logger.error("get_assessment_by_interview_error", interview_id=interview_id, error=str(e), traceback=traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/scores/{interview_id}", response_model=ScoreBreakdownResponse)
async def get_detailed_scores(interview_id: str):
    """
    Get detailed score breakdown for an interview
    
    - **interview_id**: UUID of the interview
    
    Returns detailed breakdown of all scores
    """
    try:
        with UnitOfWork() as uow:
            repo = AssessmentRepository(uow)
            
            # Get assessment
            assessment = repo.get_assessment(interview_id)
            if not assessment:
                raise HTTPException(status_code=404, detail="Assessment not found")
            
            # Get all AI analyses
            all_analyses = repo.get_all_ai_analysis_for_interview(interview_id)
            
            # Group by service
            audio_analyses = [a for a in all_analyses if a['service_name'] == 'audio-ai-service']
            video_analyses = [a for a in all_analyses if a['service_name'] == 'video-ai-service']
            text_analyses = [a for a in all_analyses if a['service_name'] == 'text-service']
            coding_analyses = [a for a in all_analyses if a['service_name'] == 'coding-service']
            
            # Extract weights from evidence_clips
            evidence_clips = assessment.get('evidence_clips', {})
            weights_used = evidence_clips.get('scoring_weights', {
                "audio": 0.20,
                "video": 0.20,
                "text": 0.20,
                "coding": 0.40 if coding_analyses else 0
            })
            
            # Build response
            return ScoreBreakdownResponse(
                interview_id=str(assessment['interview_id']),
                overall_score=float(assessment['overall_score']),
                component_scores={
                    "soft_skills": float(assessment['soft_skills_score']),
                    "communication": float(assessment['communication_score']),
                    "technical": float(assessment['technical_score']) if assessment['technical_score'] else 0,
                    "proctoring_risk": float(assessment['proctoring_risk_score'])
                },
                service_scores={
                    "audio": {"count": len(audio_analyses), "service": "audio-ai-service"},
                    "video": {"count": len(video_analyses), "service": "video-ai-service"},
                    "text": {"count": len(text_analyses), "service": "text-ai-service"},
                    "coding": {"count": len(coding_analyses), "service": "coding-service"}
                },
                weights_used=weights_used
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving scores: {str(e)}")


@router.get("/candidate/{candidate_id}", response_model=AssessmentResultResponse)
async def get_or_generate_assessment_for_candidate(candidate_id: str):
    """
    Get assessment for a candidate - generates on-demand if not exists

    **Use Case:** Recruiter views candidate profile
    - If assessment exists: Returns immediately from database
    - If not exists: Generates assessment and saves to database

    - **candidate_id**: UUID of the candidate

    Returns complete assessment data
    """
    try:
        with UnitOfWork() as uow:
            # Find the most recent completed interview for this candidate
            from sqlalchemy import select, and_
            from repositories.assessment_repository import interviews_table

            query = select(interviews_table).where(
                and_(
                    interviews_table.c.candidate_id == candidate_id,
                    interviews_table.c.status == 'completed'
                )
            ).order_by(interviews_table.c.completed_at.desc()).limit(1)

            result = uow.session.execute(query).fetchone()

            if not result:
                raise HTTPException(
                    status_code=404,
                    detail="No completed interview found for this candidate"
                )

            interview_id = str(result.id)

        return await _get_or_generate_assessment(interview_id)

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        from config.logger import logger
        logger.error("candidate_assessment_error", candidate_id=candidate_id, error=str(e), traceback=traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/customize-weights", response_model=dict)
async def customize_weights(request: CustomWeightsRequest):
    """
    Set custom scoring weights and regenerate assessment
    
    - **interview_id**: UUID of the interview
    - **weights**: Custom weights dictionary (must sum to 1.0)
    
    Example:
    ```json
    {
        "interview_id": "uuid-here",
        "weights": {
            "coding": 0.5,
            "text": 0.2,
            "audio": 0.15,
            "video": 0.15
        }
    }
    ```
    """
    try:
        # Validate weights sum to 1.0
        total = sum(request.weights.values())
        if abs(total - 1.0) > 0.01:
            raise HTTPException(
                status_code=400, 
                detail=f"Weights must sum to 1.0 (got {total})"
            )
        
        # Validate weight values
        for key, value in request.weights.items():
            if value < 0 or value > 1:
                raise HTTPException(
                    status_code=400,
                    detail=f"Weight for '{key}' must be between 0 and 1 (got {value})"
                )
        
        # Generate assessment with custom weights
        result = await assessment_service.generate_assessment(
            request.interview_id, 
            custom_weights=request.weights
        )
        
        if result['status'] == 'success':
            return {
                "status": "success",
                "message": "Assessment generated with custom weights",
                "interview_id": request.interview_id,
                "weights_used": request.weights,
                "overall_score": result['overall_score'],
                "recommendation": result['recommendation']
            }
        else:
            raise HTTPException(status_code=400, detail=result.get('message', 'Failed to generate'))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error applying custom weights: {str(e)}")