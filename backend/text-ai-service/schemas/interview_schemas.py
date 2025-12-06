from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class QuestionResponse(BaseModel):
    """Question response schema"""
    id: str
    interview_id: str
    question_number: int
    question_text: str
    question_type: str
    difficulty_level: str
    status: str

    class Config:
        from_attributes = True


class InterviewStartRequest(BaseModel):
    """Interview start request schema"""
    interview_id: str
    candidate_id: str


class NextQuestionRequest(BaseModel):
    """Next question request schema"""
    candidate_id: Optional[str] = None
    job_position_id: Optional[str] = None


class InterviewResponseRequest(BaseModel):
    """Interview response submission schema"""
    interview_id: str
    question_id: Optional[str] = None  # Deprecated, use session_id
    session_id: Optional[str] = None
    response_text: str
    response_audio_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    expected_answer_points: Optional[List[str]] = None


class InterviewResponse(BaseModel):
    """Interview response schema"""
    id: str
    interview_id: str
    question_id: str
    question_text: str
    response_text: str
    response_audio_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    confidence_score: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class InterviewDetailsResponse(BaseModel):
    """Interview details with questions"""
    interview: Dict[str, Any]
    questions: List[QuestionResponse]
    total_questions: int

    class Config:
        from_attributes = True
