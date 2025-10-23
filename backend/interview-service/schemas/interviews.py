from pydantic import BaseModel, Field
from typing import Dict, Optional
from datetime import datetime

from enum import Enum

class InterviewScheduledResponse(BaseModel):
    id: str
    status: str
    scheduled_at: datetime
    settings: Optional[Dict] = Field(default_factory=dict)


class InterviewDetailResponse(BaseModel):
    id: str
    organization_id: str
    job_position_id: str
    candidate_id: str
    interviewer_id: str
    template_id: str
    status: str
    mode: str
    scheduled_at: datetime
    settings: Optional[Dict] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

class InterviewStatusEnum(str, Enum):
    scheduled = "scheduled"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"

class UpdateInterviewStatusRequest(BaseModel):
    status: InterviewStatusEnum

class UpdateInterviewStatusResponse(BaseModel):
    id: str
    status: InterviewStatusEnum
    updated_at: datetime
