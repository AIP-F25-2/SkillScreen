from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, Dict

class NextQuestionRequest(BaseModel):
    interview_id: UUID
    session_id: UUID
    question_id: str
    candidate_response: str
    response_time_seconds: float = 0.0

class NextQuestionResponse(BaseModel):
    status: str
    next_question_text: Optional[str] = None
    next_question_id: Optional[str] = None
    audio_download_url: Optional[str] = None
    evaluation_score: Optional[float] = None
    feedback: Optional[str] = None
    summary: Optional[Dict] = None
    audio_ai_triggered: bool = False
    video_ai_triggered: bool = False
    error: Optional[str] = None