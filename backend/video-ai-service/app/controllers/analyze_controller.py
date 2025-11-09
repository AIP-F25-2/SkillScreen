from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, File, Form, UploadFile
from pydantic import BaseModel, Field

from app.services import analysis_service as svc

router = APIRouter(prefix="", tags=["analyze"])


class AnalyzeURLRequest(BaseModel):
    interview_id: UUID = Field(..., description="Identifier for the interview being analyzed")
    session_id: UUID = Field(..., description="Unique session/run identifier under the interview")
    video_url: str = Field(..., description="Azure blob URL or relative path under videos/<interview>/<session>/")


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
def analyze_url(req: AnalyzeURLRequest):
    """Analyze an existing blob for a given interview/session."""
    return svc.svc_analyze_url(interview_id=str(req.interview_id), session_id=str(req.session_id), video_url=req.video_url)

@router.get("/reports/{interview_id}")
def list_reports(interview_id: UUID):
    """List artifacts stored for an interview."""
    return svc.svc_list_reports(str(interview_id))

@router.on_event("startup")
def _startup():
    # Pre-warm (optional); models are lazily ensured on first use too.
    svc.svc_startup_warm()
