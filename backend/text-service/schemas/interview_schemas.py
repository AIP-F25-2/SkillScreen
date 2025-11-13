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

# Candidate schemas
class CandidateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=50)
    resume_text: Optional[str] = None
    skills: Optional[List[str]] = []
    experience_years: Optional[float] = Field(None, ge=0)
    education: Optional[str] = None

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

class InterviewSummary(BaseModel):
    executive_summary: str
    overall_score: float = Field(..., ge=0, le=10)
    recommendation: Recommendation
    recommendation_reason: str
    technical_assessment: Dict[str, Any] = {}
    communication_assessment: Dict[str, Any] = {}
    cultural_fit: Dict[str, Any] = {}
    strengths: List[str] = []
    areas_for_improvement: List[str] = []
    key_highlights: List[str] = []
    red_flags: List[str] = []
    improvement_tips: List[str] = []
    next_steps: List[str] = []
    interviewer_notes: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.now)

