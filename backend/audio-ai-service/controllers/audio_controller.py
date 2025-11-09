from fastapi import APIRouter, HTTPException, BackgroundTasks
from config import logger, settings
from schemas.audio_schemas import AudioProcessRequest, AudioProcessResponse, ProcessInterviewAudioRequest, ProcessInterviewAudioResponse
from services.audio_processing_service import AudioProcessingService

from pydantic import BaseModel, Field
from uuid import UUID
from fastapi import status
from services.interview_audio_processing_service import InterviewAudioProcessingService
from repositories.audio_repository import AudioRepository
from datetime import datetime, timezone

from db import UnitOfWork


router = APIRouter()


@router.post(
    "/process-interview-audio",
    response_model=ProcessInterviewAudioResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Process interview audio (async)",
    description="""
    Process interview audio/video with complete analysis pipeline.
    
    **Flow:**
    1. Receives request with interview IDs and blob name
    2. Returns 202 Accepted immediately
    3. Processes in background (3-5 minutes)
    4. Updates media_files.status and saves results
    
    **Called by:** Interview Service after candidate submits answer
    """
)
async def process_interview_audio_endpoint(request: ProcessInterviewAudioRequest):
    """
    Main API endpoint for interview audio processing
    
    Validates request and starts background processing
    Returns immediately (asynchronous)
    """
    logger.info(f"📨 Audio processing request received")
    logger.info(f"   Interview: {request.interview_id}")
    logger.info(f"   Session: {request.session_id}")
    logger.info(f"   Media File: {request.media_file_id}")
    
    try:
        # Validate: Check if media file exists
        uow = UnitOfWork()
        repo = AudioRepository(uow)
        
        media_file = repo.get_media_file_by_id(str(request.media_file_id))
        
        if not media_file:
            logger.error(f"❌ Media file not found: {request.media_file_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Media file {request.media_file_id} not found"
            )
        
        # Check if already processed (idempotency)
        if repo.check_if_already_processed(
            str(request.interview_id),
            str(request.session_id)
        ):
            logger.warning(f"⚠️ Already processed - returning success")
            return ProcessInterviewAudioResponse(
                status="accepted",
                message="Already processed (idempotent)",
                media_file_id=str(request.media_file_id),
                interview_id=str(request.interview_id),
                session_id=str(request.session_id)
            )
        
        
        
        # Start background processing via service layer
        processing_service = InterviewAudioProcessingService()
        processing_service.process_async(
            interview_id=str(request.interview_id),
            session_id=str(request.session_id),
            media_file_id=str(request.media_file_id),
            blob_name=request.blob_name
        )
        
        logger.info(f"✅ Background processing started")
        
        # Return immediate response
        return ProcessInterviewAudioResponse(
            status="accepted",
            message="Audio processing started in background",
            media_file_id=str(request.media_file_id),
            interview_id=str(request.interview_id),
            session_id=str(request.session_id)
        )
        
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"❌ Failed to start processing: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start audio processing: {str(e)}"
        )


@router.get(
    "/audio-status/{media_file_id}",
    summary="Check audio processing status",
    description="Get current processing status of a media file"
)
async def get_audio_processing_status(media_file_id: UUID):
    """
    Check processing status of a media file
    
    Returns:
    - status: 'pending', 'processing', 'completed', 'failed'
    - extra: Error details if failed
    """
    try:
        uow = UnitOfWork()
        repo = AudioRepository(uow)
        
        media_file = repo.get_media_file_by_id(str(media_file_id))
        
        if not media_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Media file {media_file_id} not found"
            )
        
        
        
        return {
            "media_file_id": str(media_file_id),
            "status": media_file.get('status', 'pending'),
            "extra": media_file.get('extra', {}),
            "updated_at": media_file.get('updated_at')
        }
        
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Failed to get status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )




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

          