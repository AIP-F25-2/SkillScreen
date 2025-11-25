from pydantic import BaseModel
from uuid import UUID
from typing import Optional

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