"""
Pydantic schemas for SkillScreen API request/response validation
"""

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class InterviewType(str, Enum):
    MIXED = "mixed"
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"

class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class Recommendation(str, Enum):
    HIRE = "Hire"
    STRONG_CONSIDER = "Strong Consider"
    CONSIDER = "Consider"
    DO_NOT_HIRE = "Do Not Hire"

class InterviewStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    TERMINATED = "terminated"

# Candidate schemas
class CandidateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=50)
    resume_text: Optional[str] = None
    skills: Optional[List[str]] = []
    experience_years: Optional[float] = Field(None, ge=0)
    education: Optional[str] = None

class CandidateResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str]
    skills: Optional[List[str]]
    experience_years: Optional[float]
    education: Optional[str]
    created_at: datetime

# Job schemas
class JobCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    company: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    requirements: Optional[List[str]] = []
    skills_required: Optional[List[str]] = []
    experience_level: Optional[str] = Field("Mid-level", max_length=50)
    job_type: Optional[str] = Field("Full-time", max_length=50)
    location: Optional[str] = Field(None, max_length=255)
    salary_range: Optional[str] = Field(None, max_length=100)

class JobResponse(BaseModel):
    id: str
    title: str
    company: str
    description: Optional[str]
    requirements: Optional[List[str]]
    skills_required: Optional[List[str]]
    experience_level: Optional[str]
    job_type: Optional[str]
    location: Optional[str]
    salary_range: Optional[str]
    created_at: datetime

# Interview schemas
class InterviewStart(BaseModel):
    candidate_id: str
    job_id: str
    interview_type: InterviewType = InterviewType.MIXED
    difficulty: Difficulty = Difficulty.MEDIUM
    max_questions: int = Field(15, ge=5, le=50)
    target_duration_minutes: int = Field(12, ge=5, le=60)

class InterviewResponse(BaseModel):
    response_text: str = Field(..., min_length=1, max_length=5000)
    response_time_seconds: Optional[float] = Field(None, ge=0)

class InterviewQuestion(BaseModel):
    id: str
    question_index: int
    question_text: str
    question_type: str
    difficulty: str
    round_number: int
    context: Optional[str]
    asked_at: datetime

class ResponseEvaluation(BaseModel):
    overall_score: float = Field(..., ge=0, le=10)
    relevance_score: float = Field(..., ge=0, le=10)
    technical_accuracy_score: float = Field(..., ge=0, le=10)
    communication_score: float = Field(..., ge=0, le=10)
    depth_score: float = Field(..., ge=0, le=10)
    job_fit_score: float = Field(..., ge=0, le=10)
    strengths: List[str] = []
    weaknesses: List[str] = []
    feedback: str
    improvement_tips: List[str] = []
    is_duplicate: bool = False
    is_off_topic: bool = False

class InterviewResponseRecord(BaseModel):
    id: str
    response_text: str
    response_length: int
    evaluation: ResponseEvaluation
    received_at: datetime

class AntiCheatingAnalysis(BaseModel):
    is_duplicate: bool = False
    is_off_topic: bool = False
    should_terminate: bool = False
    duplicate_count: int = 0
    off_topic_count: int = 0
    flags: List[str] = []
    confidence: float = Field(..., ge=0, le=1)

class TechnicalAssessment(BaseModel):
    score: float = Field(..., ge=0, le=10)
    summary: str
    technical_skills_evaluated: List[str] = []
    knowledge_gaps: List[str] = []
    competencies_demonstrated: List[str] = []

class CommunicationAssessment(BaseModel):
    score: float = Field(..., ge=0, le=10)
    summary: str
    clarity_score: float = Field(..., ge=0, le=10)
    structure_score: float = Field(..., ge=0, le=10)
    professionalism_score: float = Field(..., ge=0, le=10)
    engagement_score: float = Field(..., ge=0, le=10)

class CulturalFitAssessment(BaseModel):
    score: float = Field(..., ge=0, le=10)
    summary: str
    alignment_with_role: float = Field(..., ge=0, le=10)
    teamwork_indicators: float = Field(..., ge=0, le=10)
    professional_attitude: float = Field(..., ge=0, le=10)

class InterviewSummary(BaseModel):
    executive_summary: str
    overall_score: float = Field(..., ge=0, le=10)
    recommendation: Recommendation
    recommendation_reason: str
    technical_assessment: TechnicalAssessment
    communication_assessment: CommunicationAssessment
    cultural_fit: CulturalFitAssessment
    strengths: List[str] = []
    areas_for_improvement: List[str] = []
    key_highlights: List[str] = []
    red_flags: List[str] = []
    improvement_tips: List[str] = []
    next_steps: List[str] = []
    interviewer_notes: Optional[str] = None
    generated_at: datetime

class InterviewStatus(BaseModel):
    session_id: str
    status: InterviewStatus
    current_question_index: int
    total_questions_asked: int
    total_responses_received: int
    overall_score: Optional[float]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration_minutes: Optional[float]

class InterviewStartResponse(BaseModel):
    session_id: str
    interview_id: str
    candidate_name: str
    job_title: str
    initial_question: InterviewQuestion
    status: InterviewStatus

class InterviewContinueResponse(BaseModel):
    status: str = "continue"
    next_question: InterviewQuestion
    current_score: float
    anti_cheating_flags: AntiCheatingAnalysis

class InterviewCompleteResponse(BaseModel):
    status: str = "completed"
    summary: InterviewSummary
    termination_reason: str

# File upload schemas
class ResumeUploadResponse(BaseModel):
    filename: str
    file_path: str
    parsed_data: Dict[str, Any]

# Health check schema
class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    services: Dict[str, str]

# Error response schema
class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Audit log schema
class AuditLogEntry(BaseModel):
    action: str
    entity_type: str
    entity_id: str
    user_id: Optional[str] = None
    user_type: Optional[str] = None
    ip_address: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    details: Optional[str] = None
    created_at: datetime

# System configuration schema
class SystemConfig(BaseModel):
    key: str
    value: str
    value_type: str
    description: Optional[str] = None
    is_encrypted: bool = False
