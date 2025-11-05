import sys
sys.path.append('/common-service')

from repository.base_repository import BaseRepository
from db import UnitOfWork
from sqlalchemy import Table, Column, Text, Integer, String, Boolean, DateTime, MetaData, select, insert, update, text
from sqlalchemy.dialects.postgresql import UUID, JSONB, NUMERIC
from datetime import datetime, timezone
from typing import List, Dict, Optional
from config import logger
import json


metadata = MetaData()

# ==========================================
# TABLE DEFINITIONS
# ==========================================

media_files_table = Table(
    "media_files",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("interview_id", UUID),
    Column("session_id", UUID),
    Column("file_type", String),
    Column("file_path", String),
    Column("storage_uri", String),
    Column("file_size", Integer),
    Column("duration", Integer),
    Column("mime_type", String),
    Column("checksum", String),
    Column("metadata", JSONB),
    Column("created_at", DateTime),
    Column("deleted_at", DateTime),
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

scores_table = Table(
    "scores",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("interview_id", UUID),
    Column("response_id", UUID),
    Column("dimension", String),  # Will use 'soft_skill'
    Column("auto_score", NUMERIC),
    Column("human_override_score", NUMERIC),
    Column("rubric", JSONB),
    Column("evidence_refs", JSONB),
    Column("notes", Text),
    Column("created_by", UUID),
    Column("created_at", DateTime),
    Column("updated_at", DateTime),
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

responses_table = Table(
    "responses",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("interview_id", UUID),
    Column("session_id", UUID),
    Column("responder_id", UUID),
    Column("response_text", Text),
    Column("response_json", JSONB),
    Column("latency_ms", Integer),
    Column("duration_ms", Integer),
    Column("started_at", DateTime),
    Column("completed_at", DateTime),
    Column("created_at", DateTime),
)


# ==========================================
# REPOSITORY CLASS
# ==========================================

class AudioRepository(BaseRepository):
    """Repository for audio processing database operations"""
    
    # ==========================================
    # FETCH METHODS (Polling & Data Retrieval)
    # ==========================================


    def __init__(self, session_or_uow):
        """
        Initialize repository with session or UnitOfWork
        
        Args:
            session_or_uow: Either a SQLAlchemy Session or UnitOfWork object
        """
        # Handle both UnitOfWork and direct Session
        if hasattr(session_or_uow, 'session'):
            # It's a UnitOfWork object
            self.session = session_or_uow.session
        else:
            # It's already a Session object
            self.session = session_or_uow
    
    def get_pending_media_files(self) -> List[Dict]:
        """
        Get media files that need processing
        
        Returns files where:
        - file_type is 'audio' or 'video'
        - checksum is NULL (not processed yet)
        - NOT already in ai_analysis with service_name='audio-ai-service'
        """
        query = text("""
            SELECT 
                mf.id,
                mf.interview_id,
                mf.session_id,
                mf.file_type,
                mf.storage_uri,
                mf.duration,
                mf.created_at
            FROM media_files mf
            WHERE mf.file_type IN ('audio', 'video')
              AND mf.checksum IS NULL
              AND mf.deleted_at IS NULL
              AND NOT EXISTS (
                  SELECT 1 FROM ai_analysis aa
                  WHERE aa.interview_id = mf.interview_id
                    AND aa.session_id = mf.session_id
                    AND aa.service_name = 'audio-ai-service'
              )
            ORDER BY mf.created_at ASC
            LIMIT 10
        """)
        
        result = self.session.execute(query)
        files = [dict(row._mapping) for row in result]
        
        logger.info(f"📋 Found {len(files)} pending media files to process")
        return files

    def get_unprocessed_media_files(self, limit: int = 10) -> List[Dict]:
        """
        Get media files that need processing (improved version with race condition handling)

        Returns files where:
        - file_type is 'audio' or 'video'
        - checksum is NULL or 'processing' but stuck for >2 hours
        - NOT already successfully processed in ai_analysis

        Args:
            limit: Maximum number of files to return
        """
        query = text("""
            SELECT
                mf.id,
                mf.interview_id,
                mf.session_id,
                mf.file_type,
                mf.storage_uri,
                mf.duration,
                mf.checksum,
                mf.metadata,
                mf.created_at
            FROM media_files mf
            WHERE mf.file_type IN ('audio', 'video')
              AND mf.deleted_at IS NULL
              AND (
                  -- Never processed
                  mf.checksum IS NULL
                  OR
                  -- Stuck in processing for >2 hours (handle crashed workers)
                  (
                      mf.checksum = 'processing'
                      AND mf.created_at < NOW() - INTERVAL '2 hours'
                  )
              )
              AND NOT EXISTS (
                  -- No successful AI analysis exists
                  SELECT 1 FROM ai_analysis aa
                  WHERE aa.interview_id = mf.interview_id
                    AND aa.session_id = mf.session_id
                    AND aa.service_name = 'audio-ai-service'
                    AND aa.raw_results->>'error' IS NULL  -- Only exclude successful ones
              )
            ORDER BY mf.created_at ASC
            LIMIT :limit
        """)

        result = self.session.execute(query, {"limit": limit})
        files = [dict(row._mapping) for row in result]

        logger.info(f"📋 Found {len(files)} unprocessed media files (limit: {limit})")
        return files
    
    def get_candidate_name(self, interview_id: str) -> Optional[str]:
        """Get candidate name from interview and candidates table"""
        query = text("""
            SELECT c.full_name
            FROM interviews i
            JOIN candidates c ON i.candidate_id = c.id
            WHERE i.id = :interview_id
        """)
        
        result = self.session.execute(query, {"interview_id": interview_id})
        row = result.fetchone()
        
        if row:
            return row[0]
        
        logger.warning(f"⚠️ Candidate name not found for interview {interview_id}")
        return "Unknown Candidate"
    
    def check_if_already_processed(self, interview_id: str, session_id: str) -> bool:
        """Check if this interview/session already processed"""
        query = select(ai_analysis_table).where(
            ai_analysis_table.c.interview_id == interview_id,
            ai_analysis_table.c.session_id == session_id,
            ai_analysis_table.c.service_name == 'audio-ai-service'
        )
        
        result = self.session.execute(query).fetchone()
        return result is not None
    
    # ==========================================
    # MARK PROCESSING STATUS
    # ==========================================
    
    def mark_processing_started(self, media_file_id: str):
        """Mark media file as being processed"""
        query = update(media_files_table).where(
            media_files_table.c.id == media_file_id
        ).values(checksum='processing')
        
        self.session.execute(query)
        self.session.commit()
        logger.info(f"🔄 Marked media file {media_file_id} as processing")
    
    def mark_processing_completed(self, media_file_id: str, checksum_hash: str):
        """Mark media file as processed with checksum"""
        query = update(media_files_table).where(
            media_files_table.c.id == media_file_id
        ).values(checksum=checksum_hash)
        
        self.session.execute(query)
        self.session.commit()
        logger.info(f"✅ Marked media file {media_file_id} as completed")
    
    # ==========================================
    # SAVE RESULTS
    # ==========================================
    
    def save_transcript(self, data: Dict) -> str:
        """
        Save transcript to database
        
        Args:
            data: {
                'interview_id': uuid,
                'session_id': uuid,
                'speaker': str,
                'text': str,
                'confidence_score': float,
                'start_time': int (ms),
                'end_time': int (ms),
                'word_timestamps': dict,
                'disfluencies': dict
            }
        """
        query = insert(transcripts_table).values(**data)
        result = self.session.execute(query)
        self.session.commit()
        
        transcript_id = result.inserted_primary_key[0]
        logger.info(f"💾 Saved transcript: {transcript_id}")
        return str(transcript_id)
    
    def save_ai_analysis(self, data: Dict) -> str:
        """
        Save AI analysis results
        
        Args:
            data: {
                'interview_id': uuid,
                'session_id': uuid,
                'analysis_type': 'audio_analysis',
                'service_name': 'audio-ai-service',
                'raw_results': dict (complete analysis JSON),
                'confidence_score': float,
                'processing_time': int (seconds),
                'version': str (model versions)
            }
        """
        # Add created_at if not present
        if 'created_at' not in data:
            data['created_at'] = datetime.now(timezone.utc)
        
        query = insert(ai_analysis_table).values(**data)
        result = self.session.execute(query)
        self.session.commit()
        
        analysis_id = result.inserted_primary_key[0]
        logger.info(f"💾 Saved AI analysis: {analysis_id}")
        return str(analysis_id)
    
    def save_scores(self, data: Dict) -> str:
        """
        Save scores to database
        
        Args:
            data: {
                'interview_id': uuid,
                'response_id': uuid,
                'dimension': 'soft_skill',
                'auto_score': float,
                'rubric': dict (all scores in detail),
                'evidence_refs': dict
            }
        """
        # Add timestamps
        if 'created_at' not in data:
            data['created_at'] = datetime.now(timezone.utc)
        if 'updated_at' not in data:
            data['updated_at'] = datetime.now(timezone.utc)
        
        query = insert(scores_table).values(**data)
        result = self.session.execute(query)
        self.session.commit()
        
        score_id = result.inserted_primary_key[0]
        logger.info(f"💾 Saved scores: {score_id}")
        return str(score_id)
    
    def save_proctoring_event(self, data: Dict) -> str:
        """
        Save proctoring event (cheating detection)
        
        Args:
            data: {
                'interview_id': uuid,
                'session_id': uuid,
                'event_type': 'multiple_speakers' | 'monotonous_reading',
                'severity': 'high' | 'medium' | 'low',
                'description': str,
                'rule_id': str,
                'event_time_ms': int,
                'evidence': dict,
                'flagged_for_review': bool
            }
        """
        if 'created_at' not in data:
            data['created_at'] = datetime.now(timezone.utc)

        query = insert(proctoring_events_table).values(**data)
        result = self.session.execute(query)
        self.session.commit()
        
        event_id = result.inserted_primary_key[0]
        logger.info(f"🚨 Saved proctoring event: {event_id} - {data['event_type']}")
        return str(event_id)
    
    def save_evidence_clip(self, data: Dict) -> str:
        """
        Save evidence clip
        
        Args:
            data: {
                'interview_id': uuid,
                'session_id': uuid,
                'media_file_id': uuid,
                'start_ms': int,
                'end_ms': int,
                'label': str (e.g., 'multiple_speakers_detected')
            }
        """
        if 'created_at' not in data:
            data['created_at'] = datetime.now(timezone.utc)

        query = insert(evidence_clips_table).values(**data)
        result = self.session.execute(query)
        self.session.commit()
        
        clip_id = result.inserted_primary_key[0]
        logger.info(f"🎬 Saved evidence clip: {clip_id}")
        return str(clip_id)
    
    def get_or_create_response(self, interview_id: str, session_id: str) -> str:
        """
        Get existing response_id or create one for scores table
        
        Since scores table requires response_id, we need to ensure a response exists
        """
        # Check if response already exists
        query = select(responses_table).where(
            responses_table.c.interview_id == interview_id,
            responses_table.c.session_id == session_id
        )
        result = self.session.execute(query).fetchone()
        
        if result:
            return str(result.id)
        
        # Create a placeholder response
        response_data = {
            'interview_id': interview_id,
            'session_id': session_id,
            'responder_id': interview_id,  # Use interview_id as placeholder
            'response_text': 'Audio analysis response',
            'created_at': datetime.now(timezone.utc)
        }
        
        query = insert(responses_table).values(**response_data)
        result = self.session.execute(query)
        self.session.commit()
        
        response_id = result.inserted_primary_key[0]
        logger.info(f"📝 Created response record: {response_id}")
        return str(response_id)
    
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