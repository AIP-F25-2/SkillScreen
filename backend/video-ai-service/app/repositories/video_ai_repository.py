from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, Text, insert, select, delete

from app.db import DBFactory, UnitOfWork

metadata = MetaData()

video_analysis_runs = Table(
    "video_analysis_runs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("interview_id", String(255), nullable=False),
    Column("session_id", String(255), nullable=False),
    Column("timestamp_label", String(64), nullable=True),
    Column("source_blob", String(512), nullable=True),
    Column("report_blob", String(512), nullable=True),
    Column("video_blob", String(512), nullable=True),
    Column("source_url", String(512), nullable=True),
    Column("status", String(32), nullable=False, default="completed"),
    Column("report_json", Text, nullable=True),
    Column("summary_json", Text, nullable=True),
    Column("reviewer_notes", Text, nullable=True),
    Column("decision", String(64), nullable=True),
    Column("tags_json", Text, nullable=True),
    Column("thumbnail_blobs_json", Text, nullable=True),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
)


class VideoAIRepository:
    def __init__(self) -> None:
        DBFactory.get_engine()  # ensure engine initialized; table expected to exist

    @staticmethod
    def _format_row(row) -> Optional[Dict[str, Any]]:
        if not row:
            return None
        data = dict(row._mapping)
        report = data.pop("report_json", None)
        summary = data.pop("summary_json", None)
        tags = data.pop("tags_json", None)
        thumbs = data.pop("thumbnail_blobs_json", None)
        if report is not None:
            if isinstance(report, str):
                data["report"] = json.loads(report)
            else:
                data["report"] = report
        if summary is not None:
            if isinstance(summary, str):
                data["summary"] = json.loads(summary)
            else:
                data["summary"] = summary
        if summary is not None:
            if isinstance(summary, str):
                data["summary"] = json.loads(summary)
            else:
                data["summary"] = summary
        if tags is not None:
            if isinstance(tags, str):
                data["tags"] = json.loads(tags)
            else:
                data["tags"] = tags
        if thumbs is not None:
            if isinstance(thumbs, str):
                data["thumbnail_blobs"] = json.loads(thumbs)
            else:
                data["thumbnail_blobs"] = thumbs
        return data

    def save_report(
        self,
        *,
        interview_id: str,
        session_id: str,
        timestamp_label: Optional[str],
        status: str,
        report: Optional[Dict[str, Any]],
        summary: Optional[Dict[str, Any]],
        blobs: Dict[str, Optional[str]],
        source_url: Optional[str],
        thumbnail_blobs: Optional[list[str]] = None,
    ) -> None:
        payload = {
            "interview_id": interview_id,
            "session_id": session_id,
            "timestamp_label": timestamp_label,
            "source_blob": blobs.get("source_blob"),
            "report_blob": blobs.get("report_blob"),
            "video_blob": blobs.get("video_blob"),
            "source_url": source_url,
            "status": status,
            "report_json": json.dumps(report, default=str) if report else None,
            "summary_json": json.dumps(summary, default=str) if summary else None,
            "reviewer_notes": None,
            "decision": None,
            "tags_json": None,
            "thumbnail_blobs_json": json.dumps(thumbnail_blobs, default=str) if thumbnail_blobs else None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        with UnitOfWork() as uow:
            uow.session.execute(insert(video_analysis_runs).values(**payload))

    def list_runs(self, interview_id: str, limit: int = 50) -> list[Dict[str, Any]]:
        with UnitOfWork() as uow:
            result = uow.session.execute(
                select(video_analysis_runs)
                .where(video_analysis_runs.c.interview_id == interview_id)
                .order_by(video_analysis_runs.c.created_at.desc())
                .limit(limit)
            )
            return [self._format_row(row) for row in result]

    def get_run(self, interview_id: str, session_id: str, timestamp_label: Optional[str] = None) -> Optional[Dict[str, Any]]:
        stmt = select(video_analysis_runs).where(
            video_analysis_runs.c.interview_id == interview_id,
            video_analysis_runs.c.session_id == session_id,
        )
        if timestamp_label:
            stmt = stmt.where(video_analysis_runs.c.timestamp_label == timestamp_label)
        else:
            stmt = stmt.order_by(video_analysis_runs.c.created_at.desc()).limit(1)
        with UnitOfWork() as uow:
            row = uow.session.execute(stmt).fetchone()
            return self._format_row(row)

    def delete_run(self, interview_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        with UnitOfWork() as uow:
            row = uow.session.execute(
                select(video_analysis_runs).where(
                    video_analysis_runs.c.interview_id == interview_id,
                    video_analysis_runs.c.session_id == session_id,
                ).order_by(video_analysis_runs.c.created_at.desc()).limit(1)
            ).fetchone()
            if not row:
                return None
            uow.session.execute(
                delete(video_analysis_runs).where(
                    video_analysis_runs.c.id == row._mapping["id"]
                )
            )
            return self._format_row(row)

    def update_metadata(
        self,
        interview_id: str,
        session_id: str,
        *,
        reviewer_notes: Optional[str] = None,
        decision: Optional[str] = None,
        tags: Optional[Any] = None,
        status: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        with UnitOfWork() as uow:
            stmt = select(video_analysis_runs).where(
                video_analysis_runs.c.interview_id == interview_id,
                video_analysis_runs.c.session_id == session_id,
            ).order_by(video_analysis_runs.c.created_at.desc()).limit(1)
            row = uow.session.execute(stmt).fetchone()
            if not row:
                return None
            values = {}
            if reviewer_notes is not None:
                values["reviewer_notes"] = reviewer_notes
            if decision is not None:
                values["decision"] = decision
            if tags is not None:
                values["tags_json"] = json.dumps(tags, default=str)
            if status is not None:
                values["status"] = status
            if values:
                values["updated_at"] = datetime.utcnow()
                uow.session.execute(
                    video_analysis_runs.update()
                    .where(video_analysis_runs.c.id == row._mapping["id"])
                    .values(**values)
                )
            merged = dict(row._mapping)
            merged.update(values)
            return self._format_row(merged)

    def clear_blob(self, interview_id: str, session_id: str, blob_field: str) -> Optional[Dict[str, Any]]:
        if blob_field not in {"report_blob", "video_blob", "source_blob"}:
            raise ValueError("Invalid blob field")
        with UnitOfWork() as uow:
            row = uow.session.execute(
                select(video_analysis_runs).where(
                    video_analysis_runs.c.interview_id == interview_id,
                    video_analysis_runs.c.session_id == session_id,
                ).order_by(video_analysis_runs.c.created_at.desc()).limit(1)
            ).fetchone()
            if not row:
                return None
            now = datetime.utcnow()
            uow.session.execute(
                video_analysis_runs.update()
                .where(video_analysis_runs.c.id == row._mapping["id"])
                .values(**{blob_field: None, "updated_at": now})
            )
            merged = dict(row._mapping)
            merged[blob_field] = None
            merged["updated_at"] = now
            return self._format_row(merged)
