"""
Pydantic schemas for interview-related data models
"""

from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

class CandidateCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    resume_text: Optional[str] = None
    skills: Optional[List[str]] = None
    experience_years: Optional[float] = None
    education: Optional[str] = None

class JobCreate(BaseModel):
    title: str
    company: str
    description: Optional[str] = None
    requirements: Optional[List[str]] = None
    skills_required: Optional[List[str]] = None
    experience_level: Optional[str] = None
    job_type: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None

class InterviewStart(BaseModel):
    candidate_id: str
    job_id: str
    interview_type: Optional[str] = "mixed"
    difficulty: Optional[str] = "medium"
    max_questions: Optional[int] = 15
    target_duration_minutes: Optional[int] = 12

class InterviewResponse(BaseModel):
    interview_id: str
    question_id: str
    response_text: str
    response_time_seconds: Optional[float] = None

class InterviewSummary(BaseModel):
    interview_id: str
    executive_summary: Optional[str] = None
    overall_score: Optional[float] = None
    recommendation: Optional[str] = None
    recommendation_reason: Optional[str] = None
    technical_assessment_score: Optional[float] = None
    technical_assessment_summary: Optional[str] = None
    communication_assessment_score: Optional[float] = None
    communication_assessment_summary: Optional[str] = None
    cultural_fit_score: Optional[float] = None
    cultural_fit_summary: Optional[str] = None
    strengths: Optional[List[str]] = None
    areas_for_improvement: Optional[List[str]] = None
    key_highlights: Optional[List[str]] = None
    red_flags: Optional[List[str]] = None
    improvement_tips: Optional[List[str]] = None
    next_steps: Optional[List[str]] = None
    interviewer_notes: Optional[str] = None
