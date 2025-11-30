from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional


# Token Validation Schemas
class TokenValidationData(BaseModel):
    """Data returned when token is validated"""
    interview_id: str = Field(..., description="Interview UUID")
    candidate_id: str = Field(..., description="Candidate UUID")
    candidate_name: str
    candidate_email: str
    organization_id: str
    job_position_id: str
    status: str = Field(default="scheduled", description="Current interview status")
    scheduled_at: Optional[str] = None


class TokenValidationResponse(BaseModel):
    """Response for token validation"""
    success: bool
    message: str
    data: dict = Field(..., description="Interview details")
    meta: dict = Field(..., description="Metadata with timestamp, version, request_id")


# Interview Start Schemas
class QuestionData(BaseModel):
    """Interview question with audio"""
    question_id: Optional[str] = None
    question_number: int = Field(..., description="Question sequence number")
    question_text: str
    audio_url: Optional[str] = None
    estimated_answer_time: int = Field(default=60, description="Time in seconds to answer")
    follow_up_enabled: bool = Field(default=False, description="Allow follow-up questions")


class InterviewStartData(BaseModel):
    """Data returned when interview starts"""
    interview_id: str
    question: QuestionData
    interview_settings: dict = Field(default={}, description="Interview config (mode, difficulty, etc)")
    estimated_duration_minutes: int = Field(default=12, description="Total estimated duration")


class InterviewStartResponse(BaseModel):
    """Response for interview start"""
    success: bool
    message: str
    data: InterviewStartData
    meta: dict


# Legacy/Backward Compatibility
class ValidateTokenRequest(BaseModel):
    token: str

class StartInterviewRequest(BaseModel):
    candidate_id: str
    job_id: str
    interview_type: str = "mixed"
    difficulty: str = "medium"
    max_questions: int = 10

class StartInterviewResponse(BaseModel):
    session_id: str
    interview_id: str
    initial_question: str
    question_id: str
    audio_download_url: str
    status: str