import sys
sys.path.append('/common-service')

from repository.base_repository import BaseRepository
from db import UnitOfWork
from sqlalchemy import Table, Column, Text, Integer, String, Boolean, DateTime, MetaData, select, insert, update, text, BigInteger, and_, func
from sqlalchemy.dialects.postgresql import UUID, JSONB, NUMERIC
from datetime import datetime, timezone
from typing import List, Dict, Optional
from config import logger
import json


metadata = MetaData()

# ==========================================
# TABLE DEFINITIONS - UPDATED SCHEMA
# ==========================================

media_files_table = Table(
    "media_files",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("interview_id", UUID),
    Column("session_id", UUID),
    Column("file_type", String),
    Column("storage_uri", String),
    Column("file_size", BigInteger),
    Column("duration", Integer),
    Column("mime_type", String),
    Column("checksum", String),
    Column("metadata", JSONB),
    Column("created_at", DateTime),
    Column("deleted_at", DateTime),
    Column("blob_name", String),
    Column("expected_total", Integer),
    Column("received_indices", JSONB),
    Column("status", String),
    Column("updated_at", DateTime),
)

candidates_table = Table(
    "candidates",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("organization_id", UUID),
    Column("full_name", String),
    Column("email", String),
    Column("phone", String),
    Column("location", String),
    Column("resume_url", String),
    Column("skills", JSONB),
    Column("experience", JSONB),
    Column("education", JSONB),
    Column("projects", JSONB),
    Column("created_at", DateTime),
    Column("updated_at", DateTime),
    Column("deleted_at", DateTime),
)

interviews_table = Table(
    "interviews",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("organization_id", UUID),
    Column("job_position_id", UUID),
    Column("candidate_id", UUID),
    Column("interviewer_id", UUID),
    Column("template_id", UUID),
    Column("status", String),
    Column("mode", String),
    Column("scheduled_at", DateTime),
    Column("started_at", DateTime),
    Column("completed_at", DateTime),
    Column("settings", JSONB),
    Column("created_at", DateTime),
    Column("updated_at", DateTime),
    Column("deleted_at", DateTime),
)

transcripts_table = Table(
    "transcripts",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("interview_id", UUID),
    Column("session_id", UUID),
    Column("speaker", String),
    Column("text", Text),
    Column("confidence_score", NUMERIC),
    Column("start_time", Integer),
    Column("end_time", Integer),
    Column("word_timestamps", JSONB),
    Column("disfluencies", JSONB),
    Column("created_at", DateTime),
)

ai_analysis_table = Table(
    "ai_analysis",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("interview_id", UUID),
    Column("session_id", UUID),
    Column("analysis_type", String),
    Column("service_name", String),
    Column("raw_results", JSONB),
    Column("confidence_score", NUMERIC),
    Column("processing_time", Integer),
    Column("version", String),
    Column("created_at", DateTime),
)

proctoring_events_table = Table(
    "proctoring_events",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("interview_id", UUID),
    Column("session_id", UUID),
    Column("event_type", String),
    Column("severity", String),
    Column("description", Text),
    Column("rule_id", String),
    Column("event_time_ms", Integer),
    Column("evidence", JSONB),
    Column("flagged_for_review", Boolean),
    Column("reviewed_by", UUID),
    Column("reviewed_at", DateTime),
    Column("created_at", DateTime),
)

evidence_clips_table = Table(
    "evidence_clips",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("interview_id", UUID),
    Column("session_id", UUID),
    Column("media_file_id", UUID),
    Column("start_ms", Integer),
    Column("end_ms", Integer),
    Column("label", String),
    Column("created_by", UUID),
    Column("created_at", DateTime),
)


# ==========================================
# REPOSITORY CLASS
# ==========================================

