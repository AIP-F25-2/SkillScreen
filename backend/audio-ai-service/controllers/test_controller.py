from fastapi import APIRouter
from config import logger
from schemas.audio_schemas import AudioProcessRequest, AudioProcessResponse 
from services.audio_processing_service import AudioProcessingService
from services.media_downloader import MediaDownloader
from services.audio_extractor import AudioExtractor
from services.transcription_service import TranscriptionService
from services.filler_detection_service import FillerDetectionService


router = APIRouter()


@router.post("/process", response_model=AudioProcessResponse)
async def process_audio(request: AudioProcessRequest):
    """
    Process media from URL - without analytics
    
    Accepts both audio and video URLs. Automatically detects media type.
    
    Supported formats:
    - Audio: MP3, WAV, M4A, AAC, OGG, FLAC
    - Video: MP4, AVI, MOV, MKV, WEBM
    
    This endpoint:
    1. Downloads media from URL (auto-detects audio vs video)
    2. Extracts audio if video (skips if already audio)
    3. Transcribes using Whisper
    4. Detects filler words with timestamps
    5. Performs speaker diarization
    6. Assesses cheating risk
    
    Returns comprehensive analysis results
    """
    logger.info(f"Received media processing request")
    logger.info(f"Media URL: {request.media_url}") 
    logger.info(f"Session ID: {request.session_id}")
    logger.info(f"Candidate ID: {request.candidate_id}")
    
    processor = AudioProcessingService()
    
    result = processor.process(
        media_url=str(request.media_url),
        session_id=request.session_id,
        candidate_id=request.candidate_id
    )
    
    if result["status"] == "failed":
        logger.error(f"Processing failed: {result.get('error')}")
    
    return AudioProcessResponse(**result)

@router.post("/extraction")
async def test_extraction(request: AudioProcessRequest):
    """Test video download and audio extraction only"""
    from services.media_downloader import MediaDownloader
    from services.audio_extractor import AudioExtractor
    
    logger.info(f"Testing extraction for: {request.media_url}")
    
    downloader = MediaDownloader()
    extractor = AudioExtractor()
    
    try:
        # Download video
        video_path, error = downloader.download(str(request.media_url))
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
    from services.media_downloader import MediaDownloader
    from services.audio_extractor import AudioExtractor
    from services.transcription_service import TranscriptionService
    
    logger.info(f"Testing transcription for: {request.media_url}")
    
    downloader = MediaDownloader()
    extractor = AudioExtractor()
    transcriber = TranscriptionService()
    
    try:
        # Download video
        video_path, error = downloader.download(str(request.media_url))
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
    """
    Test combined filler detection (linguistic + acoustic)
    
    Tests both transcript-based and audio-based filler detection
    """
    logger.info(f"Test: Combined filler detection")
    logger.info(f"Media URL: {request.media_url}")
    
    downloader = MediaDownloader()
    extractor = AudioExtractor()
    transcriber = TranscriptionService()
    filler_detector = FillerDetectionService()
    
    try:
        # Download
        media_path, media_type, error = downloader.download(str(request.media_url))
        if error:
            return {"status": "failed", "error": error}
        
        # Extract audio if video
        if media_type == 'audio':
            audio_path = media_path
        else:
            audio_path, error = extractor.extract(media_path)
            if error:
                return {"status": "failed", "error": error}
        
        # Get duration
        duration = extractor.get_audio_duration(audio_path)
        
        # Transcribe
        logger.info("Transcribing audio...")
        transcription_result = transcriber.transcribe(audio_path)
        
        # Combined filler detection
        logger.info("Running combined filler detection...")
        filler_results = filler_detector.detect_combined(
            audio_path=audio_path,
            word_timestamps=transcription_result["words"],
            duration=duration
        )
        
        logger.info(f"Detection complete:")
        logger.info(f"  Linguistic: {filler_results['linguistic_count']}")
        logger.info(f"  Acoustic: {filler_results['acoustic_count']}")
        logger.info(f"  Total: {filler_results['total_fillers']}")
        
        return {
            "status": "success",
            "message": "Filler detection test completed",
            "media_url": str(request.media_url),
            "duration_seconds": duration,
            "transcript_preview": transcription_result["text"][:200] + "...",
            "filler_detection": filler_results
        }
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        return {"status": "failed", "error": str(e)}
    
    finally:
        downloader.cleanup()
        if media_type != 'audio':
            extractor.cleanup()


