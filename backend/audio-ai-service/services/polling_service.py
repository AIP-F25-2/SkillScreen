"""
Polling Service - Processes pending media files every hour
"""
import sys
sys.path.append('/common-service')

import asyncio
import time
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from config import logger, settings
from db import UnitOfWork
from repositories.audio_repository import AudioRepository
from services.audio_processing_service import AudioProcessingService


class PollingService:
    """
    Polling service that checks for unprocessed media files every hour
    and processes them with AI analysis
    """
    
    def __init__(
        self, 
        polling_interval_seconds: int = 3600,  # 1 hour default
        batch_size: int = 10,
        processing_timeout_hours: int = 2
    ):
        """
        Initialize polling service
        
        Args:
            polling_interval_seconds: Time between polling cycles (default: 3600 = 1 hour)
            batch_size: Max files to process per cycle (default: 10)
            processing_timeout_hours: Consider stuck if processing >N hours (default: 2)
        """
        self.polling_interval = polling_interval_seconds
        self.batch_size = batch_size
        self.processing_timeout = processing_timeout_hours
        self.is_running = False
        
        logger.info("🔧 Polling Service initialized:")
        logger.info(f"   - Interval: {polling_interval_seconds}s ({polling_interval_seconds/3600:.1f} hours)")
        logger.info(f"   - Batch size: {batch_size}")
        logger.info(f"   - Timeout: {processing_timeout_hours} hours")
    
    async def start_polling(self):
        """
        Main polling loop - runs continuously
        """
        self.is_running = True
        logger.info("🚀 Starting polling service...")
        
        cycle_count = 0
        
        while self.is_running:
            cycle_count += 1
            cycle_start = time.time()
            
            logger.info(f"\n{'='*60}")
            logger.info(f"🔄 Polling Cycle #{cycle_count} - {datetime.now(timezone.utc).isoformat()}")
            logger.info(f"{'='*60}")
            
            try:
                # Process pending media files
                processed_count = await self.process_pending_files()
                
                cycle_duration = time.time() - cycle_start
                logger.info(f"✅ Cycle #{cycle_count} completed: {processed_count} files processed in {cycle_duration:.1f}s")
                
            except Exception as e:
                logger.error(f"❌ Error in polling cycle #{cycle_count}: {e}", exc_info=True)
            
            # Sleep until next cycle
            next_run = datetime.fromtimestamp(time.time() + self.polling_interval, tz=timezone.utc)
            logger.info(f"😴 Sleeping for {self.polling_interval}s. Next run at: {next_run.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            await asyncio.sleep(self.polling_interval)
    
    async def process_pending_files(self) -> int:
        """
        Process all pending media files in current batch
        
        Returns:
            Number of files successfully processed
        """
        processed_count = 0
        
        try:
            # Get pending files from database (SYNCHRONOUS)
            with UnitOfWork() as uow:
                repo = AudioRepository(uow)
                pending_files = repo.get_unprocessed_media_files(limit=self.batch_size)
            
            if not pending_files:
                logger.info("📭 No pending files to process")
                return 0
            
            logger.info(f"📥 Processing {len(pending_files)} files...")
            
            # Process each file
            for idx, media_file in enumerate(pending_files, 1):
                try:
                    logger.info(f"\n--- File {idx}/{len(pending_files)} ---")
                    success = self.process_single_file(media_file)
                    
                    if success:
                        processed_count += 1
                        
                except (KeyError, ValueError, RuntimeError) as e:
                    logger.error(f"❌ Failed to process file {media_file['id']}: {e}", exc_info=True)
                    # Mark as failed in database
                    self.mark_as_failed(media_file['id'], str(e))

            logger.info(f"\n📊 Batch Summary: {processed_count}/{len(pending_files)} files processed successfully")
            return processed_count

        except (OSError, RuntimeError) as e:
            logger.error(f"❌ Error fetching pending files: {e}", exc_info=True)
            return 0
    
    def process_single_file(self, media_file: dict) -> bool:
        """
        Process a single media file through complete pipeline
        
        Args:
            media_file: Dict with keys: id, interview_id, session_id, storage_uri, etc.
        
        Returns:
            True if successful, False otherwise
        """
        media_file_id = str(media_file['id'])
        interview_id = str(media_file['interview_id'])
        session_id = str(media_file.get('session_id')) if media_file.get('session_id') else None
        storage_uri = media_file['storage_uri']
        
        logger.info(f"🎯 Processing media file: {media_file_id}")
        logger.info(f"   - Interview: {interview_id}")
        logger.info(f"   - Session: {session_id}")
        logger.info(f"   - Type: {media_file['file_type']}")
        logger.info(f"   - URI: {storage_uri[:80]}...")
        
        start_time = time.time()

        try:
            # Step 1: Mark as processing
            with UnitOfWork() as uow:
                repo = AudioRepository(uow)
                repo.mark_processing_started(media_file_id)

            logger.info("🔄 Marked as processing in database")

        except (OSError, RuntimeError) as e:
            logger.error(f"❌ Error marking processing started for {media_file_id}: {e}", exc_info=True)
            self.mark_as_failed(media_file_id, str(e), interview_id, session_id)
            return False

        try:
            # Step 2: Process with AI (it handles download internally)
            logger.info("🧠 Running AI processing...")
            processor = AudioProcessingService()
            analysis_result = processor.process(
                media_url=storage_uri,
                session_id=session_id,
                candidate_id=interview_id,
                include_analytics=True
            )

            if not analysis_result or analysis_result.get('status') != 'success':
                error_msg = analysis_result.get('error', 'Unknown error') if analysis_result else 'No result returned'
                raise ValueError(f"AI processing failed: {error_msg}")

            processing_time = int(time.time() - start_time)
            logger.info(f"✅ AI processing completed in {processing_time}s")

        except ValueError as e:
            logger.error(f"❌ AI processing error for {media_file_id}: {e}", exc_info=True)
            self.mark_as_failed(media_file_id, str(e), interview_id, session_id)
            return False
        except (OSError, RuntimeError, TimeoutError) as e:
            logger.error(f"❌ Processing service error for {media_file_id}: {e}", exc_info=True)
            self.mark_as_failed(media_file_id, str(e), interview_id, session_id)
            return False

        try:
            # Step 3: Save results to database
            logger.info("💾 Saving results to database...")
            self.save_results(
                media_file_id=media_file_id,
                interview_id=interview_id,
                session_id=session_id,
                analysis_result=analysis_result,
                processing_time=processing_time
            )

        except (KeyError, ValueError) as e:
            logger.error(f"❌ Error saving results for {media_file_id}: {e}", exc_info=True)
            self.mark_as_failed(media_file_id, str(e), interview_id, session_id)
            return False
        except (OSError, RuntimeError) as e:
            logger.error(f"❌ Database error saving results for {media_file_id}: {e}", exc_info=True)
            self.mark_as_failed(media_file_id, str(e), interview_id, session_id)
            return False

        try:
            # Step 4: Mark as completed with checksum
            # Use timestamp-based checksum since we don't have local file
            checksum = f"completed_{int(time.time())}"
            with UnitOfWork() as uow:
                repo = AudioRepository(uow)
                repo.mark_processing_completed(media_file_id, checksum)

            logger.info(f"✅ Processing completed successfully (checksum: {checksum})")
            return True

        except (OSError, RuntimeError) as e:
            logger.error(f"❌ Error marking processing completed for {media_file_id}: {e}", exc_info=True)
            self.mark_as_failed(media_file_id, str(e), interview_id, session_id)
            return False
    
    def save_results(
        self,
        media_file_id: str,
        interview_id: str,
        session_id: Optional[str],
        analysis_result: dict,
        processing_time: int
    ):
        """
        Save AI analysis results to database
        
        Saves:
        1. Transcript - candidate's answer to the question
        2. AI Analysis - complete raw results with all metrics
        3. Proctoring Events - only if cheating detected
        4. Evidence Clips - only if cheating detected
        
        Does NOT save scores/assessments (handled by another microservice)
        
        Args:
            media_file_id: UUID of media file
            interview_id: UUID of interview
            session_id: UUID of session (links to specific question)
            analysis_result: Complete analysis dict from AudioProcessingService
            processing_time: Processing time in seconds
        """
        with UnitOfWork() as uow:
            repo = AudioRepository(uow)
            
            try:
                # ============================================
                # 1. SAVE TRANSCRIPT
                # ============================================
                full_transcript = analysis_result.get('transcript', '')
                word_count = analysis_result.get('word_count', 0)
                duration_seconds = analysis_result.get('duration_seconds', 0)
                
                if full_transcript:
                    # Get speaker segments for timing info
                    speaker_analysis = analysis_result.get('speaker_analysis', {})
                    segments = speaker_analysis.get('segments', [])
                    
                    # Calculate start and end times
                    start_time_ms = int(segments[0].get('start', 0) * 1000) if segments else 0
                    end_time_ms = int(segments[-1].get('end', duration_seconds) * 1000) if segments else int(duration_seconds * 1000)
                    
                    transcript_data = {
                        'interview_id': interview_id,
                        'session_id': session_id,
                        'speaker': 'candidate',  # Always candidate (only they speak in audio)
                        'text': full_transcript,
                        'confidence_score': 0.85,  # Transcription confidence (Whisper default)
                        'start_time': start_time_ms,
                        'end_time': end_time_ms,
                        'word_timestamps': segments,  # Store speaker segments for reference
                        'disfluencies': analysis_result.get('filler_analysis', {})
                    }
                    
                    repo.save_transcript(transcript_data)
                    logger.info(f"💾 Saved transcript: {word_count} words, {duration_seconds:.1f}s duration")
                else:
                    logger.warning("⚠️ No transcript text found in analysis results")
                
                # ============================================
                # 2. SAVE AI ANALYSIS (Raw Results)
                # ============================================
                # Extract confidence score (0-10 scale)
                confidence_score = analysis_result.get('confidence_analysis', {}).get('confidence_score', 6.8)
                
                ai_analysis_data = {
                    'interview_id': interview_id,
                    'session_id': session_id,
                    'analysis_type': 'audio_analysis',
                    'service_name': 'audio-ai-service',
                    'raw_results': analysis_result,  # Complete JSON with all metrics
                    'confidence_score': confidence_score,  # Keep as 0-10 scale
                    'processing_time': processing_time,
                    'version': '1.0.0'
                }
                
                repo.save_ai_analysis(ai_analysis_data)
                logger.info(f"💾 Saved AI analysis: confidence={confidence_score}/10, processing_time={processing_time}s")
                
                # ============================================
                # 3. SAVE PROCTORING EVENTS (Only if Cheating)
                # ============================================
                cheating = analysis_result.get('cheating_detection', {})
                cheating_detected = cheating.get('cheating_detected', False)
                
                if cheating_detected:
                    # Save proctoring event
                    num_speakers = cheating.get('num_speakers', 0)
                    speaker_changes = cheating.get('speaker_changes', [])
                    risk_level = cheating.get('risk_level', 'medium')
                    reason = cheating.get('reason', 'Multiple speakers detected')
                    
                    event_data = {
                        'interview_id': interview_id,
                        'session_id': session_id,
                        'event_type': 'multiple_speakers',
                        'severity': risk_level,  # low, medium, high
                        'description': reason,
                        'rule_id': 'speaker_analysis',
                        'event_time_ms': 0,  # Overall event (not specific timestamp)
                        'evidence': {
                            'num_speakers': num_speakers,
                            'speaker_changes': speaker_changes,
                            'speaker_analysis': analysis_result.get('speaker_analysis', {})
                        },
                        'flagged_for_review': True
                    }

                    repo.save_proctoring_event(event_data)
                    logger.info(f"🚨 Saved proctoring event: {reason} (speakers: {num_speakers})")
                    
                    # ============================================
                    # 4. SAVE EVIDENCE CLIPS (For Each Speaker Change)
                    # ============================================
                    if speaker_changes:
                        for idx, change in enumerate(speaker_changes, 1):
                            # Each speaker change gets an evidence clip
                            timestamp_sec = change.get('timestamp', 0)
                            from_speaker = change.get('from', 'unknown')
                            to_speaker = change.get('to', 'unknown')
                            
                            # Create 5-second clip around the speaker change
                            clip_start_ms = max(0, int((timestamp_sec - 2) * 1000))
                            clip_end_ms = int((timestamp_sec + 3) * 1000)
                            
                            clip_data = {
                                'interview_id': interview_id,
                                'session_id': session_id,
                                'media_file_id': media_file_id,
                                'start_ms': clip_start_ms,
                                'end_ms': clip_end_ms,
                                'label': f'speaker_change_{idx}: {from_speaker}→{to_speaker}'
                            }
                            
                            repo.save_evidence_clip(clip_data)
                        
                        logger.info(f"🎬 Saved {len(speaker_changes)} evidence clips for speaker changes")
                    else:
                        logger.info("⚠️ Cheating detected but no speaker changes to create clips")
                
                else:
                    logger.info("✅ No cheating detected - no proctoring events saved")
                
                logger.info("=" * 60)
                logger.info("✅ All results saved to database successfully")
                logger.info("=" * 60)
                
            except Exception as e:
                logger.error(f"❌ Error saving results: {e}", exc_info=True)
                raise
    
    def mark_as_failed(
        self, 
        media_file_id: str, 
        error_message: str,
        interview_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """
        Mark media file as failed in database (SYNCHRONOUS)
        
        Args:
            media_file_id: UUID of media file
            error_message: Error description
            interview_id: Optional interview ID
            session_id: Optional session ID
        """
        try:
            with UnitOfWork() as uow:
                repo = AudioRepository(uow)
                
                # Mark checksum as 'failed'
                repo.mark_processing_completed(media_file_id, f"failed:{error_message[:200]}")
                
                # Save error analysis if we have interview info
                if interview_id:
                    repo.save_error_analysis(interview_id, session_id, error_message)
                
                logger.info(f"❌ Marked {media_file_id} as failed")
                
        except Exception as e:
            logger.error(f"❌ Error marking as failed: {e}", exc_info=True)
    
    def stop_polling(self):
        """Stop the polling service"""
        logger.info("🛑 Stopping polling service...")
        self.is_running = False


# Entry point for running as standalone service
if __name__ == "__main__":
    import asyncio
    
    # Get settings from environment
    polling_interval = getattr(settings, 'POLLING_INTERVAL_SECONDS', 3600)
    batch_size = getattr(settings, 'POLLING_BATCH_SIZE', 10)
    
    # Create and start service
    service = PollingService(
        polling_interval_seconds=polling_interval,
        batch_size=batch_size
    )
    
    try:
        asyncio.run(service.start_polling())
    except KeyboardInterrupt:
        logger.info("\n🛑 Received shutdown signal")
        service.stop_polling()