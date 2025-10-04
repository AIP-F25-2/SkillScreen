from fastapi import APIRouter
from config import logger
from schemas.audio_schemas import AudioProcessRequest

router = APIRouter()


@router.post("/extraction")
async def test_extraction(request: AudioProcessRequest):
    """Test video download and audio extraction only"""
    from services.video_downloader import VideoDownloader
    from services.audio_extractor import AudioExtractor
    
    logger.info(f"Testing extraction for: {request.video_url}")
    
    downloader = VideoDownloader()
    extractor = AudioExtractor()
    
    try:
        # Download video
        video_path, error = downloader.download(str(request.video_url))
        if error:
            return {"status": "failed", "error": error}
        
        # Extract audio
        audio_path, error = extractor.extract(video_path)
        if error:
            return {"status": "failed", "error": error}
        
        # Get duration
        duration = extractor.get_audio_duration(audio_path)
        
        return {
            "status": "success",
            "video_path": video_path,
            "audio_path": audio_path,
            "duration_seconds": duration
        }
    finally:
        downloader.cleanup()
        extractor.cleanup()


@router.post("/transcription")
async def test_transcription(request: AudioProcessRequest):
    """Test full pipeline: download → extract → transcribe"""
    from services.video_downloader import VideoDownloader
    from services.audio_extractor import AudioExtractor
    from services.transcription_service import TranscriptionService
    
    logger.info(f"Testing transcription for: {request.video_url}")
    
    downloader = VideoDownloader()
    extractor = AudioExtractor()
    transcriber = TranscriptionService()
    
    try:
        # Download video
        video_path, error = downloader.download(str(request.video_url))
        if error:
            return {"status": "failed", "step": "download", "error": error}
        
        # Extract audio
        audio_path, error = extractor.extract(video_path)
        if error:
            return {"status": "failed", "step": "extraction", "error": error}
        
        # Get duration
        duration = extractor.get_audio_duration(audio_path)
        
        # Transcribe
        logger.info("Starting transcription...")
        transcription_result = transcriber.transcribe(audio_path)
        
        word_count = transcriber.get_word_count(transcription_result["text"])
        
        return {
            "status": "success",
            "duration_seconds": duration,
            "transcript": transcription_result["text"],
            "word_count": word_count,
            "total_words_detected": len(transcription_result["words"]),
            "language": transcription_result["language"],
            "sample_words": transcription_result["words"][:10]
        }
    except Exception as e:
        logger.error(f"Transcription test failed: {str(e)}")
        return {"status": "failed", "error": str(e)}
    finally:
        downloader.cleanup()
        extractor.cleanup()


@router.post("/filler-detection")
async def test_filler_detection(request: AudioProcessRequest):
    """Test pipeline: download → extract → transcribe → filler detection"""
    from services.video_downloader import VideoDownloader
    from services.audio_extractor import AudioExtractor
    from services.transcription_service import TranscriptionService
    from services.filler_detection_service import FillerDetectionService
    
    logger.info(f"Testing filler detection for: {request.video_url}")
    
    downloader = VideoDownloader()
    extractor = AudioExtractor()
    transcriber = TranscriptionService()
    filler_detector = FillerDetectionService()
    
    try:
        # Download video
        video_path, error = downloader.download(str(request.video_url))
        if error:
            return {"status": "failed", "step": "download", "error": error}
        
        # Extract audio
        audio_path, error = extractor.extract(video_path)
        if error:
            return {"status": "failed", "step": "extraction", "error": error}
        
        # Get duration
        duration = extractor.get_audio_duration(audio_path)
        
        # Transcribe
        logger.info("Starting transcription...")
        transcription_result = transcriber.transcribe(audio_path)
        
        word_count = transcriber.get_word_count(transcription_result["text"])
        
        # Detect fillers
        logger.info("Detecting filler words...")
        filler_results = filler_detector.detect_from_words(transcription_result["words"])
        filler_summary = filler_detector.get_filler_summary(filler_results, duration)
        
        return {
            "status": "success",
            "duration_seconds": duration,
            "transcript": transcription_result["text"],
            "word_count": word_count,
            "filler_analysis": {
                **filler_results,
                **filler_summary
            }
        }
    except Exception as e:
        logger.error(f"Filler detection test failed: {str(e)}")
        return {"status": "failed", "error": str(e)}
    finally:
        downloader.cleanup()
        extractor.cleanup()


@router.post("/full-pipeline")
async def test_full_pipeline(request: AudioProcessRequest):
    """Test complete pipeline: download → extract → transcribe → fillers → diarization"""
    from services.video_downloader import VideoDownloader
    from services.audio_extractor import AudioExtractor
    from services.transcription_service import TranscriptionService
    from services.filler_detection_service import FillerDetectionService
    from services.diarization_service import DiarizationService
    
    logger.info(f"Testing full pipeline for: {request.video_url}")
    
    downloader = VideoDownloader()
    extractor = AudioExtractor()
    transcriber = TranscriptionService()
    filler_detector = FillerDetectionService()
    diarizer = DiarizationService()
    
    try:
        # Download video
        video_path, error = downloader.download(str(request.video_url))
        if error:
            return {"status": "failed", "step": "download", "error": error}
        
        # Extract audio
        audio_path, error = extractor.extract(video_path)
        if error:
            return {"status": "failed", "step": "extraction", "error": error}
        
        # Get duration
        duration = extractor.get_audio_duration(audio_path)
        
        # Transcribe
        logger.info("Starting transcription...")
        transcription_result = transcriber.transcribe(audio_path)
        word_count = transcriber.get_word_count(transcription_result["text"])
        
        # Detect fillers
        logger.info("Detecting filler words...")
        filler_results = filler_detector.detect_from_words(transcription_result["words"])
        filler_summary = filler_detector.get_filler_summary(filler_results, duration)
        
        # Diarization
        logger.info("Running speaker diarization...")
        diarization_result = diarizer.diarize(audio_path)
        cheating_assessment = diarizer.assess_cheating_risk(diarization_result, duration)
        
        return {
            "status": "success",
            "duration_seconds": duration,
            "transcript": transcription_result["text"],
            "word_count": word_count,
            "filler_analysis": {
                **filler_results,
                **filler_summary
            },
            "speaker_analysis": {
                **diarization_result,
                **cheating_assessment
            }
        }
    except Exception as e:
        logger.error(f"Full pipeline test failed: {str(e)}")
        return {"status": "failed", "error": str(e)}
    finally:
        downloader.cleanup()
        extractor.cleanup()