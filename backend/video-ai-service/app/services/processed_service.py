from __future__ import annotations

import os
from typing import Any, Dict, Optional, Sequence, List

from fastapi import HTTPException

from app.helpers.azure_blob import azure_blob, BlobReference
from app.repositories.video_ai_repository import VideoAIRepository
from app.services import analysis_service as analysis_svc
from app.config import settings

_repo = VideoAIRepository()
_REPORT_SUMMARY_EXCLUDE = {"events", "thumbnails_blobs","segments"}


def _ensure_run(interview_id: str, session_id: str) -> Dict[str, Any]:
    row = _repo.get_run(interview_id, session_id)
    if not row:
        raise HTTPException(404, "Session not found")
    return row


def svc_list_sessions(interview_id: str) -> Dict[str, Any]:
    return {"interview_id": interview_id, "sessions": _repo.list_runs(interview_id)}


def svc_get_session(interview_id: str, session_id: str, include_report: bool = True) -> Dict[str, Any]:
    row = _ensure_run(interview_id, session_id)
    if not include_report:
        row = {k: v for k, v in row.items() if k != "report"}
    return row


def svc_get_report(interview_id: str, session_id: str) -> Dict[str, Any]:
    row = _ensure_run(interview_id, session_id)
    report = row.get("report")
    if report is None:
        raise HTTPException(404, "Report not stored")
    return report


def _prune_report_payload(report: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not isinstance(report, dict):
        return None
    cleaned: Dict[str, Any] = {}
    for key, value in report.items():
        if key in _REPORT_SUMMARY_EXCLUDE:
            continue
        if value is None:
            continue
        if isinstance(value, (list, dict)) and not value:
            continue
        cleaned[key] = value
    return cleaned


def svc_get_summary(interview_id: str, session_id: str) -> Dict[str, Any]:
    row = _ensure_run(interview_id, session_id)
    report = row.get("report")
    summary = {
        "interview_id": row.get("interview_id"),
        "session_id": row.get("session_id"),
        "status": row.get("status"),
        "timestamp_label": row.get("timestamp_label"),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
        "summary": row.get("summary"),
        "segments": report.get("segments") if isinstance(report, dict) else None,
        "report": _prune_report_payload(report),
    }
    return summary


def svc_get_video_url(interview_id: str, session_id: str) -> Dict[str, Any]:
    row = _ensure_run(interview_id, session_id)
    blob = row.get("video_blob")
    if not blob or not azure_blob.enabled:
        raise HTTPException(404, "Annotated video not available")
    ref = BlobReference(container=azure_blob.processed_container, blob=blob)
    url = azure_blob.public_url(ref)
    if not url:
        raise HTTPException(500, "Unable to create video URL")
    return {"video_url": url, "blob": blob}


def _make_thumb_payload(row: Dict[str, Any]) -> List[Dict[str, Optional[str]]]:
    thumbs = []
    for blob in row.get("thumbnail_blobs") or []:
        url = None
        if azure_blob.enabled:
            ref = BlobReference(container=azure_blob.processed_container, blob=blob)
            url = azure_blob.public_url(ref)
        thumbs.append({"blob": blob, "url": url})
    return thumbs


def svc_get_thumbnails(interview_id: str, session_id: str) -> Dict[str, Any]:
    row = _ensure_run(interview_id, session_id)
    thumbs = _make_thumb_payload(row)
    return {"interview_id": interview_id, "session_id": session_id, "thumbnails": thumbs}


def svc_update_metadata(
    interview_id: str,
    session_id: str,
    *,
    reviewer_notes: Optional[str],
    decision: Optional[str],
    tags: Optional[Sequence[str]],
    status: Optional[str],
) -> Dict[str, Any]:
    row = _repo.update_metadata(
        interview_id,
        session_id,
        reviewer_notes=reviewer_notes,
        decision=decision,
        tags=list(tags) if tags is not None else None,
        status=status,
    )
    if not row:
        raise HTTPException(404, "Session not found")
    return row


def _delete_blob(container: str, blob: Optional[str]) -> None:
    if azure_blob.enabled and blob:
        try:
            azure_blob.delete_blob(container, blob)
        except Exception:
            pass


def _delete_blobs(container: str, blobs: Optional[Sequence[str]]) -> None:
    if not blobs:
        return
    for blob in blobs:
        _delete_blob(container, blob)


def svc_delete_report_blob(interview_id: str, session_id: str) -> Dict[str, Any]:
    row = _ensure_run(interview_id, session_id)
    _delete_blob(azure_blob.processed_container, row.get("report_blob"))
    updated = _repo.clear_blob(interview_id, session_id, "report_blob")
    return updated or row


def svc_delete_video_blob(interview_id: str, session_id: str) -> Dict[str, Any]:
    row = _ensure_run(interview_id, session_id)
    _delete_blob(azure_blob.processed_container, row.get("video_blob"))
    updated = _repo.clear_blob(interview_id, session_id, "video_blob")
    return updated or row


def _remove_local_dirs(interview_id: str, session_id: str) -> None:
    """
    Only remove derived/processed artifacts; keep original uploads intact to avoid
    losing the source video.
    """
    path = os.path.join(settings.PROCESSED_FOLDER, interview_id, session_id)
    if not os.path.isdir(path):
        return
    try:
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                try:
                    os.remove(os.path.join(root, name))
                except Exception:
                    pass
            for name in dirs:
                try:
                    os.rmdir(os.path.join(root, name))
                except Exception:
                    pass
        os.rmdir(path)
    except Exception:
        pass


def svc_delete_session(interview_id: str, session_id: str, delete_blobs: bool = True) -> Dict[str, Any]:
    row = _repo.delete_run(interview_id, session_id)
    if not row:
        raise HTTPException(404, "Session not found")
    if delete_blobs:
        _delete_blob(azure_blob.processed_container, row.get("report_blob"))
        _delete_blob(azure_blob.processed_container, row.get("video_blob"))
        _delete_blobs(azure_blob.processed_container, row.get("thumbnail_blobs"))
    _remove_local_dirs(interview_id, session_id)
    return {"ok": True, "deleted_session": session_id}


def svc_reprocess_session(interview_id: str, session_id: str) -> Dict[str, Any]:
    row = _ensure_run(interview_id, session_id)
    source_url = row.get("source_url")
    if not source_url:
        blob = row.get("source_blob")
        if blob and azure_blob.enabled:
            ref = BlobReference(container=azure_blob.videos_container, blob=blob)
            source_url = azure_blob.public_url(ref)
    if not source_url:
        raise HTTPException(400, "Source reference missing; cannot reprocess")
    return analysis_svc.svc_analyze_url(interview_id=interview_id, session_id=session_id, video_url=source_url)
