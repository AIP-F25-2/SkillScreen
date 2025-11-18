from pydantic import BaseModel, HttpUrl, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from uuid import UUID
import os



class TTSRequest(BaseModel):
    """Text-to-speech request"""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to convert to speech")
    voice: Optional[str] = Field("en-US-female", description="Voice ID")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Hello candidate, please tell me about your experience with Python.",
                "voice": "en-US-female",
                "session_id": "interview_123"
            }
        }


class TTSResponse(BaseModel):
    """Text-to-speech response"""
    status: str
    message: str
    filename: str = Field(..., description="Audio filename")  # NEW
    download_url: str = Field(..., description="Full download URL for other services")  # NEW
    text: str
    voice: Optional[str] = None
    duration_seconds: Optional[float] = None
    session_id: Optional[str] = None
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Speech generated successfully",
                "filename": "abc123.mp3",
                "download_url": "http://audio-ai-service:8000/api/v1/tts/download/abc123.mp3",
                "text": "Hello candidate...",
                "voice": "en-US-female",
                "duration_seconds": 3.5,
                "session_id": "interview_123"
            }
        }

class AudioProcessRequest(BaseModel):
    """Request schema for audio/video processing"""
    media_url: str = Field(..., description="Media location: http(s) URL, file:// URL, or local path")
    session_id: Optional[str] = Field(None, description="Interview session ID")
    candidate_id: Optional[str] = Field(None, description="Candidate ID")
    
    @field_validator("media_url")
    @classmethod
    def validate_media_location(cls, v: str) -> str:
        v = (v or "").strip()
        if v.startswith("http://") or v.startswith("https://") or v.startswith("file://"):
            return v
        if os.path.exists(v):
            return v
        raise ValueError("URL must be http(s), file://, or an existing local path")
    
    class Config:
        json_schema_extra = {
            "example": {
                "media_url": "file:///app/audio-ai-service/temp_audio/sample.mp3",
                "session_id": "session_12345",
                "candidate_id": "candidate_67890"
            }
        }


class FillerWord(BaseModel):
    """Individual filler word occurrence"""
    start: float
    end: float
    text: str


class FillerAnalysis(BaseModel):
    """Filler word analysis results"""
    filler_words: Dict[str, Dict[str, Any]] = Field(
        description="Filler words detected with counts and timestamps"
    )
    total_fillers: int = Field(description="Total number of filler words")
    filler_rate_per_minute: float = Field(description="Fillers per minute")
    most_common_fillers: List[Dict[str, Any]] = Field(
        description="Top 5 most common fillers"
    )


class SpeakerAnalysis(BaseModel):
    """Speaker diarization and cheating assessment"""
    num_speakers: int = Field(description="Number of unique speakers detected")
    speakers: List[str] = Field(description="List of speaker IDs")
    speaker_time_percentages: Dict[str, float] = Field(
        description="Percentage of time each speaker talked"
    )
    cheating_flag: bool = Field(description="Whether cheating was detected")
    risk_level: str = Field(description="Cheating risk level: low, medium, high")
    reason: str = Field(description="Explanation for cheating assessment")
    total_speaker_changes: int = Field(description="Number of speaker transitions")


class AudioProcessResponse(BaseModel):
    """Response schema for audio processing"""
    status: str = Field(..., description="Processing status: success, failed, processing")
    message: str = Field(..., description="Status message")
    media_url: str = Field(..., description="Original media URL")  # Changed from video_url
    media_type: Optional[str] = Field(None, description="Detected media type: audio or video")  # NEW
    
    # Optional fields (present on success)
    session_id: Optional[str] = Field(None, description="Interview session ID")
    candidate_id: Optional[str] = Field(None, description="Candidate ID")
    transcript: Optional[str] = Field(None, description="Full transcribed text")
    duration_seconds: Optional[float] = Field(None, description="Audio duration in seconds")
    word_count: Optional[int] = Field(None, description="Number of words in transcript")
    language: Optional[str] = Field(None, description="Detected language")
    
    filler_analysis: Optional[FillerAnalysis] = Field(None, description="Filler word analysis")
    speaker_analysis: Optional[SpeakerAnalysis] = Field(None, description="Speaker analysis")
    
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Processing timestamp")
    processing_time_seconds: Optional[float] = Field(None, description="Total processing time")
    
    # Error field
    error: Optional[str] = Field(None, description="Error message if status is failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Media processed successfully",
                "media_url": "https://example.com/recording.mp3",
                "media_type": "audio",
                "session_id": "session_12345",
                "candidate_id": "candidate_67890",
                "transcript": "Hello, my name is John...",
                "duration_seconds": 120.5,
                "word_count": 250,
                "language": "en",
                "processing_time_seconds": 45.2
            }
        }


class ProcessInterviewAudioRequest(BaseModel):
    """Request schema for interview audio processing"""
    interview_id: UUID = Field(..., description="Interview UUID")
    session_id: UUID = Field(..., description="Session UUID (question)")
    media_file_id: UUID = Field(..., description="Media file UUID")

    
    class Config:
        json_schema_extra = {
            "example": {
                "interview_id": "d37f8d3d-5c68-5f56-8a9d-59d040850c90",
                "session_id": "f211e428-3aab-4c52-abb3-c3f5f0a957c6",
                "media_file_id": "609f1983-1f85-4f33-96a6-fe67d9ba7742"
            }
        }


class ProcessInterviewAudioResponse(BaseModel):
    """Response schema for interview audio processing"""
    status: str = Field(..., description="'accepted' - processing started")
    message: str = Field(..., description="Status message")
    media_file_id: str
    interview_id: str
    session_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "accepted",
                "message": "Audio processing started in background",
                "media_file_id": "609f1983-1f85-4f33-96a6-fe67d9ba7742",
                "interview_id": "d37f8d3d-5c68-5f56-8a9d-59d040850c90",
                "session_id": "f211e428-3aab-4c52-abb3-c3f5f0a957c6",
                "timestamp": "2025-11-06T10:30:00Z"
            }
        }