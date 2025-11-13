import time
import signal
import threading
from typing import Dict, Optional
from config import logger, settings
from services.media_downloader import MediaDownloader
from services.audio_extractor import AudioExtractor
from services.transcription_service import TranscriptionService
from services.filler_detection_service import FillerDetectionService
from services.diarization_service import DiarizationService
from services.vocal_analytics_service import VocalAnalyticsService
from services.confidence_analyzer import ConfidenceAnalyzer
from services.communication_scorer import CommunicationScorer
from services.reading_detector import ReadingDetector


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
        self.analytics_service = VocalAnalyticsService()
        self.confidence_analyzer = ConfidenceAnalyzer()
        self.communication_scorer = CommunicationScorer()
        self.reading_detector = ReadingDetector()
    
    def process(self, media_url: str, session_id: Optional[str] = None, 
                candidate_id: Optional[str] = None, 
                include_analytics: bool = False) -> Dict:
        """
        Process media (audio or video) through complete pipeline
        
        Args:
            media_url: URL of media to process (audio or video)
            session_id: Optional session identifier
            candidate_id: Optional candidate identifier
            include_analytics: If True, run vocal analytics (only if no cheating)
        
        Returns:
            Dictionary with processing results
        """
        start_time = time.time()
        audio_path = None  # Track for analytics
        media_type = None  # Initialize
        
        # Set timeout
        try:
            if threading.current_thread() is threading.main_thread():
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(settings.PROCESSING_TIMEOUT_SECONDS)
        except AttributeError:
                logger.warning("Timeout not supported on this platform")
        
        try:
            logger.info(f"Starting media processing for: {media_url}")
            logger.info(f"Include analytics: {include_analytics}")
            if session_id:
                logger.info(f"Session ID: {session_id}")
            if candidate_id:
                logger.info(f"Candidate ID: {candidate_id}")
            
            # Step 1: Download media (auto-detect type)
            logger.info("Step 1/6: Downloading media...")
            media_path, media_type, error = self.downloader.download(media_url)
            if error:
                return self._error_response(media_url, "download", error, start_time)
            
            logger.info(f"Media type detected: {media_type}")
            
            # Step 2: Get/extract audio
            if media_type == 'audio':
                logger.info("Step 2/6: Media is audio - skipping extraction")
                audio_path = media_path
            else:
                logger.info("Step 2/6: Extracting audio from video...")
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
            logger.info("Step 3/6: Transcribing audio...")
            transcription_result = self.transcriber.transcribe(audio_path)
            word_count = self.transcriber.get_word_count(transcription_result["text"])
            logger.info(f"Transcription complete: {word_count} words")
            
            # Step 4: Detect fillers (linguistic + acoustic)
            logger.info("Step 4/6: Detecting filler words (linguistic + acoustic)...")
            filler_results = {}
            if settings.ENABLE_FILLER_DETECTION:
                filler_results = self.filler_detector.detect_combined(
                    audio_path=audio_path,
                    word_timestamps=transcription_result["words"],
                    duration=duration
                )
                logger.info(f"Fillers detected: {filler_results['total_fillers']} total")
                logger.info(f"  - Linguistic: {filler_results['linguistic_count']}")
                logger.info(f"  - Acoustic: {filler_results['acoustic_count']}")
            else:
                logger.info("Filler detection disabled")
            
            # Step 5: Diarization (always run - needed for cheating detection)
            logger.info("Step 5/6: Running speaker diarization...")
            diarization_result = {}
            cheating_assessment = {}
            cheating_detected = False
            
            if settings.ENABLE_DIARIZATION:
                diarization_result = self.diarizer.diarize(audio_path)
                cheating_assessment = self.diarizer.assess_cheating_risk(
                    diarization_result, duration
                )
                cheating_detected = cheating_assessment.get("cheating_flag", False)
                logger.info(f"Speakers detected: {diarization_result['num_speakers']}")
                logger.info(f"Cheating detected: {cheating_detected}")
            else:
                logger.info("Diarization disabled")
            
            # Step 6: Vocal Analytics & Confidence (conditional - only if no cheating and requested)
            vocal_analytics = {}
            confidence_analysis = {}
            reading_detection = {}
            communication_score = {}
            analytics_run = False

            if include_analytics:
                if cheating_detected:
                    logger.warning("Cheating detected - skipping vocal analytics")
                else:
                    logger.info("Step 6/6: Running vocal analytics...")
                    try:
                        # Run vocal analytics
                        vocal_analytics = self.analytics_service.analyze(
                            audio_path=audio_path,
                            transcript=transcription_result["text"],
                            word_timestamps=transcription_result["words"],
                            duration=duration
                        )
                        
                        # Run confidence analysis
                        logger.info("Analyzing confidence...")
                        confidence_analysis = self.confidence_analyzer.analyze(
                            vocal_analytics=vocal_analytics,
                            filler_analysis=filler_results
                        )
                        
                        # Run reading detection
                        logger.info("Detecting reading behavior...")
                        reading_detection = self.reading_detector.detect(
                        vocal_analytics=vocal_analytics,
                        filler_analysis=filler_results
                        )

                        # Run communication scoring
                        logger.info("Calculating communication score...")
                        communication_score = self.communication_scorer.calculate(
                        vocal_analytics=vocal_analytics,
                        filler_analysis=filler_results,
                        confidence_analysis=confidence_analysis,
                        reading_detection=reading_detection
                        )

                        analytics_run = True
                        logger.info("Complete soft skills analysis finished")
                        
                        
                    except Exception as e:
                        logger.error(f"Analytics failed: {str(e)}")
                        vocal_analytics = {"error": str(e)}
            else:
                logger.info("Step 6/6: Analytics not requested - skipping")
            
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
                "word_timestamps": transcription_result.get("words", []),
                "duration_seconds": duration,
                "word_count": word_count,
                "language": transcription_result.get("language", "en"),
                "processing_time_seconds": round(processing_time, 2),
                "analytics_run": analytics_run
            }
            
            # Add cheating detection (top-level for visibility)
            response["cheating_detection"] = {
                "cheating_detected": cheating_detected,
                "risk_level": cheating_assessment.get("risk_level", "low") if cheating_assessment else "low",
                "reason": cheating_assessment.get("reason", "Single speaker - normal") if cheating_assessment else "Single speaker - normal",
                "num_speakers": diarization_result.get("num_speakers", 1) if diarization_result else 1,
                "speaker_changes": cheating_assessment.get("speaker_changes", []) if cheating_assessment else []
            }
            
            # Add filler analysis
            if filler_results:
                response["filler_analysis"] = filler_results
            
            # Add detailed speaker analysis (for reference)
            if diarization_result:
                response["speaker_analysis"] = {**diarization_result, **cheating_assessment}
            
            # Add vocal analytics (only if run)
            if vocal_analytics and analytics_run:
                response["vocal_analytics"] = vocal_analytics
            
            # Add confidence analysis (only if run)
            if confidence_analysis and analytics_run:
                response["confidence_analysis"] = confidence_analysis

            # Add reading detection (only if run)
            if reading_detection and analytics_run:
                response["reading_detection"] = reading_detection

            # Add communication score (only if run)
            if communication_score and analytics_run:
                response["communication_score"] = communication_score    
            
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
                if threading.current_thread() is threading.main_thread():
                    signal.alarm(0)
            except AttributeError:
                    pass
            
            self.downloader.cleanup()
            if media_type and media_type != 'audio':
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
            "processing_time_seconds": round(processing_time, 2),
            "cheating_detected": False,
            "analytics_run": False
        }