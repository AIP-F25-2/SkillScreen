from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class InterviewCreateRequest(BaseModel):
    """Request to create a new interview"""
    candidate_id: str = Field(..., description="Candidate UUID")
    job_position_id: str = Field(..., description="Job position UUID")
    interview_type: Optional[str] = Field("mixed", description="Interview type: technical, behavioral, mixed")
    max_questions: Optional[int] = Field(15, description="Maximum number of questions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "candidate_id": "550e8400-e29b-41d4-a716-446655440000",
                "job_position_id": "660e8400-e29b-41d4-a716-446655440001",
                "interview_type": "mixed",
                "max_questions": 15
            }
        }


class InterviewCreateResponse(BaseModel):
    """Response after creating interview"""
    interview_id: str
    session_id: str
    status: str
    first_question: Optional[Dict[str, Any]] = None
    message: str


class InterviewStatusResponse(BaseModel):
    """Interview status information"""
    interview_id: str
    status: str = Field(..., description="Status: scheduled, in_progress, completed, cancelled")
    current_question_number: int
    total_questions_asked: int
    max_questions: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    processing_status: Optional[str] = None


class QuestionRequest(BaseModel):
    """Request for next question (optional context)"""
    context: Optional[Dict[str, Any]] = None


class QuestionResponse(BaseModel):
    """Question details"""
    question_id: str
    session_id: str
    question_text: str
    question_number: int
    question_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AnswerSubmitRequest(BaseModel):
    """Request to submit answer"""
    session_id: str = Field(..., description="Question session UUID")
    question_id: str = Field(..., description="Question UUID")
    text_answer: str = Field(..., description="Text answer from candidate")
    media_file_id: Optional[str] = Field(None, description="Media file UUID if video/audio recorded")
    response_time_seconds: Optional[float] = Field(None, description="Time taken to answer")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "770e8400-e29b-41d4-a716-446655440002",
                "question_id": "880e8400-e29b-41d4-a716-446655440003",
                "text_answer": "I have 5 years of experience in Python development...",
                "media_file_id": "990e8400-e29b-41d4-a716-446655440004",
                "response_time_seconds": 45.5
            }
        }


class AnswerSubmitResponse(BaseModel):
    """Response after submitting answer"""
    interview_id: str
    session_id: str
    question_id: str
    status: str
    processing_status: str
    message: str


class InterviewSummaryResponse(BaseModel):
    """Comprehensive interview summary"""
    interview_id: str
    candidate_id: str
    candidate_name: Optional[str] = None
    job_title: Optional[str] = None
    
    # Overall scores
    overall_score: Optional[float] = None
    recommendation: Optional[str] = None
    
    # Text evaluation summary
    text_evaluation: Optional[Dict[str, Any]] = None
    
    # Audio analysis summary
    audio_analysis: Optional[Dict[str, Any]] = None
    
    # Video analysis summary
    video_analysis: Optional[Dict[str, Any]] = None
    
    # Interview metadata
    total_questions: int
    total_answers: int
    duration_minutes: Optional[float] = None
    completion_rate: Optional[float] = None
    
    # Timestamps
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    summary_generated_at: Optional[datetime] = None
    
    # Detailed assessments
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    red_flags: Optional[List[str]] = None
    next_steps: Optional[List[str]] = None

