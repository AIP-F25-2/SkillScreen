from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class CandidateData(BaseModel):
    """Candidate extracted from resume"""
    candidate_id: str = Field(..., description="Candidate UUID")
    full_name: str
    email: str
    phone: Optional[str] = None
    resume_url: Optional[str] = None
    skills: Optional[List[str]] = None
    experience_years: Optional[int] = None


class InterviewScheduled(BaseModel):
    """Interview created for candidate"""
    interview_id: str = Field(..., description="Interview UUID")
    candidate_id: str
    candidate_name: str
    candidate_email: str
    status: str = "scheduled"
    scheduled_at: Optional[str] = None


class ResumesUploadedData(BaseModel):
    """Detailed upload response data"""
    upload_id: str = Field(..., description="Unique upload batch ID")
    organization_id: str
    job_position_id: str
    total_files_processed: int
    candidates_created: int
    interviews_scheduled: int
    candidates: List[CandidateData] = []
    interviews: List[InterviewScheduled] = []
    failed_files: Optional[List[str]] = None
    processing_time_seconds: float


class ResumeUploadResponse(BaseModel):
    """Success response for resume upload"""
    success: bool
    message: str
    data: dict = Field(..., description="Upload result data")
    meta: dict = Field(..., description="Metadata with timestamp, version, request_id")


class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    message: str
    error: str
    meta: dict