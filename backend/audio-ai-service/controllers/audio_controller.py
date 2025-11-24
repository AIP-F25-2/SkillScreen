from fastapi import APIRouter, HTTPException, BackgroundTasks
from config import logger, settings
from schemas.audio_schemas import AudioProcessRequest, AudioProcessResponse, ProcessInterviewAudioRequest, ProcessInterviewAudioResponse, CandidateAudioAnalysisResponse, CandidateTranscriptsResponse
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
    1. Receives request with interview IDs, media file ID and session ID
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
    logger.info("Audio processing request received")
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
        # Extract storage_uri from media_file record
        storage_uri = media_file.get('storage_uri') if isinstance(media_file, dict) else media_file.storage_uri

        if not storage_uri:
            logger.error(f"❌ Storage URI missing for media file: {request.media_file_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Storage URI missing for media file {request.media_file_id}"
            )
        logger.info(f"storage_uri: {storage_uri}")

        
        # Check if already processed (idempotency)
        if repo.check_if_already_processed(
            str(request.interview_id),
            str(request.session_id)
        ):
            logger.warning("⚠️Already processed - returning success")
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
            storage_uri=storage_uri
        )
        
        logger.info("✅Background processing started")
        
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


@router.get(
    "/candidate-transcripts/{candidate_id}",
    response_model=CandidateTranscriptsResponse,
    summary="Get candidate transcripts",
    description="Get all transcripts with word-level timestamps and transcription confidence"
)
async def get_candidate_transcripts(candidate_id: str):
    """
    Get all transcripts for a candidate
    
    Returns transcription details with:
    - Full text transcripts
    - Word-level timestamps with Whisper probabilities
    - Transcription confidence (Whisper accuracy)
    """
    try:
        logger.info(f"📝 Fetching transcripts for candidate: {candidate_id}")
        
        uow = UnitOfWork()
        repo = AudioRepository(uow)
        
        # Get candidate info
        candidate_name = repo.get_candidate_name(candidate_id)
        
        if not candidate_name:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate {candidate_id} not found in the system"
            )
        
        # Check if candidate has any interviews
        has_interviews = repo.check_candidate_has_interviews(candidate_id)
        
        if not has_interviews:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No interviews scheduled or completed for candidate '{candidate_name}'. The candidate has not taken any interviews yet."
            )
        
        # Get transcripts
        transcripts = repo.get_candidate_transcripts(candidate_id)
        
        if not transcripts:
            # Interviews exist but no transcripts = processing not done
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transcripts not available for candidate '{candidate_name}'. The interview recordings are still being processed or analysis has not started yet. Please check back in a few minutes."
            )
        
        # Format transcripts
        formatted_transcripts = [_format_transcript_detail(t) for t in transcripts]
        
        # Calculate summary
        summary = _calculate_transcript_summary(formatted_transcripts)
        
        logger.info(f"✅ Found {len(transcripts)} transcripts for {candidate_name}")
        
        return CandidateTranscriptsResponse(
            candidate_id=candidate_id,
            candidate_name=candidate_name,
            total_sessions=len({t['session_id'] for t in transcripts}),
            transcripts=formatted_transcripts,
            summary=summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get transcripts: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve transcripts: {str(e)}"
        )


@router.get(
    "/candidate-audio-analysis/{candidate_id}",
    response_model=CandidateAudioAnalysisResponse,
    summary="Get candidate audio analysis",
    description="Get candidate speaking performance: confidence, fillers, vocal quality, cheating detection"
)
async def get_candidate_audio_analysis(candidate_id: str):
    """
    Get audio performance analysis for a candidate
    
    Returns candidate speaking metrics:
    - Candidate confidence score (0-10)
    - Communication quality
    - Filler word analysis
    - Vocal analytics
    - Cheating detection
    """
    try:
        logger.info(f"🎤 Fetching audio analysis for candidate: {candidate_id}")
        
        uow = UnitOfWork()
        repo = AudioRepository(uow)
        
        # Get candidate info
        candidate_name = repo.get_candidate_name(candidate_id)
        
        if not candidate_name:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate {candidate_id} not found in the system"
            )
        
        # Check if candidate has any interviews
        has_interviews = repo.check_candidate_has_interviews(candidate_id)
        
        if not has_interviews:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No interviews scheduled or completed for candidate '{candidate_name}'. The candidate has not taken any interviews yet."
            )
        
        # Get analyses
        analyses = repo.get_candidate_audio_analyses(candidate_id)
        
        if not analyses:
            # Interviews exist but no analyses = processing not done
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Audio analysis not available for candidate '{candidate_name}'. The interview recordings are still being processed or analysis has not completed yet. Please check back in a few minutes."
            )
        
        # Format analyses
        formatted_analyses = [_format_audio_analysis_detail(a) for a in analyses]
        
        # Calculate summary
        summary = _calculate_audio_analysis_summary(formatted_analyses)
        
        logger.info(f"✅ Found {len(analyses)} audio analyses for {candidate_name}")
        
        return CandidateAudioAnalysisResponse(
            candidate_id=candidate_id,
            candidate_name=candidate_name,
            total_sessions=len({a['session_id'] for a in analyses}),
            analyses=formatted_analyses,
            summary=summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get audio analysis: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audio analysis: {str(e)}"
        )


