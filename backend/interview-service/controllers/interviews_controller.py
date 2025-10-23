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
from schemas.interviews import InterviewScheduledResponse
from repositories.interviews_repository import get_interview_by_id

from schemas.interviews import UpdateInterviewStatusRequest, UpdateInterviewStatusResponse
from services.scheduling_service import update_interview_status_service

router = APIRouter()

# ✅ Request model for scheduling
class InterviewScheduleRequest(BaseModel):
    organization_id: str
    job_position_id: str
    candidate_id: str        # points to candidates.id
    interviewer_id: str      # points to users.id
    template_id: str
    mode: str = Field(..., description="chat | audio | video | hybrid")
    scheduled_at: datetime
    duration_minutes: int = 45
    settings: dict | None = None
    create_calendar_event: bool = False


# ✅ Single, clean route with response_model
@router.post("/schedule", response_model=InterviewScheduledResponse)
def schedule_interview(request: InterviewScheduleRequest):
    try:
        result = schedule_interview_service(request)
        return create_response(result)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{id}")
def get_interview(id: str):
    result = get_interview_by_id(id)
    if not result:
        raise HTTPException(status_code=404, detail="Interview not found")
    return create_response(result)

@router.put("/{id}/status", response_model=UpdateInterviewStatusResponse)
def update_interview_status_route(id: str, req: UpdateInterviewStatusRequest):
    try:
        result = update_interview_status_service(id, req.status)
        return create_response(result)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
