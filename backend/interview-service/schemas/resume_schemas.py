from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class FileInfo(BaseModel):
    """Information about a processed file"""
    filename: str
    url: str
    size: int
    status: str  # Can be: "processed", "failed", "duplicate_email"
    extracted_emails: List[str] = []
    extracted_name: Optional[str] = None
    email_count: int = 0
    id: Optional[str] = None  # Candidate ID from database
    candidate_save_error: Optional[str] = None  # Error if candidate save failed

class ResumeUploadResponse(BaseModel):
    """Response for resume upload endpoint"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)

class ResumeUploadData(BaseModel):
    """Data structure for resume upload response"""
    upload_id: str
    status: str
    files_received: int
    files_processed: int
    files: List[FileInfo] = []
    timestamp: str

class APIResponse(BaseModel):
    """Standard API response structure"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)
