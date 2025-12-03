from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, File, Form, UploadFile
from pydantic import BaseModel, Field, root_validator

from app.services import analysis_service as svc

router = APIRouter(prefix="", tags=["analyze"])


class AnalyzeURLRequest(BaseModel):
    interview_id: UUID = Field(..., description="Identifier for the interview being analyzed")
    session_id: UUID = Field(..., description="Unique session/run identifier under the interview")
    video_url: Optional[str] = Field(None, description="Azure blob URL or relative path under videos/<interview>/<session>/")
    media_id: Optional[UUID] = Field(None, description="Existing media_files.id referencing a recorded video")

    @root_validator(skip_on_failure=True)
    def _ensure_target(cls, values):
        if not values.get("video_url") and not values.get("media_id"):
            raise ValueError("Provide either video_url or media_id")
        return values


# --------- Endpoints (thin, delegating to service) ---------
@router.get("/status")
def status():
    return svc.svc_status()

@router.post("/reset")
def reset():
    return svc.svc_reset()

@router.post("/analyze-video")
async def analyze_video(
    interview_id: UUID = Form(...),
    session_id: UUID = Form(...),
    file: UploadFile = File(...),
):
    """Upload + analyze a new session for an interview."""
    return await svc.svc_analyze_upload(interview_id=str(interview_id), session_id=str(session_id), file=file)

@router.post("/analyze-url")
def analyze_url(req: AnalyzeURLRequest, background_tasks: BackgroundTasks):
    """Analyze an existing blob for a given interview/session."""
    interview_id = str(req.interview_id)
    session_id = str(req.session_id)
    media_id = str(req.media_id) if req.media_id else None

    if media_id:
        svc.validate_media_reference(interview_id, session_id, media_id)

    background_tasks.add_task(
        svc.svc_analyze_url,
        interview_id=interview_id,
        session_id=session_id,
        video_url=req.video_url,
        media_id=media_id,
    )
    return svc.build_accept_response(interview_id, session_id, media_id)

@router.get("/reports/{interview_id}")
def list_reports(interview_id: UUID):
    """List artifacts stored for an interview."""
    return svc.svc_list_reports(str(interview_id))

@router.on_event("startup")
def _startup():
    # Pre-warm (optional); models are lazily ensured on first use too.
    svc.svc_startup_warm()