# Helper functions
def _format_transcript_detail(transcript: dict) -> dict:
    """Format transcript with full details"""
    text = transcript.get('text', '')
    word_count = len(text.split()) if text else 0
    start = transcript.get('start_time', 0)
    end = transcript.get('end_time', 0)
    
    return {
        "interview_id": str(transcript['interview_id']),
        "session_id": str(transcript['session_id']),
        "question_number": transcript.get('question_number'),
        "speaker": transcript.get('speaker', 'candidate'),
        "text": text,
        "transcription_confidence": transcript.get('confidence_score', 0.0),
        "start_time": start,
        "end_time": end,
        "duration_seconds": round(end - start, 2),
        "word_count": word_count,
        "word_timestamps": transcript.get('word_timestamps', []),
        "created_at": transcript.get('created_at')
    }


def _calculate_transcript_summary(transcripts: list) -> dict:
    """Calculate transcript summary statistics"""
    total_words = sum(t['word_count'] for t in transcripts)
    total_time = sum(t['duration_seconds'] for t in transcripts)
    
    confidences = [t['transcription_confidence'] for t in transcripts if t['transcription_confidence']]
    avg_confidence = round(sum(confidences) / len(confidences), 3) if confidences else 0
    
    avg_wpm = round((total_words / total_time) * 60, 1) if total_time > 0 else 0
    
    return {
        "total_words": total_words,
        "total_speaking_time_seconds": round(total_time, 1),
        "avg_transcription_confidence": avg_confidence,
        "avg_words_per_minute": avg_wpm
    }


def _format_audio_analysis_detail(analysis: dict) -> dict:
    """Format audio analysis with performance metrics"""
    raw_results = analysis.get('raw_results', {})
    
    return {
        "interview_id": str(analysis['interview_id']),
        "session_id": str(analysis['session_id']),
        "question_number": analysis.get('question_number'),
        "candidate_confidence_score": analysis.get('confidence_score'),
        "communication_score": raw_results.get('communication_score', {}).get('communication_score'),
        "filler_analysis": raw_results.get('filler_analysis', {}),
        "vocal_analytics": raw_results.get('vocal_analytics', {}),
        "speaker_analysis": raw_results.get('speaker_analysis', {}),
        "reading_detection": raw_results.get('reading_detection'),
        "processing_time_seconds": analysis.get('processing_time', 0),
        "created_at": analysis.get('created_at')
    }


def _calculate_audio_analysis_summary(analyses: list) -> dict:
    """Calculate audio performance summary"""
    
    # Candidate confidence (0-10 scale)
    confidence_scores = [a['candidate_confidence_score'] for a in analyses if a['candidate_confidence_score']]
    avg_confidence = round(sum(confidence_scores) / len(confidence_scores), 2) if confidence_scores else 0
    
    # Communication scores
    comm_scores = [a['communication_score'] for a in analyses if a['communication_score']]
    avg_comm = round(sum(comm_scores) / len(comm_scores), 2) if comm_scores else 0
    
    # Fillers
    total_fillers = sum(a['filler_analysis'].get('total_fillers', 0) for a in analyses)
    filler_rates = [a['filler_analysis'].get('filler_rate_per_minute', 0) for a in analyses]
    avg_filler_rate = round(sum(filler_rates) / len(filler_rates), 2) if filler_rates else 0
    
    # Speaking rate
    speaking_rates = [
        a['vocal_analytics'].get('speaking_rate', {}).get('words_per_minute', 0) 
        for a in analyses 
        if a.get('vocal_analytics')
    ]
    avg_speaking_rate = round(sum(speaking_rates) / len(speaking_rates), 1) if speaking_rates else 0
    
    # Cheating incidents
    cheating_incidents = sum(
        1 for a in analyses 
        if a['speaker_analysis'].get('cheating_flag', False)
    )
    
    return {
        "avg_candidate_confidence": avg_confidence,
        "avg_communication_score": avg_comm,
        "total_fillers": total_fillers,
        "avg_filler_rate_per_minute": avg_filler_rate,
        "cheating_incidents": cheating_incidents,
        "avg_speaking_rate_wpm": avg_speaking_rate
    }            

          