class AudioRepository(BaseRepository):
    """Repository for audio processing database operations"""
    
    def __init__(self, session_or_uow):
        """
        Initialize repository with session or UnitOfWork
        
        Args:
            session_or_uow: Either a SQLAlchemy Session or UnitOfWork object
        """
        if hasattr(session_or_uow, 'session'):
            self.session = session_or_uow.session
        else:
            self.session = session_or_uow
    
    # ==========================================
    # MEDIA FILE OPERATIONS
    # ==========================================
    
    def get_media_file_by_id(self, media_file_id: str) -> Optional[Dict]:
        """Get media file by ID"""
        query = select(media_files_table).where(
            media_files_table.c.id == media_file_id
        )
        
        result = self.session.execute(query).fetchone()
        
        if result:
            return dict(result._mapping)
        
        logger.warning(f"⚠️ Media file not found: {media_file_id}")
        return None
    
    def update_media_file_status(
        self, 
        media_file_id: str, 
        status: str, 
        extra_data: Optional[Dict] = None
    ):
        """
        Update media file status and metadata
        
        Args:
            media_file_id: UUID of media file
            status: 'processing', 'completed', 'failed'
            extra_data: Additional data to store in metadata JSONB field
        """
        update_values = {
            'status': status,
            'updated_at': datetime.now(timezone.utc)
        }
        
        if extra_data:
            existing = self.get_media_file_by_id(media_file_id)
            if existing and existing.get('metadata'):
                merged_extra = {**existing['metadata'], **extra_data}
                update_values['metadata'] = merged_extra
            else:
                update_values['metadata'] = extra_data
        
        query = update(media_files_table).where(
            media_files_table.c.id == media_file_id
        ).values(**update_values)
        
        self.session.execute(query)
        self.session.commit()
        
        logger.info(f"📝 Updated media file {media_file_id} status: {status}")
    
    def mark_processing_started(self, media_file_id: str):
        """Mark media file as being processed"""
        self.update_media_file_status(
            media_file_id, 
            'processing',
            {'processing_started_at': datetime.now(timezone.utc).isoformat()}
        )
        logger.info(f"🔄 Marked media file {media_file_id} as processing")
    
    def mark_processing_completed(self, media_file_id: str):
        """Mark media file as completed"""
        self.update_media_file_status(
            media_file_id,
            'completed',
            {'processing_completed_at': datetime.now(timezone.utc).isoformat()}
        )
        logger.info(f"✅ Marked media file {media_file_id} as completed")
    
    def mark_processing_failed(
        self, 
        media_file_id: str, 
        error_message: str,
        retry_count: int = 0
    ):
        """
        Mark media file as failed with error details
        
        Args:
            media_file_id: UUID of media file
            error_message: Error description
            retry_count: Number of retry attempts
        """
        extra_data = {
            'error': error_message,
            'error_timestamp': datetime.now(timezone.utc).isoformat(),
            'retry_count': retry_count,
            'status': 'failed'
        }
        
        self.update_media_file_status(media_file_id, 'failed', extra_data)
        logger.error(f"❌ Marked media file {media_file_id} as failed: {error_message}")
    
    def increment_retry_count(self, media_file_id: str) -> int:
        """
        Increment retry count and return new count
        
        Returns:
            New retry count
        """
        media_file = self.get_media_file_by_id(media_file_id)
        
        if not media_file:
            return 0
        
        metadata = media_file.get('metadata', {})
        retry_count = metadata.get('retry_count', 0) + 1
        
        self.update_media_file_status(
            media_file_id,
            'processing',
            {'retry_count': retry_count, 'last_retry_at': datetime.now(timezone.utc).isoformat()}
        )
        
        logger.info(f"🔁 Incremented retry count for {media_file_id}: {retry_count}")
        return retry_count
    
    # ==========================================
    # CANDIDATE & INTERVIEW INFO
    # ==========================================
    
    def get_candidate_name(self, candidate_id: str) -> Optional[str]:
        """Get candidate name by ID"""
        query = select(candidates_table.c.full_name).where(
            candidates_table.c.id == candidate_id
        )
        
        result = self.session.execute(query).fetchone()
        
        if result:
            return result[0]
        
        logger.warning(f"⚠️ Candidate not found: {candidate_id}")
        return None
    
    def get_interview_info(self, interview_id: str) -> Optional[Dict]:
        """Get interview details"""
        query = select(interviews_table).where(
            interviews_table.c.id == interview_id
        )
        
        result = self.session.execute(query).fetchone()
        
        if result:
            return dict(result._mapping)
        
        logger.warning(f"⚠️ Interview not found: {interview_id}")
        return None
    
    def check_if_already_processed(self, interview_id: str, session_id: str) -> bool:
        """Check if already processed SUCCESSFULLY"""
        query = select(ai_analysis_table).where(
            and_(
                ai_analysis_table.c.interview_id == interview_id,
                ai_analysis_table.c.session_id == session_id,
                ai_analysis_table.c.service_name == 'audio-ai-service'
            )
        )
        result = self.session.execute(query).fetchone()

        if not result:
            return False

        raw_results = result.raw_results if hasattr(result, 'raw_results') else {}

        if isinstance(raw_results, dict):
            status = raw_results.get('status', 'success')
            if status == 'failed':
                return False

        return True
    
    # ==========================================
    # SAVE RESULTS
    # ==========================================
    
    def save_transcript(self, data: Dict) -> str:
        """Save transcript to database"""
        if 'created_at' not in data:
            data['created_at'] = datetime.now(timezone.utc)
        
        query = insert(transcripts_table).values(**data)
        result = self.session.execute(query)
        self.session.commit()
        
        transcript_id = result.inserted_primary_key[0]
        logger.info(f"💾 Saved transcript: {transcript_id}")
        return str(transcript_id)
    
    def save_ai_analysis(self, data: Dict) -> str:
        """Save AI analysis results"""
        if 'created_at' not in data:
            data['created_at'] = datetime.now(timezone.utc)
        
        query = insert(ai_analysis_table).values(**data)
        result = self.session.execute(query)
        self.session.commit()
        
        analysis_id = result.inserted_primary_key[0]
        logger.info(f"💾 Saved AI analysis: {analysis_id}")
        return str(analysis_id)
    
    def save_proctoring_event(self, data: Dict) -> str:
        """Save proctoring event (cheating detection)"""
        if 'created_at' not in data:
            data['created_at'] = datetime.now(timezone.utc)

        query = insert(proctoring_events_table).values(**data)
        result = self.session.execute(query)
        self.session.commit()
        
        event_id = result.inserted_primary_key[0]
        logger.info(f"🚨 Saved proctoring event: {event_id} - {data['event_type']}")
        return str(event_id)
    
    def save_evidence_clip(self, data: Dict) -> str:
        """Save evidence clip"""
        if 'created_at' not in data:
            data['created_at'] = datetime.now(timezone.utc)

        query = insert(evidence_clips_table).values(**data)
        result = self.session.execute(query)
        self.session.commit()
        
        clip_id = result.inserted_primary_key[0]
        logger.info(f"🎬 Saved evidence clip: {clip_id}")
        return str(clip_id)
    
    def save_error_analysis(self, interview_id: str, session_id: str, error_message: str):
        """Save error record in ai_analysis for failed processing"""
        error_data = {
            'interview_id': interview_id,
            'session_id': session_id,
            'analysis_type': 'audio_analysis',
            'service_name': 'audio-ai-service',
            'raw_results': {
                'error': True,
                'error_message': error_message,
                'status': 'failed'
            },
            'created_at': datetime.now(timezone.utc)
        }
        
        query = insert(ai_analysis_table).values(**error_data)
        self.session.execute(query)
        self.session.commit()
        
        logger.error(f"❌ Saved error analysis for interview {interview_id}")
    
    # ==========================================
    # POLLING SUPPORT
    # ==========================================
    
    def get_pending_media_files_for_polling(self, limit: int = 10) -> List[Dict]:
        """
        Get media files for polling (backup processing)
        
        Returns files where:
        - status is NULL, 'pending', or 'failed' (for retry)
        - file_type is 'audio' or 'video'
        - NOT already successfully processed
        """
        query = text("""
            SELECT
                mf.id,
                mf.interview_id,
                mf.session_id,
                mf.file_type,
                mf.blob_name,
                mf.storage_uri,
                mf.duration,
                mf.status,
                mf.metadata,
                mf.created_at
            FROM media_files mf
            WHERE mf.file_type IN ('audio', 'video')
              AND (
                    mf.status IS NULL
                    OR mf.status = 'pending'
                    OR (mf.status = 'failed' AND (mf.metadata->>'retry_count')::int < 3)
              )
              AND NOT EXISTS (
                    SELECT 1 FROM ai_analysis aa
                    WHERE aa.interview_id = mf.interview_id
                      AND aa.session_id = mf.session_id
                      AND aa.service_name = 'audio-ai-service'
                      AND aa.raw_results->>'status' != 'failed'
              )
            ORDER BY mf.created_at ASC
            LIMIT :limit
        """)

        result = self.session.execute(query, {"limit": limit})
        files = [dict(row._mapping) for row in result]

        logger.info(f"📋 Found {len(files)} pending media files for polling")
        return files
    
    # ==========================================
    # CANDIDATE ANALYSIS QUERIES
    # ==========================================
    
    def check_candidate_has_interviews(self, candidate_id: str) -> bool:
        """
        Check if candidate has any interviews (scheduled or completed)
        
        Args:
            candidate_id: Candidate identifier
            
        Returns:
            True if candidate has interviews, False otherwise
        """
        query = select(func.count()).select_from(interviews_table).where(
            interviews_table.c.candidate_id == candidate_id
        )
        
        result = self.session.execute(query).scalar()
        return result > 0

    def get_candidate_transcripts(self, candidate_id: str):
        """Get all transcripts for a candidate with interview details"""
        query = (
            select(
                transcripts_table,
                interviews_table.c.candidate_id
            )
            .select_from(
                transcripts_table
                .join(interviews_table, transcripts_table.c.interview_id == interviews_table.c.id)
            )
            .where(interviews_table.c.candidate_id == candidate_id)
            .order_by(
                transcripts_table.c.interview_id,
                transcripts_table.c.start_time
            )
        )
        
        result = self.session.execute(query)
        return [dict(row._mapping) for row in result]

    def get_candidate_audio_analyses(self, candidate_id: str):
        """Get all audio analyses for a candidate"""
        query = (
            select(
                ai_analysis_table,
                interviews_table.c.candidate_id
            )
            .select_from(
                ai_analysis_table
                .join(interviews_table, ai_analysis_table.c.interview_id == interviews_table.c.id)
            )
            .where(
                interviews_table.c.candidate_id == candidate_id,
                ai_analysis_table.c.service_name == 'audio-ai-service'
            )
            .order_by(ai_analysis_table.c.created_at.desc())
        )
        
        result = self.session.execute(query)
        return [dict(row._mapping) for row in result]