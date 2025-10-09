# def check_conflicts(candidate_id: str, interviewer_id: str, start_time, duration_minutes: int):
#     """
#     Check if candidate or interviewer has scheduling conflicts.
#     Placeholder: returns False (no conflict).
#     """
#     return False


from fastapi import HTTPException
from repositories.interviews_repository import (
    check_time_conflicts,
    insert_interview_record
)
from datetime import datetime, timedelta
import uuid

def schedule_interview_service(request):
    """Core scheduling logic"""
    # 1️⃣ Validate schedule time (no past date)
    if request.scheduled_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Scheduled time cannot be in the past")

    # 2️⃣ Check for conflicts (candidate/interviewer availability)
    has_conflict = check_time_conflicts(
        candidate_id=request.candidate_id,
        interviewer_id=request.interviewer_id,
        scheduled_at=request.scheduled_at,
        duration=request.duration_minutes
    )

    if has_conflict:
        raise HTTPException(status_code=409, detail="Scheduling conflict detected")

    # 3️⃣ (Stub) Calendar event creation
    calendar_info = None
    if request.create_calendar_event:
        calendar_info = {
            "provider": "google",
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "join_url": "https://meet.google.com/placeholder"
        }

    # 4️⃣ Prepare interview record
    interview_data = {
        "organization_id": request.organization_id,
        "job_position_id": request.job_position_id,
        "candidate_id": request.candidate_id,
        "interviewer_id": request.interviewer_id,
        "template_id": request.template_id,
        "status": "scheduled",
        "mode": request.mode,
        "scheduled_at": request.scheduled_at,
        "settings": {
            "calendar": calendar_info,
            "duration_minutes": request.duration_minutes,
            "timezone": request.settings.get("timezone") if request.settings else "UTC"
        }
    }

    # 5️⃣ Insert record into DB
    created = insert_interview_record(interview_data)
    return created
