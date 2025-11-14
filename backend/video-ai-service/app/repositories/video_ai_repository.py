# app.repositories.video_ai_repository.py

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Sequence

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    and_,
    delete,
    func,
    insert,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, NUMERIC, UUID

from app.utils.db import DBFactory, UnitOfWork

_LOG = logging.getLogger("video_ai_repository")

metadata = MetaData()

video_analysis_runs = Table(
    "video_analysis_runs",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")),
    Column("interview_id", UUID(as_uuid=True), nullable=False),
    Column("session_id", UUID(as_uuid=True), nullable=False),
    Column("timestamp_label", String(64), nullable=True),
    Column("media_file_id", UUID(as_uuid=True)),
    Column("report_blob", String(512), nullable=True),
    Column("video_blob", String(512), nullable=True),
    Column("status", String(32), nullable=False, default="completed"),
    Column("report_json", Text, nullable=True),
    Column("summary_json", Text, nullable=True),
    Column("reviewer_notes", Text, nullable=True),
    Column("decision", String(64), nullable=True),
    Column("tags_json", Text, nullable=True),
    Column("thumbnail_blobs_json", Text, nullable=True),
    Column("created_at", DateTime, default=datetime.now(timezone.utc)),
    Column("updated_at", DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)),
)

ai_analysis_table = Table(
    "ai_analysis",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")),
    Column("interview_id", UUID(as_uuid=True), nullable=False),
    Column("session_id", UUID(as_uuid=True)),
    Column("analysis_type", String, nullable=False),
    Column("service_name", String, nullable=False),
    Column("raw_results", JSONB),
    Column("confidence_score", NUMERIC(3, 2)),
    Column("processing_time", Integer),
    Column("version", String),
    Column("created_at", DateTime, default=datetime.now(timezone.utc)),
)

evidence_clips_table = Table(
    "evidence_clips",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")),
    Column("interview_id", UUID(as_uuid=True), nullable=False),
    Column("session_id", UUID(as_uuid=True)),
    Column("media_file_id", UUID(as_uuid=True), nullable=False),
    Column("start_ms", Integer, nullable=False),
    Column("end_ms", Integer, nullable=False),
    Column("label", String),
    Column("created_by", UUID(as_uuid=True)),
    Column("created_at", DateTime, default=datetime.now(timezone.utc)),
)

media_files_table = Table(
    "media_files",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("interview_id", UUID(as_uuid=True), nullable=False),
    Column("session_id", UUID(as_uuid=True)),
    Column("file_type", String(64)),
    Column("storage_uri", String(1024)),
    Column("file_size", Integer),
    Column("duration", Integer),
    Column("mime_type", String(128)),
    Column("checksum", String(256)),
    Column("metadata", JSONB),
    Column("created_at", DateTime),
    Column("deleted_at", DateTime),
    Column("blob_name", Text),
    Column("expected_total", Integer),
    Column("received_indices", ARRAY(Integer)),
    Column("status", String(32)),
    Column("updated_at", DateTime),
)


