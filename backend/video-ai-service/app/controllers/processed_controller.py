from __future__ import annotations

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from app.services import processed_service as svc

router = APIRouter(prefix="/processed", tags=["processed"])

# ---------- Request models (controller-only) ----------

class CreateProcessRequest(BaseModel):
    user_id: str = Field(..., description="User ID (subfolder under uploads/ and processed/)")
    video_url: str = Field(..., description="Path/URL of the source video (relative or absolute)")

class UpdateMetadataRequest(BaseModel):
    reviewer_notes: Optional[str] = None
    decision: Optional[str] = Field(None, description="e.g., 'advance', 'reject', 'hold'")
    tags: Optional[List[str]] = None
    extra: Optional[Dict[str, Any]] = None

# ---------- Endpoints (thin; delegate to service) ----------

@router.get("/{user_id}/sessions")
def list_sessions(user_id: str):
    return svc.svc_list_sessions(user_id)

@router.get("/{user_id}/{timestamp}/report")
def get_report(user_id: str, timestamp: str):
    data = svc.svc_get_report(user_id, timestamp)
    return JSONResponse(content=data)

@router.get("/{user_id}/{timestamp}/video")
def get_video(user_id: str, timestamp: str):
    vp = svc.svc_get_video_path(user_id, timestamp)
    # Rely on client to set correct content-type; mp4 is most common
    return FileResponse(vp, media_type="video/mp4", filename=vp.split("/")[-1])

@router.get("/{user_id}/{timestamp}/thumbnails")
def list_thumbnails(user_id: str, timestamp: str):
    return svc.svc_list_thumbnails(user_id, timestamp)

@router.get("/{user_id}/reports")
def list_reports(user_id: str, include_summary: bool = Query(True)):
    return svc.svc_list_reports(user_id, include_summary=include_summary)

@router.post("")
def create_process(req: CreateProcessRequest):
    return svc.svc_create_process(req.user_id, req.video_url)

@router.patch("/{user_id}/{timestamp}/metadata")
def update_metadata(user_id: str, timestamp: str, patch: UpdateMetadataRequest):
    return svc.svc_update_metadata(user_id, timestamp, patch.model_dump(exclude_none=True))

@router.delete("/delete_by_user_id_and_session/{user_id}/{timestamp}")
def delete_session(user_id: str, timestamp: str, purge_thumbnails: bool = True):
    return svc.svc_delete_session(user_id, timestamp, purge_thumbnails=purge_thumbnails)

@router.post("/{user_id}/{timestamp}/reprocess")
def reprocess_session(user_id: str, timestamp: str):
    return svc.svc_reprocess_session(user_id, timestamp)

class DeleteByNameRequest(BaseModel):
    name: str = Field(..., description="Exact filename under processed/<user_id>/")
    purge_thumbnails: bool = True
    delete_upload: bool = False

class DeleteByURLRequest(BaseModel):
    video_url: str = Field(..., description="URL or filename that contains <user>_<timestamp>.<ext>")
    purge_thumbnails: bool = True
    delete_upload: bool = False

class DeleteUploadOnlyRequest(BaseModel):
    name_or_url: str = Field(..., description="Exact filename or URL under uploads/<user_id>/")

@router.delete("/delete_by_name/{user_id}")
def delete_by_name(user_id: str, req: DeleteByNameRequest):
    """
    Delete processed artifacts by exact filename in processed/<user_id>/.
    If the filename contains a timestamp, counterpart report/video is also removed.
    """
    return svc.svc_delete_by_name(
        user_id=user_id,
        name=req.name,
        purge_thumbnails=req.purge_thumbnails,
        delete_upload=req.delete_upload
    )

@router.delete("/delete_by_url/{user_id}")
def delete_by_url(user_id: str, req: DeleteByURLRequest):
    """
    Delete processed artifacts by the source URL/filename (infers <timestamp>).
    Optionally delete the original uploaded source.
    """
    return svc.svc_delete_by_url(
        user_id=user_id,
        video_url=req.video_url,
        purge_thumbnails=req.purge_thumbnails,
        delete_upload=req.delete_upload
    )