from pydantic import BaseModel, HttpUrl, Field
from typing import Optional
from datetime import datetime

class AudioProcessRequest(BaseModel):
    """Request schema for audio processing"""
    video_url: HttpUrl = Field(..., description="URL of the video to process")
    session_id: Optional[str] = Field(None, description="Interview session ID")
    candidate_id: Optional[str] = Field(None, description="Candidate ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "video_url": "https://example.com/interview_video.mp4",
                "session_id": "session_12345",
                "candidate_id": "candidate_67890"
            }
        }

class AudioProcessResponse(BaseModel):
    """Response schema for audio processing"""
    status: str = Field(..., description="Processing status: success, failed, processing")
    message: str = Field(..., description="Status message")
    video_url: str = Field(..., description="Original video URL")
    transcript: Optional[str] = Field(None, description="Transcribed text")
    duration_seconds: Optional[float] = Field(None, description="Audio duration in seconds")
    word_count: Optional[int] = Field(None, description="Number of words in transcript")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Processing timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Audio processed successfully",
                "video_url": "https://example.com/interview_video.mp4",
                "transcript": "Hello, my name is John...",
                "duration_seconds": 120.5,
                "word_count": 250,
                "timestamp": "2025-10-01T12:00:00"
            }
        }