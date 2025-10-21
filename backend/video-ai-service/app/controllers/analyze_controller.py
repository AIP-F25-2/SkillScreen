from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field

from app.services import analysis_service as svc

router = APIRouter(prefix="", tags=["analyze"])  # keep your existing routes

# --------- Schemas (controller only) ---------
class AnalyzeURLRequest(BaseModel):
    user_id: str = Field(..., description="User folder under uploads/ & processed/")
    video_url: str = Field(..., description="Local/relative path or URL that resolves to uploads/<user_id>/*")


# --------- Endpoints (thin, delegating to service) ---------
@router.get("/status")
def status():
    return svc.svc_status()

@router.post("/reset")
def reset():
    return svc.svc_reset()

@router.post("/analyze-video")
async def analyze_video(
    user_id: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Upload + analyze.
    Saves to:  uploads/<user_id>/<user_id>_<timestamp>.<ext>
    Outputs to: processed/<user_id>/<user_id>_<timestamp>_annotated.<ext> and <user_id>_report.json
    """
    return await svc.svc_analyze_upload(user_id=user_id, file=file)

@router.post("/analyze-url")
def analyze_url(req: AnalyzeURLRequest):
    """
    Analyze an existing video present under uploads/<user_id>/<user_id>_<timestamp>.<ext>
    """
    return svc.svc_analyze_url(user_id=req.user_id, video_url=req.video_url)

@router.get("/reports/{user_id}")
def list_reports(user_id: str):
    """
    List artifacts (reports, annotated videos, thumbnails) for a user.
    """
    return svc.svc_list_reports(user_id)

@router.on_event("startup")
def _startup():
    # Pre-warm (optional); models are lazily ensured on first use too.
    svc.svc_startup_warm()