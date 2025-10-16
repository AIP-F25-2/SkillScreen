# from fastapi import APIRouter, Depends
# from interview import create_response

# router = APIRouter()

# @router.post("/schedule")
# def schedule_interview():
#     """Schedule a new interview (MVP placeholder)"""
#     return create_response({"message": "Schedule interview - not yet implemented"})

# @router.get("/{interview_id}")
# def get_interview(interview_id: str):
#     """Fetch interview by ID (MVP placeholder)"""
#     return create_response({"message": f"Get interview {interview_id} - not yet implemented"})

# @router.put("/{interview_id}/status")
# def update_interview_status(interview_id: str):
#     """Update interview status (MVP placeholder)"""
#     return create_response({"message": f"Update status for {interview_id} - not yet implemented"})

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from services.scheduling_service import schedule_interview_service
from utils.response import create_response

router = APIRouter()

class InterviewScheduleRequest(BaseModel):
    organization_id: str
    job_position_id: str
    candidate_id: str        # ← now points to candidates.id
    interviewer_id: str      # ← users.id
    template_id: str
    mode: str = Field(..., description="chat | audio | video | hybrid")
    scheduled_at: datetime
    duration_minutes: int = 45
    settings: dict | None = None
    create_calendar_event: bool = False

@router.post("/schedule")
def schedule_interview(request: InterviewScheduleRequest):
    try:
        result = schedule_interview_service(request)
        return create_response(result)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