class VideoAIRepository:
    def __init__(self) -> None:
        DBFactory.get_engine()  # ensure engine initialized; table expected to exist

    @staticmethod
    def _format_row(row) -> Optional[Dict[str, Any]]:
        if not row:
            return None

        data = dict(row._mapping)

        # mapping for json fields → output fields
        json_fields = {
            "report_json": "report",
            "summary_json": "summary",
            "tags_json": "tags",
            "thumbnail_blobs_json": "thumbnail_blobs",
        }

        for src_field, target_field in json_fields.items():
            raw_value = data.pop(src_field, None)
            if raw_value is None:
                continue

            if isinstance(raw_value, str):
                try:
                    data[target_field] = json.loads(raw_value)
                except json.JSONDecodeError:
                    # fallback: store raw value if not valid JSON
                    data[target_field] = raw_value
            else:
                data[target_field] = raw_value

        return data

    @staticmethod
    def _extract_confidence_score(summary: Optional[Dict[str, Any]]) -> Optional[float]:
        if not isinstance(summary, dict):
            return None
        performance = summary.get("performance")
        subscores = performance.get("subscores") if isinstance(performance, dict) else None
        confidence_pct = None
        if isinstance(subscores, dict):
            confidence_pct = subscores.get("Confidence")
        if confidence_pct is not None:
            confidence_score = float(confidence_pct) / 10.0
        else:
            cheat_prob = summary.get("cheating_probability")
            if cheat_prob is None:
                return None
            confidence_score = (1.0 - float(cheat_prob)) * 10.0
        confidence_score = max(0.0, min(9.99, confidence_score))
        return round(confidence_score, 2)

    def _save_ai_analysis(
        self,
        uow: UnitOfWork,
        interview_id: str,
        session_id: str,
        summary: Optional[Dict[str, Any]],
        processing_time_seconds: Optional[float],
    ) -> None:
        payload: Dict[str, Any] = {
            "interview_id": interview_id,
            "session_id": session_id,
            "analysis_type": "video_analysis",
            "service_name": "video-ai-service",
            "raw_results": summary or {},
            "confidence_score": self._extract_confidence_score(summary),
            "processing_time": int(round(processing_time_seconds)) if processing_time_seconds is not None else None,
            "version": "v1.0",
            "created_at": datetime.now(timezone.utc),
        }
        uow.session.execute(insert(ai_analysis_table).values(**payload))

    @staticmethod
    def _segments_to_clip_rows(
        interview_id: str,
        session_id: str,
        media_file_id: str,
        segments: Sequence[Dict[str, Any]],
    ) -> list[Dict[str, Any]]:
        rows: list[Dict[str, Any]] = []
        now = datetime.now(timezone.utc)
        for segment in segments or []:
            label = segment.get("type")
            start = segment.get("start")
            end = segment.get("end")
            if label is None or start is None or end is None:
                continue
            try:
                start_ms = int(round(float(start) * 1000))
                end_ms = int(round(float(end) * 1000))
            except (TypeError, ValueError):
                continue
            if end_ms <= start_ms:
                continue
            rows.append(
                {
                    "interview_id": interview_id,
                    "session_id": session_id,
                    "media_file_id": media_file_id,
                    "start_ms": start_ms,
                    "end_ms": end_ms,
                    "label": label,
                    "created_by": None,
                    "created_at": now,
                }
            )
        return rows

    def _lookup_media_file_id(self, uow: UnitOfWork, interview_id: str, session_id: str) -> Optional[str]:
        stmt = (
            select(media_files_table.c.id)
            .where(
                and_(
                    media_files_table.c.interview_id == interview_id,
                    media_files_table.c.session_id == session_id,
                    func.lower(media_files_table.c.file_type) == "video",
                    media_files_table.c.deleted_at.is_(None),
                )
            )
            .order_by(media_files_table.c.created_at.desc(), media_files_table.c.id.desc())
            .limit(1)
        )
        row = uow.session.execute(stmt).fetchone()
        return str(row._mapping["id"]) if row else None

    def _save_evidence_clips(
        self,
        uow: UnitOfWork,
        interview_id: str,
        session_id: str,
        report: Optional[Dict[str, Any]],
        media_file_id: Optional[str],
    ) -> None:
        if not isinstance(report, dict):
            return
        segments = report.get("segments")
        if not segments:
            return
        resolved_media_id = media_file_id or self._lookup_media_file_id(uow, interview_id, session_id)
        if not resolved_media_id:
            _LOG.warning(
                "Skipping evidence clip persistence; media file not found for interview=%s session=%s",
                interview_id,
                session_id,
            )
            return
        rows = self._segments_to_clip_rows(interview_id, session_id, resolved_media_id, segments)
        if not rows:
            return
        uow.session.execute(
            delete(evidence_clips_table).where(
                and_(
                    evidence_clips_table.c.interview_id == interview_id,
                    evidence_clips_table.c.session_id == session_id,
                )
            )
        )
        uow.session.execute(insert(evidence_clips_table), rows)

    def get_media_file(self, media_id: str) -> Optional[Dict[str, Any]]:
        stmt = select(media_files_table).where(media_files_table.c.id == media_id).limit(1)
        with UnitOfWork() as uow:
            row = uow.session.execute(stmt).fetchone()
            return dict(row._mapping) if row else None

    def find_media_file_by_blob(self, interview_id: str, session_id: str, blob_name: str) -> Optional[str]:
        if not blob_name:
            return None
        stmt = (
            select(media_files_table.c.id)
            .where(
                and_(
                    media_files_table.c.interview_id == interview_id,
                    media_files_table.c.session_id == session_id,
                    media_files_table.c.blob_name == blob_name,
                    media_files_table.c.deleted_at.is_(None),
                )
            )
            .order_by(media_files_table.c.created_at.desc())
            .limit(1)
        )
        with UnitOfWork() as uow:
            row = uow.session.execute(stmt).fetchone()
            return str(row._mapping["id"]) if row else None

    def save_report(
        self,
        *,
        interview_id: str,
        session_id: str,
        timestamp_label: Optional[str],
        status: str,
        report: Optional[Dict[str, Any]],
        summary: Optional[Dict[str, Any]],
        report_blob: Optional[str],
        video_blob: Optional[str],
        thumbnail_blobs: Optional[list[str]] = None,
        media_file_id: Optional[str] = None,
        processing_time_seconds: Optional[float] = None,
    ) -> None:
        payload = {
            "interview_id": interview_id,
            "session_id": session_id,
            "timestamp_label": timestamp_label,
            "media_file_id": media_file_id,
            "report_blob": report_blob,
            "video_blob": video_blob,
            "status": status,
            "report_json": json.dumps(report, default=str) if report else None,
            "summary_json": json.dumps(summary, default=str) if summary else None,
            "reviewer_notes": None,
            "decision": None,
            "tags_json": None,
            "thumbnail_blobs_json": json.dumps(thumbnail_blobs, default=str) if thumbnail_blobs else None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        with UnitOfWork() as uow:
            uow.session.execute(insert(video_analysis_runs).values(**payload))
            self._save_ai_analysis(uow, interview_id, session_id, summary, processing_time_seconds)
            try:
                self._save_evidence_clips(uow, interview_id, session_id, report, media_file_id)
            except Exception:
                _LOG.warning(
                    "Failed to persist evidence clips for interview=%s session=%s",
                    interview_id,
                    session_id,
                    exc_info=True,
                )

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
                values["updated_at"] = datetime.now(timezone.utc)
                uow.session.execute(
                    video_analysis_runs.update()
                    .where(video_analysis_runs.c.id == row._mapping["id"])
                    .values(**values)
                )
            merged = dict(row._mapping)
            merged.update(values)
            return self._format_row(merged)

    def clear_blob(self, interview_id: str, session_id: str, blob_field: str) -> Optional[Dict[str, Any]]:
        if blob_field not in {"report_blob", "video_blob"}:
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
            now = datetime.now(timezone.utc)
            uow.session.execute(
                video_analysis_runs.update()
                .where(video_analysis_runs.c.id == row._mapping["id"])
                .values(**{blob_field: None, "updated_at": now})
            )
            merged = dict(row._mapping)
            merged[blob_field] = None
            merged["updated_at"] = now
            return self._format_row(merged)
