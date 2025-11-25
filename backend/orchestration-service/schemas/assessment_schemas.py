from pydantic import BaseModel
from typing import Optional, Dict

class AssessmentResponse(BaseModel):
    interview_id: str
    overall_score: float
    recommendation: str
    summary: str