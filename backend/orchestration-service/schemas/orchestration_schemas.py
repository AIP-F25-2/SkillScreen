from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class NextQuestionRequest(BaseModel):
    """Request when candidate clicks 'Next Question'"""
    interview_id: UUID = Field(..., description="Interview UUID")
    session_id: UUID = Field(..., description="Current session/question UUID")
    media_file_id: UUID = Field(..., description="Media file ID from media-service")
    candidate_response: str = Field(..., description="Candidate's text answer")
    
    class Config:
        json_schema_extra = {
            "example": {
                "interview_id": "d37f8d3d-5c68-5f56-8a9d-59d040850c90",
                "session_id": "f211e428-3aab-4c52-abb3-c3f5f0a957c6",
                "media_file_id": "609f1983-1f85-4f33-96a6-fe67d9ba7742",
                "candidate_response": "I have 5 years of experience in Python..."
            }
        }


class NextQuestionResponse(BaseModel):
    """Response with next question + audio"""
    status: str = Field(..., description="'success' or 'error'")
    next_question_text: str = Field(..., description="Next question text")
    audio_download_url: str = Field(..., description="URL to download TTS audio")
    evaluation_score: Optional[float] = Field(None, description="Score for current answer")
    feedback: Optional[str] = Field(None, description="Feedback on current answer")
    
    # Background processing status
    audio_ai_triggered: bool = Field(..., description="Audio AI analysis started")
    video_ai_triggered: bool = Field(..., description="Video AI analysis started")
    
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "next_question_text": "Can you explain your experience with Docker?",
                "audio_download_url": "http://audio-ai-service:8080/api/tts/download/abc123.mp3",
                "evaluation_score": 85.5,
                "feedback": "Good answer, but could elaborate more on specific projects",
                "audio_ai_triggered": True,
                "video_ai_triggered": True
            }
        }


class GetAssessmentRequest(BaseModel):
    """Request to get final assessment"""
    interview_id: UUID


class GetAssessmentResponse(BaseModel):
    """Assessment response from assessment-service"""
    status: str
    interview_id: str
    assessment_id: str
    overall_score: float
    recommendation: str
    summary: str
    # ... other fields from assessment service