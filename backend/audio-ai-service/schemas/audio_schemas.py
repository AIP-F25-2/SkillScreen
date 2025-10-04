from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any
from datetime import datetime



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
    audio_file_path: Optional[str] = None  # Internal path
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
                "audio_file_path": "temp_audio/abc123.mp3",
                "text": "Hello candidate...",
                "voice": "en-US-female",
                "duration_seconds": 3.5,
                "session_id": "interview_123"
            }
        }


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
    video_url: str = Field(..., description="Original video URL")
    
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
                "message": "Audio processed successfully",
                "video_url": "https://example.com/video.mp4",
                "session_id": "session_12345",
                "candidate_id": "candidate_67890",
                "transcript": "Hello, my name is John...",
                "duration_seconds": 120.5,
                "word_count": 250,
                "language": "en",
                "filler_analysis": {
                    "total_fillers": 8,
                    "filler_rate_per_minute": 4.0
                },
                "speaker_analysis": {
                    "num_speakers": 1,
                    "cheating_flag": False,
                    "risk_level": "low"
                },
                "processing_time_seconds": 45.2
            }
        }