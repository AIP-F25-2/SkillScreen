from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional
from datetime import datetime
import uuid

from schemas.interview_schemas import (
    InterviewCreateRequest,
    InterviewCreateResponse,
    InterviewStatusResponse,
    QuestionRequest,
    QuestionResponse,
    AnswerSubmitRequest,
    AnswerSubmitResponse,
    InterviewSummaryResponse
)
from services.orchestration_service import OrchestrationService

router = APIRouter()


@router.post("/interviews", response_model=InterviewCreateResponse)
async def create_interview(request: InterviewCreateRequest):
    """
    Create a new interview session
    
    This endpoint:
    1. Creates interview in database
    2. Generates first question from text-service
    3. Returns interview session details
    """
    try:
        orchestration = OrchestrationService()
        result = await orchestration.create_interview(
            candidate_id=request.candidate_id,
            job_position_id=request.job_position_id,
            interview_type=request.interview_type,
            max_questions=request.max_questions
        )
        
        return InterviewCreateResponse(
            interview_id=result["interview_id"],
            session_id=result["session_id"],
            status="created",
            first_question=result.get("first_question"),
            message="Interview created successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create interview: {str(e)}")


@router.get("/interviews/{interview_id}/status", response_model=InterviewStatusResponse)
async def get_interview_status(interview_id: str):
    """
    Get current status of an interview
    
    Returns:
    - Interview progress
    - Current question number
    - Completion status
    - Processing status
    """
    try:
        orchestration = OrchestrationService()
        status = await orchestration.get_interview_status(interview_id)
        
        return InterviewStatusResponse(**status)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get interview status: {str(e)}")


@router.post("/interviews/{interview_id}/questions", response_model=QuestionResponse)
async def get_next_question(interview_id: str, request: Optional[QuestionRequest] = None):
    """
    Get next question for the interview
    
    This endpoint:
    1. Checks if interview can continue
    2. Generates contextual question from text-service
    3. Returns question with metadata
    """
    try:
        orchestration = OrchestrationService()
        question = await orchestration.get_next_question(
            interview_id=interview_id,
            context=request.context if request else None
        )
        
        return QuestionResponse(**question)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get next question: {str(e)}")


@router.post("/interviews/{interview_id}/answers", response_model=AnswerSubmitResponse)
async def submit_answer(
    interview_id: str,
    request: AnswerSubmitRequest,
    background_tasks: BackgroundTasks
):
    """
    Submit answer to interview question
    
    This endpoint:
    1. Receives text answer and media files
    2. Stores media in media-service
    3. Triggers background processing:
       - Audio analysis (audio-ai-service)
       - Video analysis (video-ai-service)
       - Text evaluation (text-service)
    4. Returns immediate acknowledgment
    """
    try:
        orchestration = OrchestrationService()
        
        # Submit answer and get session details
        result = await orchestration.submit_answer(
            interview_id=interview_id,
            session_id=request.session_id,
            question_id=request.question_id,
            text_answer=request.text_answer,
            media_file_id=request.media_file_id,
            response_time_seconds=request.response_time_seconds
        )
        
        # Trigger background processing if media exists
        if request.media_file_id:
            background_tasks.add_task(
                orchestration.process_media_in_background,
                interview_id=interview_id,
                session_id=request.session_id,
                media_file_id=request.media_file_id
            )
        
        return AnswerSubmitResponse(
            interview_id=interview_id,
            session_id=request.session_id,
            question_id=request.question_id,
            status="accepted",
            processing_status=result.get("processing_status", "pending"),
            message="Answer submitted successfully. Processing in background."
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit answer: {str(e)}")


@router.post("/interviews/{interview_id}/complete")
async def complete_interview(interview_id: str, background_tasks: BackgroundTasks):
    """
    Complete interview and trigger final summary generation
    
    This endpoint:
    1. Marks interview as completed
    2. Triggers background summary generation
    3. Aggregates all analysis results
    4. Generates final recommendation
    """
    try:
        orchestration = OrchestrationService()
        
        # Mark interview as completed
        result = await orchestration.complete_interview(interview_id)
        
        # Trigger summary generation in background
        background_tasks.add_task(
            orchestration.generate_interview_summary,
            interview_id=interview_id
        )
        
        return {
            "interview_id": interview_id,
            "status": "completed",
            "message": "Interview completed. Summary generation in progress.",
            "summary_available": False
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete interview: {str(e)}")


@router.get("/interviews/{interview_id}/summary", response_model=InterviewSummaryResponse)
async def get_interview_summary(interview_id: str):
    """
    Get comprehensive interview summary
    
    Returns:
    - Overall scores
    - Text evaluation results
    - Audio analysis results
    - Video analysis results
    - Final recommendation
    """
    try:
        orchestration = OrchestrationService()
        summary = await orchestration.get_interview_summary(interview_id)
        
        return InterviewSummaryResponse(**summary)
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Interview summary not available: {str(e)}")


@router.get("/interviews/{interview_id}/results")
async def get_detailed_results(interview_id: str):
    """
    Get detailed results including all service responses
    
    Returns comprehensive data from:
    - Text service evaluations
    - Audio AI analysis
    - Video AI analysis
    - All transcripts
    - All scores
    """
    try:
        orchestration = OrchestrationService()
        results = await orchestration.get_detailed_results(interview_id)
        
        return {
            "interview_id": interview_id,
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")


@router.delete("/interviews/{interview_id}")
async def cancel_interview(interview_id: str):
    """
    Cancel an ongoing interview
    """
    try:
        orchestration = OrchestrationService()
        result = await orchestration.cancel_interview(interview_id)
        
        return {
            "interview_id": interview_id,
            "status": "cancelled",
            "message": "Interview cancelled successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel interview: {str(e)}")

