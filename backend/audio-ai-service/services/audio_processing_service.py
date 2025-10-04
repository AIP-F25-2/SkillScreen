import time
import signal
from typing import Dict, Optional, Tuple
from config import logger, settings
from services.video_downloader import VideoDownloader
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
        self.downloader = VideoDownloader()
        self.extractor = AudioExtractor()
        self.transcriber = TranscriptionService()
        self.filler_detector = FillerDetectionService()
        self.diarizer = DiarizationService()
    
    def process(self, video_url: str, session_id: Optional[str] = None, 
                candidate_id: Optional[str] = None) -> Dict:
        """
        Process video through complete pipeline with timeout protection
        """
        start_time = time.time()
        
        # Set timeout (Unix only - won't work on Windows, add try/except)
        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(settings.PROCESSING_TIMEOUT_SECONDS)
        except AttributeError:
            logger.warning("Timeout not supported on this platform")
        
        try:
            logger.info(f"Starting audio processing for video: {video_url}")
            if session_id:
                logger.info(f"Session ID: {session_id}")
            if candidate_id:
                logger.info(f"Candidate ID: {candidate_id}")
            
            # Step 1: Download video
            logger.info("Step 1/5: Downloading video...")
            video_path, error = self.downloader.download(video_url)
            if error:
                return self._error_response(video_url, "download", error, start_time)
            
            # Step 2: Extract audio
            logger.info("Step 2/5: Extracting audio...")
            audio_path, error = self.extractor.extract(video_path)
            if error:
                return self._error_response(video_url, "extraction", error, start_time)
            
            duration = self.extractor.get_audio_duration(audio_path)
            logger.info(f"Audio duration: {duration:.2f} seconds")
            
            # Check duration limit
            if duration > (settings.MAX_VIDEO_DURATION_MINUTES * 60):
                return self._error_response(
                    video_url, "validation",
                    f"Video duration {duration/60:.1f} minutes exceeds limit of {settings.MAX_VIDEO_DURATION_MINUTES} minutes",
                    start_time
                )
            
            # Step 3: Transcribe
            logger.info("Step 3/5: Transcribing audio...")
            transcription_result = self.transcriber.transcribe(audio_path)
            word_count = self.transcriber.get_word_count(transcription_result["text"])
            logger.info(f"Transcription complete: {word_count} words")
            
            # Step 4: Detect fillers (optional based on config)
            filler_results = {}
            filler_summary = {}
            if settings.ENABLE_FILLER_DETECTION:
                logger.info("Step 4/5: Detecting filler words...")
                filler_results = self.filler_detector.detect_from_words(
                    transcription_result["words"]
                )
                filler_summary = self.filler_detector.get_filler_summary(
                    filler_results, duration
                )
                logger.info(f"Fillers detected: {filler_results['total_fillers']}")
            else:
                logger.info("Step 4/5: Filler detection disabled")
            
            # Step 5: Diarization (optional based on config)
            diarization_result = {}
            cheating_assessment = {}
            if settings.ENABLE_DIARIZATION:
                logger.info("Step 5/5: Running speaker diarization...")
                diarization_result = self.diarizer.diarize(audio_path)
                cheating_assessment = self.diarizer.assess_cheating_risk(
                    diarization_result, duration
                )
                logger.info(f"Speakers detected: {diarization_result['num_speakers']}")
                logger.info(f"Cheating risk: {cheating_assessment['risk_level']}")
            else:
                logger.info("Step 5/5: Diarization disabled")
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            logger.info(f"Processing complete in {processing_time:.2f} seconds")
            
            # Build response
            response = {
                "status": "success",
                "message": "Audio processing completed successfully",
                "video_url": video_url,
                "session_id": session_id,
                "candidate_id": candidate_id,
                "transcript": transcription_result["text"],
                "duration_seconds": duration,
                "word_count": word_count,
                "language": transcription_result.get("language", "en"),
                "processing_time_seconds": round(processing_time, 2)
            }
            
            # Add optional analyses
            if filler_results:
                response["filler_analysis"] = {**filler_results, **filler_summary}
            
            if diarization_result:
                response["speaker_analysis"] = {**diarization_result, **cheating_assessment}
            
            return response
            
        except TimeoutError:
            logger.error(f"Processing timeout after {settings.PROCESSING_TIMEOUT_SECONDS}s")
            return self._error_response(
                video_url, "timeout",
                f"Processing exceeded {settings.PROCESSING_TIMEOUT_SECONDS}s timeout",
                start_time
            )
        
        except Exception as e:
            logger.error(f"Unexpected error during processing: {str(e)}", exc_info=True)
            return self._error_response(
                video_url, "processing", str(e), start_time
            )
        
        finally:
            # Cancel timeout alarm
            try:
                signal.alarm(0)
            except AttributeError:
                pass
            
            # Cleanup temp files
            self.downloader.cleanup()
            self.extractor.cleanup()
    
    def _error_response(self, video_url: str, step: str, error: str, 
                       start_time: float) -> Dict:
        """Generate error response"""
        processing_time = time.time() - start_time
        
        return {
            "status": "failed",
            "message": f"Processing failed at {step} step",
            "video_url": video_url,
            "error": error,
            "processing_time_seconds": round(processing_time, 2)
        }