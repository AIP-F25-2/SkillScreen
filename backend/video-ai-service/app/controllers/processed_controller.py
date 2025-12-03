from __future__ import annotations

from typing import List, Optional
from html import escape
from uuid import UUID

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.services import processed_service as svc

router = APIRouter(prefix="/processed", tags=["processed"])


class UpdateSessionRequest(BaseModel):
    reviewer_notes: Optional[str] = Field(None, description="Reviewer notes or comments")
    decision: Optional[str] = Field(None, description="Decision flag e.g. approve/reject/hold")
    tags: Optional[List[str]] = Field(None, description="List of tags applied to this session")
    status: Optional[str] = Field(None, description="Session processing status")


@router.get("/{interview_id}/sessions")
def list_sessions(interview_id: UUID):
    return svc.svc_list_sessions(str(interview_id))


@router.get("/{interview_id}/{session_id}")
def get_session(interview_id: UUID, session_id: UUID, include_report: bool = Query(True)):
    return svc.svc_get_session(str(interview_id), str(session_id), include_report=include_report)


@router.get("/{interview_id}/{session_id}/summary")
def get_summary(interview_id: UUID, session_id: UUID):
    return svc.svc_get_summary(str(interview_id), str(session_id))


@router.get("/{interview_id}/{session_id}/report")
def get_report(interview_id: UUID, session_id: UUID):
    return svc.svc_get_report(str(interview_id), str(session_id))


@router.get("/{interview_id}/{session_id}/video")
def get_video(interview_id: UUID, session_id: UUID):
    return svc.svc_get_video_url(str(interview_id), str(session_id))


@router.get("/{interview_id}/{session_id}/thumbnails")
def get_thumbnails(interview_id: UUID, session_id: UUID):
    return svc.svc_get_thumbnails(str(interview_id), str(session_id))


@router.get("/{interview_id}/{session_id}/thumbnails/view", response_class=HTMLResponse)
def view_thumbnails(interview_id: UUID, session_id: UUID) -> HTMLResponse:
    iid = str(interview_id)
    sid = str(session_id)
    payload = svc.svc_get_thumbnails(iid, sid)
    thumbs = payload.get("thumbnails") or []
    styles = """
    <style>
      body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background:#0f172a; color:#e2e8f0; padding:2rem; }
      h1 { margin-top:0; }
      .meta { margin-bottom:1rem; color:#94a3b8; }
      .thumb-grid { display:grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap:1rem; }
      .thumb-card { background:rgba(15,23,42,0.7); border:1px solid rgba(148,163,184,0.3); border-radius:12px; padding:0.75rem; box-shadow:0 10px 25px rgba(15,23,42,0.35); }
      .thumb-card img { width:100%; border-radius:8px; object-fit:cover; background:#020617; }
      .thumb-card code { display:block; margin-top:0.5rem; white-space:pre-wrap; word-break:break-all; color:#a5b4fc; font-size:0.85rem; }
      .empty { padding:1.5rem; background:rgba(15,23,42,0.7); border-radius:12px; border:1px dashed rgba(148,163,184,0.4); text-align:center; }
      a { color:#38bdf8; text-decoration:none; }
    </style>
    """
    header = f"<h1>Thumbnails for interview {escape(iid)} / session {escape(sid)}</h1>"
    if not thumbs:
        body = f"{styles}{header}<div class='meta'>No thumbnails stored for this session.</div><div class='empty'>No thumbnails available.</div>"
        return HTMLResponse(content=body)

    cards = []
    for idx, item in enumerate(thumbs, 1):
        blob = escape(item.get("blob") or f"thumb-{idx}")
        url = item.get("url")
        if url:
            safe_url = escape(url)
            img_html = f'<a href="{safe_url}" target="_blank" rel="noopener"><img src="{safe_url}" alt="{blob}"></a>'
        else:
            img_html = "<div class='empty'>No SAS URL available for this thumbnail.</div>"
        cards.append(f"<div class='thumb-card'>{img_html}<code>{blob}</code></div>")
    grid = "<div class='thumb-grid'>" + "".join(cards) + "</div>"
    body = f"{styles}{header}<div class='meta'>Total thumbnails: {len(thumbs)}</div>{grid}"
    return HTMLResponse(content=body)


@router.patch("/{interview_id}/{session_id}")
def update_session(interview_id: UUID, session_id: UUID, patch: UpdateSessionRequest):
    return svc.svc_update_metadata(
        str(interview_id),
        str(session_id),
        reviewer_notes=patch.reviewer_notes,
        decision=patch.decision,
        tags=patch.tags,
        status=patch.status,
    )


@router.delete("/{interview_id}/{session_id}")
def delete_session(interview_id: UUID, session_id: UUID, delete_blobs: bool = True):
    return svc.svc_delete_session(str(interview_id), str(session_id), delete_blobs=delete_blobs)


@router.delete("/{interview_id}/{session_id}/report")
def delete_report_blob(interview_id: UUID, session_id: UUID):
    return svc.svc_delete_report_blob(str(interview_id), str(session_id))


@router.delete("/{interview_id}/{session_id}/video")
def delete_video_blob(interview_id: UUID, session_id: UUID):
    return svc.svc_delete_video_blob(str(interview_id), str(session_id))


@router.post("/{interview_id}/{session_id}/reprocess")
def reprocess_session(interview_id: UUID, session_id: UUID):
    return svc.svc_reprocess_session(str(interview_id), str(session_id))
