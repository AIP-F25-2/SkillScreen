# backend/interview-service/services/calendar_service.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import os
import uuid
from typing import Optional, Dict, Any
from utils.ics import build_ics_event

@dataclass
class CalendarEventRequest:
    interview_id: str
    title: str
    starts_at: datetime
    duration_minutes: int
    organizer_email: str
    attendee_email: str
    location: Optional[str] = None
    description: Optional[str] = None
    timezone_str: Optional[str] = "UTC"   # kept for future expansion

class CalendarService:
    """
    Provider-agnostic calendar helper.
    provider: 'none' (default) | 'google' | 'outlook'
    """
    def __init__(self, provider: Optional[str] = None):
        self.provider = (provider or os.getenv("CALENDAR_PROVIDER", "none")).lower()

    # PUBLIC API --------------------------------------------------------------

    def create_event(self, req: CalendarEventRequest) -> Dict[str, Any]:
        if self.provider == "none":
            return self._create_ics(req)

        if self.provider == "google":
            # TODO: implement real Google Calendar insert (service account or OAuth)
            # return self._google_create(req)
            return self._not_configured("google")

        if self.provider == "outlook":
            # TODO: implement Microsoft Graph create
            # return self._outlook_create(req)
            return self._not_configured("outlook")

        return self._not_configured(self.provider)

    def delete_event(self, interview_id: str, provider_event_id: Optional[str]) -> Dict[str, Any]:
        if self.provider == "none":
            # Nothing persisted externally for ICS-only fallback
            return {"deleted": True, "provider": "ics", "note": "No external event to delete."}

        if self.provider == "google":
            # TODO: call Google Calendar delete
            return self._not_configured("google")

        if self.provider == "outlook":
            # TODO: call Microsoft Graph delete
            return self._not_configured("outlook")

        return self._not_configured(self.provider)

    # INTERNALS ---------------------------------------------------------------

    def _create_ics(self, req: CalendarEventRequest) -> Dict[str, Any]:
        """
        Build a standards-compliant ICS invite. You can store the string
        in interviews.settings->'calendar' or let the frontend download it.
        """
        uid = f"{uuid.uuid4()}@skillscreen"
        dtstart_utc = self._as_utc(req.starts_at)
        dtend_utc = dtstart_utc + timedelta(minutes=req.duration_minutes)

        ics = build_ics_event(
            uid=uid,
            dtstart=dtstart_utc,
            dtend=dtend_utc,
            summary=req.title,
            description=req.description or "",
            organizer=req.organizer_email,
            attendees=[req.attendee_email],
            location=req.location or "Online",
        )

        return {
            "provider": "ics",
            "provider_event_id": uid,
            "ics": ics,
            "starts_at": dtstart_utc.isoformat().replace("+00:00", "Z"),
            "ends_at": dtend_utc.isoformat().replace("+00:00", "Z"),
        }

    def _not_configured(self, which: str) -> Dict[str, Any]:
        return {
            "provider": which,
            "error": f"{which} calendar not configured yet",
            "configured": False,
        }

    @staticmethod
    def _as_utc(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
