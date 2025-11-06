# app/repositories/media_repository.py
from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from typing import Optional, Dict, Any
from sqlalchemy import select, insert, update, delete
from repository.base_repository import BaseRepository
from app.db.schema import media


class MediaRepository(BaseRepository):
    # ==============
    # VIDEO (one row per recording)
    # ==============

    def create_recording_video(
        self,
        *,
        user_id: str,
        session_id: str,
        expected_total: Optional[int] = None,
        assigned_user: Optional[str] = None,
        candidate_id: Optional[str] = None,
        interview_id: Optional[str] = None,
    ) -> int:
        """
        Create a 'video' row at upload/init time.
        Tracks chunks in received_indices/expected_total on THIS row.
        """
        now = datetime.utcnow()
        stmt = (
            insert(media)
            .values(
                user_id=user_id,
                media_type="video",
                file_name=None,
                file_path=None,
                blob_name=None,
                content_type=None,         # will become 'video/mp4' at finalize
                status="recording",         # <— recording state
                size_bytes=None,
                duration_ms=None,
                session_id=session_id,      # used to match subsequent chunk updates
                assigned_user=assigned_user,
                candidate_id=candidate_id,
                interview_id=interview_id,
                expected_total=expected_total,
                received_indices=[],        # <— track chunks here
                extra="{}",                 # merged_chunks etc. at finalize
                created_at=now,
                updated_at=now,
            )
            .returning(media.c.id)
        )
        return self.session.execute(stmt).scalar_one()

    def mark_chunk_received(
        self,
        *,
        user_id: str,
        session_id: str,
        idx: Optional[int],
        expected_total: Optional[int] = None,
    ) -> None:
        """
        Append idx into received_indices and lift expected_total if provided.
        Operates on the existing video row (status='recording').
        """
        row = self.session.execute(
            select(
                media.c.id,
                media.c.received_indices,
                media.c.expected_total,
                media.c.status,
            )
            .where(
                media.c.user_id == user_id,
                media.c.session_id == session_id,
                media.c.media_type == "video",
            )
            .order_by(media.c.id.desc())
            .limit(1)
        ).mappings().one_or_none()

        if not row:
            # If no row found (edge case), create one on-the-fly
            video_id = self.create_recording_video(
                user_id=user_id, session_id=session_id, expected_total=expected_total
            )
            cur = []
            exp = expected_total
            row_id = video_id
        else:
            row_id = row["id"]
            cur = list(row["received_indices"] or [])
            exp = row["expected_total"]
            # If someone already finalized, flip it back to recording for safety? Usually not.
            # We just keep writing while status is 'recording'.
        
        if idx is not None:
            ii = int(idx)
            if ii not in cur:
                cur.append(ii)
                cur.sort()

        if expected_total is not None:
            exp = max(int(expected_total), int(exp or 0))

        self.session.execute(
            update(media)
            .where(media.c.id == row_id)
            .values(
                received_indices=cur,
                expected_total=exp,
                updated_at=datetime.utcnow(),
            )
        )

    def finalize_recording(
        self,
        *,
        user_id: str,
        session_id: str,
        final_file_name: str,
        final_blob_path: str,
        merged_chunks: List[str],
        size_bytes: Optional[int] = None,
        duration_ms: Optional[int] = None,
    ) -> int:
        """
        Finalize the existing recording row: write file_name/path/blob_name, status='finalized',
        content_type='video/mp4', extra -> {"merged_chunks": [...]}
        Returns the video row id.
        """
        row = self.session.execute(
            select(media.c.id)
            .where(
                media.c.user_id == user_id,
                media.c.session_id == session_id,
                media.c.media_type == "video",
            )
            .order_by(media.c.id.desc())
            .limit(1)
        ).scalar_one_or_none()

        if row is None:
            # If there is somehow no row, create one and then finalize it.
            row = self.create_recording_video(
                user_id=user_id, session_id=session_id, expected_total=None
            )

        self.session.execute(
            update(media)
            .where(media.c.id == row)
            .values(
                file_name=final_file_name,
                file_path=final_blob_path,
                blob_name=final_blob_path,
                content_type="video/mp4",
                status="finalized",
                size_bytes=size_bytes,
                duration_ms=duration_ms,
                extra={"merged_chunks": merged_chunks},
                updated_at=datetime.utcnow(),
            )
        )
        return row

    # Optional helper if you want to explicitly abandon an ongoing recording
    def abort_recording(self, *, user_id: str, session_id: str) -> None:
        self.session.execute(
            update(media)
            .where(
                media.c.user_id == user_id,
                media.c.session_id == session_id,
                media.c.media_type == "video",
                media.c.status == "recording",
            )
            .values(status="aborted", updated_at=datetime.utcnow())
        )

    # ==============
    # FILE (one row per uploaded file)
    # ==============

    def insert_file(
        self,
        *,
        user_id: str,
        file_name: str,
        blob_path: str,
        content_type: str,
        size_bytes: Optional[int] = None,
        assigned_user: Optional[str] = None,
        extra: Optional[dict] = None,
    ) -> int:
        now = datetime.utcnow()
        new_id = self.session.execute(
            insert(media)
            .values(
                user_id=user_id,
                media_type="file",
                file_name=file_name,
                file_path=blob_path,
                blob_name=blob_path,
                content_type=content_type,
                status="finalized",
                size_bytes=size_bytes,
                assigned_user=assigned_user,
                extra=extra or {},
                created_at=now,
                updated_at=now,
            )
            .returning(media.c.id)
        ).scalar_one()
        return new_id

    # ==============
    # Queries & deletes (unchanged/optional)
    # ==============

    def list_videos_by_user(self, *, user_id: str):
        return self.session.execute(
            select(media).where(media.c.user_id == user_id, media.c.media_type == "video")
        ).mappings().all()

    def list_files_by_user(self, *, user_id: str):
        return self.session.execute(
            select(media).where(media.c.user_id == user_id, media.c.media_type == "file")
        ).mappings().all()

    def delete_by_blob_path(self, *, blob_path: str) -> int:
        res = self.session.execute(delete(media).where(media.c.blob_name == blob_path))
        return res.rowcount or 0


    def get_recording_status(
            self, *, user_id: str, session_id: str
        ) -> Optional[Dict[str, Any]]:
            """
            Return the current recording row's chunk status for this user+session.
            Looks only at the single-row-per-video design (media_type='video').
            """
            row = self.session.execute(
                select(
                    media.c.id,
                    media.c.status,
                    media.c.expected_total,
                    media.c.received_indices,
                )
                .where(
                    media.c.user_id == user_id,
                    media.c.session_id == session_id,
                    media.c.media_type == "video",
                )
                .order_by(media.c.id.desc())
                .limit(1)
            ).mappings().one_or_none()

            if not row:
                return None

            expected = row["expected_total"] or 0
            received = sorted(set(row["received_indices"] or []))
            missing = list(range(expected))
            if expected:
                missing = [i for i in range(expected) if i not in received]

            return {
                "id": row["id"],
                "status": row["status"],
                "expected_total": expected,
                "received": received,
                "missing": missing,
            }