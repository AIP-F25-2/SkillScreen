from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class JobPositionCreate(BaseModel):
    """Schema for creating a new job position"""
    organization_id: str = Field(..., description="Organization ID")
    title: str = Field(..., min_length=1, max_length=255, description="Job title")
    description: Optional[str] = Field(None, description="Job description")
    required_skills: Optional[List[str]] = Field(None, description="List of required skills")
    department: Optional[str] = Field(None, max_length=255, description="Department name")
    is_active: Optional[bool] = Field(True, description="Whether the position is active")
    created_by: Optional[str] = Field(None, description="User ID who created the position")

class JobPositionUpdate(BaseModel):
    """Schema for updating a job position"""
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Job title")
    description: Optional[str] = Field(None, description="Job description")
    required_skills: Optional[List[str]] = Field(None, description="List of required skills")
    department: Optional[str] = Field(None, max_length=255, description="Department name")
    is_active: Optional[bool] = Field(None, description="Whether the position is active")

class JobPositionResponse(BaseModel):
    """Schema for job position response"""
    id: str
    organization_id: str
    title: str
    description: Optional[str]
    required_skills: Optional[List[str]]
    department: Optional[str]
    is_active: bool
    created_by: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    deleted_at: Optional[str]

class JobPositionListResponse(BaseModel):
    """Schema for list of job positions"""
    job_positions: List[JobPositionResponse]
    total: int
    limit: int
    offset: int

class APIResponse(BaseModel):
    """Standard API response structure"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


