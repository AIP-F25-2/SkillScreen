# app/repositories/media_repository.py
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import text
from db import UnitOfWork
import json


class MediaRepository:
    """Unified repository for the media_files table."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.session = uow.session

    # -----------------------------------------------------
    # Create entry on upload init
    # -----------------------------------------------------
    def create_media_entry(self, interview_id: str, session_id: str, blob_name: str, file_type: str, expected_total: int):
        q = text("""
            INSERT INTO media_files (
                interview_id, session_id, file_type, blob_name,
                expected_total, received_indices, status, created_at, updated_at
            )
            VALUES (:iid, :sid, :ftype, :blob, :expected, ARRAY[]::integer[], 'uploading', NOW(), NOW())
            RETURNING id;
        """)
        res = self.session.execute(q, {
            "iid": interview_id,
            "sid": session_id,
            "ftype": file_type,
            "blob": blob_name,
            "expected": expected_total
        })
        self.session.commit()
        return res.mappings().first()

    # -----------------------------------------------------
    # Insert or update chunk progress
    # -----------------------------------------------------
    def upsert_chunk(self, interview_id, session_id, blob_name, file_type, total_chunks, chunk_index):
        q = text("""
            INSERT INTO media_files (
                interview_id, session_id, file_type, blob_name,
                expected_total, received_indices, status, created_at, updated_at
            )
            VALUES (:iid, :sid, :ftype, :blob, :total, ARRAY[:idx], 'uploading', NOW(), NOW())
            ON CONFLICT (interview_id, session_id)
            DO UPDATE SET
                received_indices = array_append(media_files.received_indices, :idx),
                expected_total = COALESCE(media_files.expected_total, :total),
                updated_at = NOW()
            RETURNING *;
        """)
        res = self.session.execute(q, {
            "iid": interview_id,
            "sid": session_id,
            "ftype": file_type,
            "blob": blob_name,
            "total": total_chunks,
            "idx": chunk_index,
        })
        self.session.commit()
        return res.mappings().first()

    # -----------------------------------------------------
    # Mark individual chunk (legacy compatibility)
    # -----------------------------------------------------
    def mark_chunk_received(self, interview_id, session_id, idx: int, expected_total: Optional[int]):
        q = text("""
            UPDATE media_files
               SET received_indices = array_append(received_indices, :idx),
                   expected_total = COALESCE(expected_total, :total),
                   updated_at = NOW()
             WHERE interview_id = :iid AND session_id = CAST(:sid AS uuid)
        """)
        self.session.execute(q, {
            "iid": interview_id,
            "sid": session_id,
            "idx": idx,
            "total": expected_total
        })

    # -----------------------------------------------------
    # Finalize merged upload
    # -----------------------------------------------------
    def finalize_upload(self, interview_id, session_id, storage_uri, file_size, checksum, blob_name=None, file_type=None, mime_type=None):
        self.session.execute(text("""
            UPDATE media_files
            SET storage_uri = :uri,
                file_size = :size,
                checksum = :chk,
                blob_name = :blob_name,
                file_type = :file_type,
                mime_type = :mime_type,
                status = 'completed',
                updated_at = NOW()
            WHERE interview_id = :iid
            AND session_id = CAST(:sid AS uuid)
        """), {
            "uri": storage_uri,
            "size": file_size,
            "chk": checksum,
            "iid": interview_id,
            "sid": session_id,
            "blob_name": blob_name,
            "file_type": file_type,
            "mime_type": mime_type
        })


    # -----------------------------------------------------
    # Generic insert for resume/interview files
    # -----------------------------------------------------
    def insert_file(
        self,
        *,
        media_type: str,
        interview_id: Optional[str] = None,
        session_id: Optional[str] = None,
        blob_name: Optional[str] = None,
        storage_uri: Optional[str] = None,
        mime_type: Optional[str] = None,
        status: Optional[str] = None,
        metadata: Optional[dict] = None,
        duration_ms: Optional[int] = None,
    ) -> str:
        """Insert a general file (non-video) into media_files table."""
        meta_json = json.dumps(metadata or {})
        q = text("""
            INSERT INTO media_files (
                interview_id, session_id, file_type, blob_name, storage_uri, mime_type,
                status, metadata, duration, created_at, updated_at
            )
            VALUES (:iid, CAST(:sid AS uuid), :ftype, :blob, :uri, :mime, :status, CAST(:meta AS jsonb), :duration, NOW(), NOW())
            RETURNING id;
        """)
        res = self.session.execute(q, {
            "iid": interview_id,
            "sid": session_id,
            "ftype": media_type,
            "blob": blob_name,
            "uri": storage_uri,
            "mime": mime_type,
            "status": status or "uploaded",
            "meta": meta_json,
            "duration": duration_ms,
        })
        self.session.commit()
        return res.scalar_one()

    # -----------------------------------------------------
    # Fetch current upload state
    # -----------------------------------------------------
    def get_recording_status(self, interview_id, session_id):
        q = text("""
            SELECT id, expected_total, received_indices, status, storage_uri
              FROM media_files
             WHERE interview_id = :iid
               AND session_id = CAST(:sid AS uuid)
             ORDER BY created_at DESC
             LIMIT 1;
        """)
        r = self.session.execute(q, {"iid": interview_id, "sid": session_id}).mappings().first()
        return dict(r) if r else None

    # -----------------------------------------------------
    # Abort/reset helper
    # -----------------------------------------------------
    def abort_recording(self, interview_id, session_id):
        self.session.execute(
            text("""
                UPDATE media_files
                   SET status='aborted', updated_at=NOW()
                 WHERE interview_id = :iid AND session_id = CAST(:sid AS uuid)
            """),
            {"iid": interview_id, "sid": session_id},
        )


    def create_recording_video(self, interview_id: str, session_id: str, expected_total: int | None = None):
        """Creates a new upload entry in media_files table."""
        result = self.uow.session.execute(
            text("""
                INSERT INTO media_files (interview_id, session_id, expected_total, received_indices, status, created_at, updated_at)
                VALUES (:iid, CAST(:sid AS uuid), :total, '{}', 'uploading', NOW(), NOW())
                RETURNING id
            """),
            {"iid": interview_id, "sid": session_id, "total": expected_total}
        )
        return result.scalar_one()


    def get_latest_active_record(self, interview_id, session_id):
        return self.session.execute(text("""
            SELECT id, expected_total, received_indices, status, blob_name
            FROM media_files
            WHERE interview_id = :iid
            AND session_id = CAST(:sid AS uuid)
            AND status = 'uploading'
            ORDER BY created_at DESC
            LIMIT 1;
        """), {"iid": interview_id, "sid": session_id}).mappings().first()


    def mark_chunk_received_by_id(self, record_id, idx, expected_total=None):
        self.session.execute(
            text("""
                UPDATE media_files
                SET received_indices = array_append(received_indices, :idx),
                    expected_total = COALESCE(:expected_total, expected_total),
                    updated_at = NOW()
                WHERE id = CAST(:rid AS uuid)
            """),
            {"idx": idx, "expected_total": expected_total, "rid": record_id}
        )


    def finalize_upload_by_id(self, record_id, storage_uri, file_size, checksum,
                            blob_name, file_type, mime_type,duration_ms: Optional[int] = None):
        self.session.execute(
            text("""
                UPDATE media_files
                SET storage_uri = :uri,
                    file_size = :size,
                    checksum = :chk,
                    blob_name = :blob,
                    file_type = :ftype,
                    mime_type = :mtype,
                    duration = COALESCE(:duration, duration),
                    status = 'completed',
                    updated_at = NOW()
                WHERE id = CAST(:rid AS uuid)
            """),
            {
                "uri": storage_uri,
                "size": file_size,
                "chk": checksum,
                "blob": blob_name,
                "ftype": file_type,
                "mtype": mime_type,
                "duration": duration_ms,
                "rid": record_id,
            }
        )


    def list_all_videos(self):
        result = self.session.execute(text("""
            SELECT id, interview_id, session_id, blob_name, status, created_at, updated_at
            FROM media_files
            WHERE file_type = 'video' OR mime_type LIKE 'video/%'
            ORDER BY created_at DESC;
        """)).mappings().all()
        return [dict(r) for r in result]


        # -----------------------------------------------------
    # Delete file by blob_name
    # -----------------------------------------------------
    def delete_file_record(self, interview_id: str, blob_name: str) -> int:
        """Deletes a file record from media_files by interview_id + blob_name."""
        q = text("""
            DELETE FROM media_files
             WHERE interview_id = :iid
               AND (blob_name = :blob OR storage_uri = :blob)
        """)
        res = self.session.execute(q, {"iid": interview_id, "blob": blob_name})
        self.session.commit()
        return res.rowcount
