"""
Interview Audio Processing Service with Database Integration

This service handles the complete workflow of processing interview audio:
1. Download from Azure Blob Storage
2. Process audio (transcription, diarization, analytics)
3. Save results to database
4. Update status tracking

Used by: audio_controller.py for the /process-interview-audio endpoint
"""

import threading
from typing import Dict, Optional
from uuid import UUID
from config import logger, settings
from services.audio_processing_service import AudioProcessingService
from services.media_downloader import MediaDownloader
from repositories.audio_repository import AudioRepository
from db import UnitOfWork
from datetime import datetime, timezone


class InterviewAudioProcessingService:
    """
    Service for processing interview audio with database integration
    
    This service orchestrates:
    - Status updates in media_files table
    - Audio processing pipeline
    - Result persistence to database
    - Error handling and retry logic
    """
    
    def __init__(self):
        self.max_retries = 2  # Allow 3 retry on failure
    
    def process_async(
        self,
        interview_id: str,
        session_id: str,
        media_file_id: str,
        blob_name: str
    ):
        """
        Start asynchronous audio processing in background thread
        
        Args:
            interview_id: Interview UUID
            session_id: Session UUID (question)
            media_file_id: Media file UUID
            blob_name: Blob storage filename
        """
        logger.info(f"🚀 Starting async processing for media file {media_file_id}")
        
        # Start background thread
        processing_thread = threading.Thread(
            target=self._process_background,
            args=(interview_id, session_id, media_file_id, blob_name),
            daemon=True
        )
        processing_thread.start()
        
        logger.info(f"✅ Background thread started for {media_file_id}")
    
    def _process_background(
        self,
        interview_id: str,
        session_id: str,
        media_file_id: str,
        blob_name: str
    ):
        """
        Background worker for audio processing
        
        This runs in a separate thread and:
        1. Updates status to 'processing'
        2. Downloads from Azure Blob
        3. Processes audio
        4. Saves results to database
        5. Updates status to 'completed' or 'failed'
        6. Retries once on failure
        """
        uow = None
        
        try:
            logger.info(f"🎬 [Background] Processing started")
            logger.info(f"   Media File: {media_file_id}")
            logger.info(f"   Interview: {interview_id}")
            logger.info(f"   Session: {session_id}")
            logger.info(f"   Blob: {blob_name}")
            
            # Initialize database
            uow = UnitOfWork()
            repo = AudioRepository(uow)
            
            # Check if already processed
            if repo.check_if_already_processed(interview_id, session_id):
                logger.warning(f"⚠️ Already processed - skipping")
                return
            
            # Get media file info
            media_file = repo.get_media_file_by_id(media_file_id)
            if not media_file:
                logger.error(f"❌ Media file {media_file_id} not found")
                return
            
            # Check retry count (using metadata field)
            metadata_field = media_file.get('metadata', {})
            retry_count = metadata_field.get('retry_count', 0) if metadata_field else 0
            
            if retry_count >= self.max_retries:
                logger.error(f"❌ Max retries ({self.max_retries}) exceeded")
                repo.mark_processing_failed(
                    media_file_id,
                    f"Max retries ({self.max_retries}) exceeded",
                    retry_count
                )
                return
            
            # Mark as processing
            repo.mark_processing_started(media_file_id)
            
            # Download from Azure Blob
            blob_url = self._build_blob_url(blob_name)
            logger.info(f"📥 Downloading: {blob_url}")
            
            downloader = MediaDownloader()
            media_path, media_type, download_error = downloader.download(
                blob_url,
                media_file_id=media_file_id
            )
            
            if download_error:
                self._handle_processing_error(
                    repo, media_file_id, interview_id, session_id,
                    f"Download failed: {download_error}",
                    retry_count, blob_name
                )
                return
            
            logger.info(f"✅ Downloaded: {media_path} (type: {media_type})")
            
            # Process audio
            logger.info(f"🎤 Processing audio...")
            processor = AudioProcessingService()
            
            processing_result = processor.process(
                media_url=media_path,
                session_id=session_id,
                include_analytics=True
            )
            
            if processing_result["status"] != "success":
                error_msg = f"Processing failed: {processing_result.get('error', 'Unknown')}"
                self._handle_processing_error(
                    repo, media_file_id, interview_id, session_id,
                    error_msg, retry_count, blob_name
                )
                return
            
            logger.info(f"✅ Audio processing completed")
            
            # Save results
            self._save_results(
                repo, processing_result,
                interview_id, session_id, media_file_id
            )
            
            # Mark completed
            repo.mark_processing_completed(media_file_id)
            
            logger.info(f"🎉 [Background] Processing completed for {media_file_id}")
            
            # Cleanup
            downloader.cleanup()
            
        except Exception as e:
            logger.error(f"❌ [Background] Unexpected error: {str(e)}", exc_info=True)
            
            if uow:
                try:
                    repo = AudioRepository(uow)
                    media_file = repo.get_media_file_by_id(media_file_id)
                    metadata_field = media_file.get('metadata', {})
                    retry_count = metadata_field.get('retry_count', 0) if metadata_field else 0
                    
                    repo.mark_processing_failed(media_file_id, str(e), retry_count)
                    repo.save_error_analysis(interview_id, session_id, str(e))
                except Exception as db_error:
                    logger.error(f"Failed to save error: {db_error}")
        
        finally:
            if uow:
                try:
                    pass  # UnitOfWork auto-closes
                except:
                    pass
    
    def _build_blob_url(self, blob_name: str) -> str:
        """Build full Azure Blob Storage URL"""
        return (
            f"https://{settings.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/"
            f"{settings.AZURE_STORAGE_CONTAINER_NAME}/{blob_name}"
        )
    
    def _handle_processing_error(
        self,
        repo: AudioRepository,
        media_file_id: str,
        interview_id: str,
        session_id: str,
        error_msg: str,
        retry_count: int,
        blob_name: str
    ):
        """
        Handle processing error with retry logic
        
        Args:
            repo: Audio repository instance
            media_file_id: Media file UUID
            interview_id: Interview UUID
            session_id: Session UUID
            error_msg: Error message
            retry_count: Current retry count
            blob_name: Blob storage filename
        """
        logger.error(f"❌ {error_msg}")
        
        # Retry logic
        if retry_count < self.max_retries:
            logger.info(f"🔁 Retrying... (attempt {retry_count + 1}/{self.max_retries})")
            repo.increment_retry_count(media_file_id)
            
            # Retry in new background thread
            threading.Thread(
                target=self._process_background,
                args=(
                    interview_id, 
                    session_id,
                    media_file_id,
                    blob_name
                ),
                daemon=True
            ).start()
        else:
            # Max retries exceeded
            repo.mark_processing_failed(media_file_id, error_msg, retry_count)
            repo.save_error_analysis(interview_id, session_id, error_msg)
    
    def _save_results(
        self,
        repo: AudioRepository,
        result: dict,
        interview_id: str,
        session_id: str,
        media_file_id: str
    ):
        """
        Save all processing results to database
        
        Saves to:
        - transcripts
        - ai_analysis
        - proctoring_events (if cheating detected)
        - evidence_clips (if cheating detected)
        """
        logger.info(f"💾 Saving results to database...")
        
        # 1. Save transcript
        transcript_data = {
            'interview_id': interview_id,
            'session_id': session_id,
            'speaker': 'candidate',
            'text': result.get('transcript', ''),
            'confidence_score': 0.95 if result.get('language') == 'en' else 0.85,
            'word_timestamps': result.get('word_timestamps', {}),
            'disfluencies': result.get('filler_analysis', {})
        }
        repo.save_transcript(transcript_data)
        
        # 2. Save AI analysis (complete results)
        ai_analysis_data = {
            'interview_id': interview_id,
            'session_id': session_id,
            'analysis_type': 'audio_analysis',
            'service_name': 'audio-ai-service',
            'raw_results': result,
            'confidence_score': self._calculate_confidence_score(result),
            'processing_time': int(result.get('processing_time_seconds', 0)),
            'version': 'v1.0'
        }
        repo.save_ai_analysis(ai_analysis_data)
        
        # 3. Save proctoring events (if cheating detected)
        cheating_detection = result.get('cheating_detection', {})
        if cheating_detection.get('cheating_detected', False):
            logger.warning(f"🚨 Cheating detected - saving proctoring event")
            
            proctoring_data = {
                'interview_id': interview_id,
                'session_id': session_id,
                'event_type': 'multiple_speakers',
                'severity': cheating_detection.get('risk_level', 'medium'),
                'description': cheating_detection.get('reason', 'Multiple speakers detected'),
                'rule_id': 'AUDIO_MULTI_SPEAKER',
                'evidence': result.get('speaker_analysis', {}),
                'flagged_for_review': True
            }
            repo.save_proctoring_event(proctoring_data)
            
            # 4. Save evidence clips
            speaker_changes = cheating_detection.get('speaker_changes', [])
            for i, change in enumerate(speaker_changes[:5]):
                clip_data = {
                    'interview_id': interview_id,
                    'session_id': session_id,
                    'media_file_id': media_file_id,
                    'start_ms': int(change.get('start', 0) * 1000),
                    'end_ms': int(change.get('end', 0) * 1000),
                    'label': f"speaker_change_{i+1}: {change.get('from_speaker')}→{change.get('to_speaker')}"
                }
                repo.save_evidence_clip(clip_data)
        
        logger.info(f"✅ Results saved to database")
    
    def _calculate_confidence_score(self, result: dict) -> float:
        """
        Calculate overall confidence score (0-10 scale)
        
        Based on:
        - Communication score (if available)
        - Vocal analytics quality
        - Transcript completeness
        """
        communication_score = result.get('communication_score', {})
        
        if communication_score and 'overall_score' in communication_score:
            return round(communication_score['overall_score'], 2)
        
        # Fallback
        vocal_analytics = result.get('vocal_analytics', {})
        
        if vocal_analytics:
            speaking_rate = vocal_analytics.get('speaking_rate_wpm', 0)
            pitch_variance = vocal_analytics.get('pitch', {}).get('std_dev', 0)
            
            rate_score = min(10, max(0, (speaking_rate / 180) * 10))
            pitch_score = min(10, pitch_variance * 2)
            
            return round((rate_score + pitch_score) / 2, 2)
        
        return 6.0  # Default