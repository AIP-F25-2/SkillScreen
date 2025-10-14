from fastapi import APIRouter, HTTPException, BackgroundTasks
from config import logger, settings
from schemas.audio_schemas import AudioProcessRequest, AudioProcessResponse
from services.audio_processing_service import AudioProcessingService

router = APIRouter()


@router.post("/process-interview")
async def process_interview(request: AudioProcessRequest):
    """
    Complete interview analysis endpoint
    
    This is the main endpoint for production interview processing.
    Always includes vocal analytics unless cheating is detected.
    
    Pipeline:
    1. Download, detects and extract media type (audio vs video)
    2. Transcribe with Whisper
    3. Detect filler words
    4. Speaker diarization
    5. Check for cheating
    6. IF no cheating → Run vocal analytics (speaking rate, pitch, energy, pauses)
    7. Return complete results
    
    Processing time: 5-10 minutes for 5-minute interview
    
    Use cases:
    - Called by interview orchestration service after interview submission
    - Results sent to next service for assessment
    """
    logger.info(f"Interview processing request received")
    logger.info(f"Media URL: {request.media_url}")
    logger.info(f"Session ID: {request.session_id}")
    logger.info(f"Candidate ID: {request.candidate_id}")
    
    processor = AudioProcessingService()
    
    # Always include analytics for interview processing
    result = processor.process(
        media_url=str(request.media_url),
        session_id=request.session_id,
        candidate_id=request.candidate_id,
        include_analytics=True  # Always run analytics (unless cheating detected)
    )
    
    # Log key results
    if result["status"] == "success":
        logger.info(f"Interview processing completed")
        logger.info(f"Cheating detected: {result.get('cheating_detected', False)}")
        logger.info(f"Analytics run: {result.get('analytics_run', False)}")
    else:
        logger.error(f"Interview processing failed: {result.get('error')}")
    
    return result


@router.post("/transcribe")
async def transcribe_media(request: AudioProcessRequest):
    """
    Transcribe media without analysis (faster)
    
    Use this endpoint when you only need the transcript, not filler detection or diarization.
    
    Processing time: ~30-60 seconds (vs 3-5 minutes for full analysis)
    
    Supported formats:
    - Audio: MP3, WAV, M4A, AAC, OGG, FLAC
    - Video: MP4, AVI, MOV, MKV, WEBM
    """
    from services.media_downloader import MediaDownloader
    from services.audio_extractor import AudioExtractor
    from services.transcription_service import TranscriptionService
    
    logger.info(f"Transcription-only request")
    logger.info(f"Media URL: {request.media_url}")
    logger.info(f"Session ID: {request.session_id}")
    
    downloader = MediaDownloader()
    extractor = AudioExtractor()
    transcriber = TranscriptionService()
    
    try:
        # Download media
        media_path, media_type, error = downloader.download(str(request.media_url))
        if error:
            return {
                "status": "failed",
                "message": "Media download failed",
                "media_url": str(request.media_url),
                "error": error
            }
        
        logger.info(f"Media type: {media_type}")
        
        # Get audio
        if media_type == 'audio':
            logger.info("Using audio file directly")
            audio_path = media_path
        else:
            logger.info("Extracting audio from video")
            audio_path, error = extractor.extract(media_path)
            if error:
                return {
                    "status": "failed",
                    "message": "Audio extraction failed",
                    "media_url": str(request.media_url),
                    "error": error
                }
        
        # Get duration
        duration = extractor.get_audio_duration(audio_path)
        logger.info(f"Audio duration: {duration:.2f}s")
        
        # Transcribe
        logger.info("Starting transcription...")
        transcription_result = transcriber.transcribe(audio_path)
        word_count = transcriber.get_word_count(transcription_result["text"])
        
        logger.info(f"Transcription complete: {word_count} words")
        
        return {
            "status": "success",
            "message": "Transcription completed successfully",
            "media_url": str(request.media_url),
            "media_type": media_type,
            "transcript": transcription_result["text"],
            "duration_seconds": duration,
            "word_count": word_count,
            "language": transcription_result["language"],
            "session_id": request.session_id,
            "candidate_id": request.candidate_id
        }
        
    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}", exc_info=True)
        return {
            "status": "failed",
            "message": "Transcription failed",
            "media_url": str(request.media_url),
            "error": str(e)
        }
    
    finally:
        downloader.cleanup()
        if media_type != 'audio':
            extractor.cleanup()

          