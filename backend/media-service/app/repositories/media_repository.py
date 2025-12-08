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
        blob_name: Optional[str] = None,
        mime_type: Optional[str] = None,
        status: Optional[str] = None,
        metadata: Optional[dict] = None,
        duration_ms: Optional[int] = None,
    ) -> str:
        """Insert a general file (non-video) into media_files table."""
        meta_json = json.dumps(metadata or {})
        q = text("""
            INSERT INTO media_files (
                interview_id, file_type, storage_uri, mime_type,
                status, metadata, duration, created_at, updated_at
            )
            VALUES (:iid, :ftype, :blob, :mime, :status, CAST(:meta AS jsonb), :duration,NOW(), NOW())
            RETURNING id;
        """)
        res = self.session.execute(q, {
            "iid": interview_id,
            "ftype": media_type,
            "blob": blob_name,
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


    def _ensure_interview_session_exists(self, session_id: str, interview_id: str): # nosonar
        """Ensure interview_session exists in interview_sessions table. Create it if it doesn't exist."""
        import logging
        logger = logging.getLogger(__name__)
        
        # Check if session exists
        session_check = self.uow.session.execute(
            text("""
                SELECT id::text 
                FROM interview_sessions 
                WHERE id = CAST(:sid AS uuid)
                LIMIT 1
            """),
            {"sid": session_id}
        ).scalar_one_or_none()
        
        if session_check:
            logger.debug(f"Interview session {session_id} already exists")
            return True  # Session exists
        
        # Check if interview exists (required for foreign key constraint)
        interview_check = self.uow.session.execute(
            text("""
                SELECT id::text 
                FROM interviews 
                WHERE id = CAST(:iid AS uuid)
                LIMIT 1
            """),
            {"iid": interview_id}
        ).scalar_one_or_none()
        
        if not interview_check:
            logger.warning(
                f"Interview {interview_id} does not exist in interviews table. "
                f"Cannot create interview_session. Will store session_id as NULL in media_files."
            )
            return False  # Signal that we can't create the session
        
        # Session doesn't exist - create a minimal one
        logger.info(f"Creating minimal interview_session record: session_id={session_id}, interview_id={interview_id}")
        try:
            self.uow.session.execute(
                text("""
                    INSERT INTO interview_sessions (
                        id, interview_id, question_id, question_text, question_type,
                        candidate_response, response_duration, started_at, completed_at,
                        metadata, created_at
                    )
                    VALUES (
                        CAST(:sid AS uuid),
                        CAST(:iid AS uuid),
                        'media_upload',
                        'Media upload session',
                        'general',
                        NULL,
                        NULL,
                        NOW(),
                        NULL,
                        '{"created_by": "media_service", "auto_created": true}'::jsonb,
                        NOW()
                    )
                    ON CONFLICT (id) DO NOTHING
                """),
                {"sid": session_id, "iid": interview_id}
            )
            # Flush to ensure the insert is visible in the current transaction
            self.uow.session.flush()
            
            # Verify the session was actually created
            verify_check = self.uow.session.execute(
                text("""
                    SELECT id::text 
                    FROM interview_sessions 
                    WHERE id = CAST(:sid AS uuid)
                    LIMIT 1
                """),
                {"sid": session_id}
            ).scalar_one_or_none()
            
            if verify_check:
                logger.info(f"Created and verified interview_session record: {session_id}")
                return True
            else:
                logger.error(f"Failed to verify interview_session creation: {session_id}")
                return False
        except Exception as e:
            logger.error(f"Failed to create interview_session record: {e}", exc_info=True)
            # Don't re-raise - let the calling code handle it
            return False

    def create_recording_video(self, interview_id: str, session_id: str, expected_total: int | None = None): # nosonar
        """Creates a new upload entry in media_files table."""
        import logging
        logger = logging.getLogger(__name__)
        
        # Normalize interview_id (remove whitespace)
        interview_id = str(interview_id).strip()
        session_id = str(session_id).strip() if session_id else None
        
        logger.info(f"Creating media file record: interview_id={interview_id}, session_id={session_id}")
        
        # If session_id is provided, ensure it exists in interview_sessions first
        session_available = False  # Default to False - only set to True if we confirm it exists/created
        if session_id:
            try:
                result = self._ensure_interview_session_exists(session_id, interview_id)
                if result is True:
                    session_available = True
                    logger.info(f"Session {session_id} is available (exists or was created)")
                elif result is False:
                    session_available = False
                    logger.warning(f"Session {session_id} cannot be created (interview doesn't exist)")
                else:
                    # Shouldn't happen, but handle it
                    session_available = False
            except Exception as e:
                logger.error(f"Error ensuring interview_session exists: {e}. Will not store session_id.", exc_info=True)
                session_available = False
        
        # Try to store session_id directly (only if we confirmed it exists or was created)
        if session_id and session_available is True:
            try:
                # Attempt insert with session_id
                result = self.uow.session.execute(
                    text("""
                        INSERT INTO media_files (interview_id, session_id, file_type, expected_total, received_indices, status, created_at, updated_at)
                        VALUES (CAST(:iid AS uuid), CAST(:sid AS uuid), 'video', :total, '{}', 'uploading', NOW(), NOW())
                        RETURNING id
                    """),
                    {"iid": interview_id, "sid": session_id, "total": expected_total}
                )
                record_id = result.scalar_one()
                logger.info(f"Successfully created media file record with session_id: id={record_id}, session_id={session_id}")
                return record_id
            except Exception as e:
                error_msg = str(e)
                # Check if it's a foreign key violation for session_id
                if "foreign key" in error_msg.lower() and ("session_id" in error_msg.lower() or "interview_sessions" in error_msg.lower()):
                    logger.warning(
                        f"Foreign key violation for session_id {session_id} even after ensuring session exists. "
                        "Falling back to NULL session_id."
                    )
                    # Fall through to insert with NULL
                else:
                    # Re-raise other errors
                    logger.error(f"Error creating media file record: {error_msg}")
                    raise
        
        # Insert with NULL session_id (either no session_id provided, or foreign key violation)
        result = self.uow.session.execute(
            text("""
                INSERT INTO media_files (interview_id, session_id, file_type, expected_total, received_indices, status, created_at, updated_at)
                VALUES (CAST(:iid AS uuid), NULL, 'video', :total, '{}', 'uploading', NOW(), NOW())
                RETURNING id
            """),
            {"iid": interview_id, "total": expected_total}
        )
        record_id = result.scalar_one()
        logger.info(f"Successfully created media file record with NULL session_id: id={record_id}")
        return record_id


    def get_latest_active_record(self, interview_id, session_id): # nosonar
        """Get the latest active upload record.
        
        This method handles the case where session_id might be NULL in the database
        even if a session_id was provided. It checks both the provided session_id
        and NULL to find the matching record.
        """
        # First try with the provided session_id (if provided)
        if session_id:
            result = self.session.execute(text("""
                SELECT id, expected_total, received_indices, status, blob_name
                FROM media_files
                WHERE interview_id = CAST(:iid AS uuid)
                AND session_id = CAST(:sid AS uuid)
                AND status = 'uploading'
                ORDER BY created_at DESC
                LIMIT 1;
            """), {"iid": interview_id, "sid": session_id}).mappings().first()
            
            if result:
                return dict(result)
            
            # If not found with provided session_id, also check for NULL session_id
            # (in case the record was inserted with NULL because session didn't exist in interview_sessions)
            # This allows us to find records that were created when session_id didn't exist
            result = self.session.execute(text("""
                SELECT id, expected_total, received_indices, status, blob_name
                FROM media_files
                WHERE interview_id = CAST(:iid AS uuid)
                AND session_id IS NULL
                AND status = 'uploading'
                ORDER BY created_at DESC
                LIMIT 1;
            """), {"iid": interview_id}).mappings().first()
            
            return dict(result) if result else None
        else:
            # No session_id provided - only check for NULL
            result = self.session.execute(text("""
                SELECT id, expected_total, received_indices, status, blob_name
                FROM media_files
                WHERE interview_id = CAST(:iid AS uuid)
                AND session_id IS NULL
                AND status = 'uploading'
                ORDER BY created_at DESC
                LIMIT 1;
            """), {"iid": interview_id}).mappings().first()
            
            return dict(result) if result else None


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
