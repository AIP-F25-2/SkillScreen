# def check_conflicts(candidate_id: str, interviewer_id: str, start_time, duration_minutes: int):
#     """
#     Check if candidate or interviewer has scheduling conflicts.
#     Placeholder: returns False (no conflict).
#     """
#     return False

from fastapi import HTTPException
from datetime import datetime, timezone
import uuid

from repositories.interviews_repository import (
    check_time_conflicts,
    insert_interview_record,
    verify_fk_belong_to_org,   # NEW: light FK/org checks to help beginners
)

def schedule_interview_service(request):
    # 1) Basic time sanity
    if request.scheduled_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Scheduled time cannot be in the past")

    # 2) Verify foreign keys exist & belong to same org (helps avoid 500s from FK errors)
    ok, msg = verify_fk_belong_to_org(
        org_id=request.organization_id,
        job_position_id=request.job_position_id,
        candidate_id=request.candidate_id,   # candidates.id
        interviewer_id=request.interviewer_id,  # users.id
        template_id=request.template_id
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    # 3) Conflict checks (candidate or interviewer busy)
    has_conflict = check_time_conflicts(
        org_id=request.organization_id,
        candidate_id=request.candidate_id,
        interviewer_id=request.interviewer_id,
        scheduled_at=request.scheduled_at,
        duration=request.duration_minutes,
    )
    if has_conflict:
        raise HTTPException(status_code=409, detail="Scheduling conflict detected")

    # 4) (Optional) calendar stub
    calendar_info = None
    if request.create_calendar_event:
        calendar_info = {
            "provider": request.settings.get("calendar_provider") if request.settings else "google",
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "join_url": "https://meet.placeholder/abc-defg-hij"
        }

    # 5) Build payload to insert
    interview_data = {
        "organization_id": request.organization_id,
        "job_position_id": request.job_position_id,
        "candidate_id": request.candidate_id,     # candidates.id
        "interviewer_id": request.interviewer_id, # users.id
        "template_id": request.template_id,
        "status": "scheduled",
        "mode": request.mode,
        "scheduled_at": request.scheduled_at,
        "settings": {
            "calendar": calendar_info,
            "duration_minutes": request.duration_minutes,
            "timezone": (request.settings or {}).get("timezone", "UTC")
        }
    }

    # 6) Insert row → return minimal view
    created = insert_interview_record(interview_data)
    return created
