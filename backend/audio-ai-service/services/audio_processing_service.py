import time
import signal
from typing import Dict, Optional
from config import logger, settings
from services.media_downloader import MediaDownloader  # Renamed but import stays same
from services.audio_extractor import AudioExtractor
from services.transcription_service import TranscriptionService
from services.filler_detection_service import FillerDetectionService
from services.diarization_service import DiarizationService


class TimeoutError(Exception):
    """Raised when processing exceeds timeout"""
    pass


def timeout_handler(signum, frame):
    raise TimeoutError("Processing timeout exceeded")


class AudioProcessingService:
    """Main orchestrator for audio processing pipeline"""
    
    def __init__(self):
        self.downloader = MediaDownloader()
        self.extractor = AudioExtractor()
        self.transcriber = TranscriptionService()
        self.filler_detector = FillerDetectionService()
        self.diarizer = DiarizationService()
    
    def process(self, media_url: str, session_id: Optional[str] = None, 
                candidate_id: Optional[str] = None) -> Dict:
        """
        Process media (audio or video) through complete pipeline
        
        Args:
            media_url: URL of media to process (audio or video)
            session_id: Optional session identifier
            candidate_id: Optional candidate identifier
        
        Returns:
            Dictionary with processing results
        """
        start_time = time.time()
        
        # Set timeout
        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(settings.PROCESSING_TIMEOUT_SECONDS)
        except AttributeError:
            logger.warning("Timeout not supported on this platform")
        
        try:
            logger.info(f"Starting media processing for: {media_url}")
            if session_id:
                logger.info(f"Session ID: {session_id}")
            if candidate_id:
                logger.info(f"Candidate ID: {candidate_id}")
            
            # Step 1: Download media (auto-detect type)
            logger.info("Step 1: Downloading media...")
            media_path, media_type, error = self.downloader.download(media_url)
            if error:
                return self._error_response(media_url, "download", error, start_time)
            
            logger.info(f"Media type detected: {media_type}")
            
            # Step 2: Get/extract audio
            if media_type == 'audio':
                logger.info("Step 2: Media is audio - skipping extraction")
                audio_path = media_path  # Use directly
            else:
                logger.info("Step 2: Extracting audio from video...")
                audio_path, error = self.extractor.extract(media_path)
                if error:
                    return self._error_response(media_url, "extraction", error, start_time)
            
            duration = self.extractor.get_audio_duration(audio_path)
            logger.info(f"Audio duration: {duration:.2f} seconds")
            
            # Validate duration
            if duration > (settings.MAX_VIDEO_DURATION_MINUTES * 60):
                return self._error_response(
                    media_url, "validation",
                    f"Duration {duration/60:.1f} minutes exceeds limit of {settings.MAX_VIDEO_DURATION_MINUTES} minutes",
                    start_time
                )
            
            # Step 3: Transcribe
            logger.info("Step 3: Transcribing audio...")
            transcription_result = self.transcriber.transcribe(audio_path)
            word_count = self.transcriber.get_word_count(transcription_result["text"])
            logger.info(f"Transcription complete: {word_count} words")
            
            # Step 4: Detect fillers (if enabled)
            filler_results = {}
            filler_summary = {}
            if settings.ENABLE_FILLER_DETECTION:
                logger.info("Step 4: Detecting filler words...")
                filler_results = self.filler_detector.detect_from_words(
                    transcription_result["words"]
                )
                filler_summary = self.filler_detector.get_filler_summary(
                    filler_results, duration
                )
                logger.info(f"Fillers detected: {filler_results['total_fillers']}")
            else:
                logger.info("Step 4: Filler detection disabled")
            
            # Step 5: Diarization (if enabled)
            diarization_result = {}
            cheating_assessment = {}
            if settings.ENABLE_DIARIZATION:
                logger.info("Step 5: Running speaker diarization...")
                diarization_result = self.diarizer.diarize(audio_path)
                cheating_assessment = self.diarizer.assess_cheating_risk(
                    diarization_result, duration
                )
                logger.info(f"Speakers detected: {diarization_result['num_speakers']}")
                logger.info(f"Cheating risk: {cheating_assessment['risk_level']}")
            else:
                logger.info("Step 5: Diarization disabled")
            
            processing_time = time.time() - start_time
            logger.info(f"Processing complete in {processing_time:.2f} seconds")
            
            # Build response
            response = {
                "status": "success",
                "message": "Media processing completed successfully",
                "media_url": media_url,
                "media_type": media_type,
                "session_id": session_id,
                "candidate_id": candidate_id,
                "transcript": transcription_result["text"],
                "duration_seconds": duration,
                "word_count": word_count,
                "language": transcription_result.get("language", "en"),
                "processing_time_seconds": round(processing_time, 2)
            }
            
            if filler_results:
                response["filler_analysis"] = {**filler_results, **filler_summary}
            
            if diarization_result:
                response["speaker_analysis"] = {**diarization_result, **cheating_assessment}
            
            return response
            
        except TimeoutError:
            logger.error(f"Processing timeout after {settings.PROCESSING_TIMEOUT_SECONDS}s")
            return self._error_response(
                media_url, "timeout",
                f"Processing exceeded {settings.PROCESSING_TIMEOUT_SECONDS}s timeout",
                start_time
            )
        
        except Exception as e:
            logger.error(f"Unexpected error during processing: {str(e)}", exc_info=True)
            return self._error_response(media_url, "processing", str(e), start_time)
        
        finally:
            try:
                signal.alarm(0)
            except AttributeError:
                pass
            
            self.downloader.cleanup()
            # Only cleanup extracted audio if we extracted it
            if media_type != 'audio':
                self.extractor.cleanup()
    
    def _error_response(self, media_url: str, step: str, error: str, 
                       start_time: float) -> Dict:
        """Generate error response"""
        processing_time = time.time() - start_time
        
        return {
            "status": "failed",
            "message": f"Processing failed at {step} step",
            "media_url": media_url,
            "error": error,
            "processing_time_seconds": round(processing_time, 2)
        }