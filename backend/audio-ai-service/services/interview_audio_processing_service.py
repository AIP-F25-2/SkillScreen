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
        storage_uri: str
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
            args=(interview_id, session_id, media_file_id, storage_uri),
            daemon=True
        )
        processing_thread.start()
        
        logger.info(f"✅ Background thread started for {media_file_id}")
    
    def _process_background(
        self,
        interview_id: str,
        session_id: str,
        media_file_id: str,
        storage_uri: str
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
        downloader = None

        try:
            logger.info("🎬[Background] Processing started")
            logger.info(f"   Media File: {media_file_id}")
            logger.info(f"   Interview: {interview_id}")
            logger.info(f"   Session: {session_id}")
            logger.info(f"   Blob url: {storage_uri}")

            # Initialize database
            uow = UnitOfWork()
            repo = AudioRepository(uow)

            # Validate prerequisites
            validation_error = self._validate_prerequisites(
                repo, interview_id, session_id, media_file_id
            )
            if validation_error:
                return

            # Check retry count
            media_file = repo.get_media_file_by_id(media_file_id)
            retry_count = self._get_retry_count(media_file)

            if retry_count >= self.max_retries:
                logger.error(f"❌ Max retries ({self.max_retries}) exceeded")
                repo.mark_processing_failed(
                    media_file_id,
                    f"Max retries ({self.max_retries}) exceeded",
                    retry_count
                )
                return

            # Mark as processing and download
            repo.mark_processing_started(media_file_id)
            downloader = MediaDownloader()

            media_path, _, download_error = self._download_media(
                downloader, storage_uri, media_file_id
            )

            if download_error:
                self._handle_processing_error(
                    repo, media_file_id, interview_id, session_id,
                    f"Download failed: {download_error}",
                    retry_count, storage_uri
                )
                return

            # Process audio
            processing_result = self._process_audio(media_path, session_id)

            if processing_result["status"] != "success":
                error_msg = f"Processing failed: {processing_result.get('error', 'Unknown')}"
                self._handle_processing_error(
                    repo, media_file_id, interview_id, session_id,
                    error_msg, retry_count, storage_uri
                )
                return

            logger.info("✅Audio processing completed")

            # Save results
            self._save_results(
                repo, processing_result,
                interview_id, session_id, media_file_id
            )

            # Mark completed
            repo.mark_processing_completed(media_file_id)
            logger.info(f"🎉 [Background] Processing completed for {media_file_id}")

        except Exception as e:
            logger.error(f"❌ [Background] Unexpected error: {str(e)}", exc_info=True)
            self._handle_unexpected_error(uow, media_file_id, interview_id, session_id, e)

        finally:
            if downloader:
                downloader.cleanup()

    def _validate_prerequisites(
        self,
        repo: AudioRepository,
        interview_id: str,
        session_id: str,
        media_file_id: str
    ) -> Optional[str]:
        """
        Validate prerequisites before processing

        Returns:
            Error message if validation fails, None if valid
        """
        # Check if already processed
        if repo.check_if_already_processed(interview_id, session_id):
            logger.warning("⚠️Already processed - skipping")
            return "already_processed"

        # Get media file info
        media_file = repo.get_media_file_by_id(media_file_id)
        if not media_file:
            logger.error(f"❌ Media file {media_file_id} not found")
            return "media_file_not_found"

        return None

    def _get_retry_count(self, media_file: Dict) -> int:
        """Extract retry count from media file metadata"""
        metadata_field = media_file.get('metadata', {})
        return metadata_field.get('retry_count', 0) if metadata_field else 0

    def _download_media(
        self,
        downloader: MediaDownloader,
        storage_uri: str,
        media_file_id: str
    ) -> tuple:
        """Download media from Azure Blob Storage"""
        logger.info(f"📥 Downloading: {storage_uri}")

        media_path, media_type, download_error = downloader.download(
            storage_uri,
            media_file_id=media_file_id
        )

        if not download_error:
            logger.info(f"✅ Downloaded: {media_path} (type: {media_type})")

        return media_path, media_type, download_error

    def _process_audio(
        self,
        media_path: str,
        session_id: str
    ) -> dict:
        """Process audio and return results"""
        logger.info("🎤Processing audio...")
        processor = AudioProcessingService()

        return processor.process(
            media_url=media_path,
            session_id=session_id,
            include_analytics=True
        )

    def _handle_unexpected_error(
        self,
        uow: Optional[object],
        media_file_id: str,
        interview_id: str,
        session_id: str,
        error: Exception
    ):
        """Handle unexpected errors during processing"""
        if uow:
            try:
                repo = AudioRepository(uow)
                media_file = repo.get_media_file_by_id(media_file_id)
                retry_count = self._get_retry_count(media_file)

                repo.mark_processing_failed(media_file_id, str(error), retry_count)
                repo.save_error_analysis(interview_id, session_id, str(error))
            except Exception as db_error:
                logger.error(f"Failed to save error: {db_error}")
    


    
    def _handle_processing_error(
        self,
        repo: AudioRepository,
        media_file_id: str,
        interview_id: str,
        session_id: str,
        error_msg: str,
        retry_count: int,
        storage_uri: str
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
                    storage_uri
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
        - transcripts (with confidence, start_time, end_time)
        - ai_analysis (with confidence_score)
        - proctoring_events (if cheating detected)
        - evidence_clips (if cheating detected)
        """
        logger.info("💾Saving results to database...")
        
        # ============================================
        # FIX 1 & 2: Calculate confidence from Whisper word probabilities
        # and extract start/end times
        # ============================================
        words_with_confidence = result.get('word_timestamps', [])
        avg_confidence = 0.95  # default fallback
        
        if words_with_confidence:
            # Calculate average word probability from Whisper
            confidences = [
                w.get('probability', 0.95) 
                for w in words_with_confidence 
                if 'probability' in w
            ]
            if confidences:
                avg_confidence = round(sum(confidences) / len(confidences), 3)
        
        # Extract start and end times from word timestamps
        start_time = 0.0
        end_time = result.get('duration_seconds', 0.0)
        
        if words_with_confidence:
            start_time = words_with_confidence[0].get('start', 0.0)
            end_time = words_with_confidence[-1].get('end', end_time)
        
        # 1. Save transcript (with calculated confidence and times)
        transcript_data = {
            'interview_id': interview_id,
            'session_id': session_id,
            'speaker': 'candidate',
            'text': result.get('transcript', ''),
            'confidence_score': avg_confidence,  # ✅ FIX 1: Calculated from Whisper
            'start_time': start_time,            # ✅ FIX 2: Populated
            'end_time': end_time,                # ✅ FIX 2: Populated
            'word_timestamps': result.get('word_timestamps', {}),
            'disfluencies': result.get('filler_analysis', {})
        }
        repo.save_transcript(transcript_data)
        
        # ============================================
        # FIX 3: Extract confidence_score from results
        # ============================================
        # Try to get from confidence_analysis first
        confidence_score = None
        
        if 'confidence_analysis' in result:
            confidence_score = result['confidence_analysis'].get('confidence_score', None)
        
        # Fallback to communication_score
        if confidence_score is None and 'communication_score' in result:
            confidence_score = result['communication_score'].get('communication_score', None)
        
        # Final fallback to calculated score
        if confidence_score is None:
            confidence_score = self._calculate_confidence_score(result)
        
        # 2. Save AI analysis (with confidence_score)
        ai_analysis_data = {
            'interview_id': interview_id,
            'session_id': session_id,
            'analysis_type': 'audio_analysis',
            'service_name': 'audio-ai-service',
            'raw_results': result,
            'confidence_score': confidence_score,  # ✅ FIX 3: Now populated
            'processing_time': int(result.get('processing_time_seconds', 0)),
            'version': 'v1.0'
        }
        repo.save_ai_analysis(ai_analysis_data)
        
        # 3. Save proctoring events (if cheating detected)
        cheating_detection = result.get('cheating_detection', {})
        if cheating_detection.get('cheating_detected', False):
            logger.warning("🚨Cheating detected - saving proctoring event")
            
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
        
        logger.info("✅Results saved to database")
    
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