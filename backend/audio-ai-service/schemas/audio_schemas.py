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
    filename: str = Field(..., description="Audio filename")
    download_url: str = Field(..., description="Full download URL for other services")
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
    media_url: str = Field(..., description="Original media URL")
    media_type: Optional[str] = Field(None, description="Detected media type: audio or video")
    
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


class TranscriptDetail(BaseModel):
    """Individual transcript detail"""
    interview_id: str
    session_id: str
    question_number: Optional[int] = None
    speaker: str
    text: str
    transcription_confidence: float = Field(description="Whisper transcription accuracy (0-1)")
    start_time: float
    end_time: float
    duration_seconds: float
    word_count: int
    word_timestamps: List[Dict[str, Any]] = Field(description="Word-level timestamps with probabilities")
    created_at: datetime


class CandidateTranscriptsResponse(BaseModel):
    """Response for candidate transcripts"""
    candidate_id: str
    candidate_name: Optional[str] = None
    total_sessions: int = Field(description="Total interview questions answered")
    transcripts: List[TranscriptDetail]
    summary: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "candidate_id": "candidate_123",
                "candidate_name": "John Doe",
                "total_sessions": 3,
                "transcripts": [
                    {
                        "interview_id": "uuid1",
                        "session_id": "uuid2",
                        "question_number": 1,
                        "speaker": "candidate",
                        "text": "Hello, my name is John...",
                        "transcription_confidence": 0.92,
                        "start_time": 0.5,
                        "end_time": 120.3,
                        "duration_seconds": 119.8,
                        "word_count": 250,
                        "word_timestamps": [
                            {"word": "Hello", "start": 0.5, "end": 0.8, "probability": 0.95}
                        ],
                        "created_at": "2025-11-14T10:30:00Z"
                    }
                ],
                "summary": {
                    "total_words": 712,
                    "total_speaking_time_seconds": 450.5,
                    "avg_transcription_confidence": 0.91,
                    "avg_words_per_minute": 95.2
                }
            }
        }


class AudioAnalysisDetail(BaseModel):
    """Individual audio analysis result"""
    interview_id: str
    session_id: str
    question_number: Optional[int] = None
    candidate_confidence_score: Optional[float] = Field(description="Candidate speaking confidence (0-10)")
    communication_score: Optional[float] = Field(description="Communication quality score (0-10)")
    filler_analysis: Dict[str, Any]
    vocal_analytics: Dict[str, Any]
    speaker_analysis: Dict[str, Any]
    reading_detection: Optional[Dict[str, Any]] = None
    processing_time_seconds: int
    created_at: datetime


class CandidateAudioAnalysisResponse(BaseModel):
    """Response for candidate audio analysis"""
    candidate_id: str
    candidate_name: Optional[str] = None
    total_sessions: int = Field(description="Total interview questions analyzed")
    analyses: List[AudioAnalysisDetail]
    summary: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "candidate_id": "candidate_123",
                "candidate_name": "John Doe",
                "total_sessions": 3,
                "analyses": [
                    {
                        "interview_id": "uuid1",
                        "session_id": "uuid2",
                        "question_number": 1,
                        "candidate_confidence_score": 7.5,
                        "communication_score": 8.2,
                        "filler_analysis": {
                            "total_fillers": 5,
                            "filler_rate_per_minute": 2.4
                        },
                        "vocal_analytics": {
                            "speaking_rate_wpm": 95,
                            "pitch_mean_hz": 180
                        },
                        "speaker_analysis": {
                            "num_speakers": 1,
                            "cheating_flag": False
                        },
                        "processing_time_seconds": 65,
                        "created_at": "2025-11-14T10:30:00Z"
                    }
                ],
                "summary": {
                    "avg_candidate_confidence": 7.8,
                    "avg_communication_score": 8.1,
                    "total_fillers": 15,
                    "avg_filler_rate_per_minute": 2.1,
                    "cheating_incidents": 0,
                    "avg_speaking_rate_wpm": 92.5
                }
            }
        }