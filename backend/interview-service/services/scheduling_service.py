# def check_conflicts(candidate_id: str, interviewer_id: str, start_time, duration_minutes: int):
#     """
#     Check if candidate or interviewer has scheduling conflicts.
#     Placeholder: returns False (no conflict).
#     """
#     return False

from fastapi import HTTPException
from datetime import datetime, timezone, timedelta
import uuid

from repositories.interviews_repository import update_interview_status
from fastapi import HTTPException

from repositories.interviews_repository import (
    check_time_conflicts,
    insert_interview_record,
    verify_fk_belong_to_org,
)

def _to_utc(dt: datetime) -> datetime:
    """Return a timezone-aware UTC datetime."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def schedule_interview_service(request):
    # ---- 1) Normalize datetimes to UTC (FIX for naive vs aware) ----
    scheduled_at_utc = _to_utc(request.scheduled_at)
    now_utc = datetime.now(timezone.utc)

    if scheduled_at_utc <= now_utc:
        raise HTTPException(status_code=400, detail="scheduled_at must be in the future (UTC)")

    # Optional: compute end time if your conflict checker needs a window
    duration = (request.duration_minutes or 45)
    end_at_utc = scheduled_at_utc + timedelta(minutes=duration)

    # ---- 2) Verify FK / same-org coherence ----
    ok, msg = verify_fk_belong_to_org(
        org_id=request.organization_id,
        job_position_id=request.job_position_id,
        candidate_id=request.candidate_id,
        interviewer_id=request.interviewer_id,
        template_id=request.template_id
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    # ---- 3) Conflict checks (pass UTC times) ----
    has_conflict = check_time_conflicts(
        org_id=request.organization_id,
        candidate_id=request.candidate_id,
        interviewer_id=request.interviewer_id,
        scheduled_at=scheduled_at_utc,
        duration=duration,
        # if your repo supports end time, pass end_at_utc too
        # end_at=end_at_utc,
    )
    if has_conflict:
        raise HTTPException(status_code=409, detail="Scheduling conflict detected")

    # ---- 4) Calendar stub (unchanged) ----
    calendar_info = None
    if request.create_calendar_event:
        calendar_info = {
            "provider": request.settings.get("calendar_provider") if request.settings else "google",
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "join_url": "https://meet.placeholder/abc-defg-hij"
        }

    # ---- 5) Build payload using UTC datetime ----
    interview_data = {
        "organization_id": request.organization_id,
        "job_position_id": request.job_position_id,
        "candidate_id": request.candidate_id,
        "interviewer_id": request.interviewer_id,
        "template_id": request.template_id,
        "status": "scheduled",
        "mode": request.mode,                     # "chat" | "audio" | "video" | "hybrid"
        "scheduled_at": scheduled_at_utc,         # <-- use UTC-aware value
        "settings": {
            "calendar": calendar_info,
            "duration_minutes": duration,
            "timezone": (request.settings or {}).get("timezone", "UTC")
        }
    }

    # ---- 6) Insert row and return ----
    created = insert_interview_record(interview_data)
    return created

def update_interview_status_service(interview_id: str, new_status: str):
    result = update_interview_status(interview_id, new_status)
    if not result:
        raise HTTPException(status_code=404, detail="Interview not found")
    return result

