from fastapi import APIRouter, HTTPException, BackgroundTasks
from config import logger, settings
from schemas.audio_schemas import AudioProcessRequest, AudioProcessResponse
from services.audio_processing_service import AudioProcessingService

router = APIRouter()


@router.post("/process", response_model=AudioProcessResponse)
async def process_audio(request: AudioProcessRequest):
    """
    Process audio from video URL - Production endpoint
    
    This endpoint performs complete audio analysis:
    1. Downloads video from provided URL
    2. Extracts audio track
    3. Transcribes using Whisper ASR
    4. Detects filler words with timestamps
    5. Performs speaker diarization
    6. Assesses cheating risk based on multiple speakers
    
    Returns comprehensive analysis including:
    - Full transcript
    - Filler word analysis (counts, timestamps, rate)
    - Speaker detection (number of speakers, time distribution)
    - Cheating risk assessment
    
    Processing time: ~3-5 minutes for a 5-minute video
    """
    logger.info(f"Received audio processing request")
    logger.info(f"Video URL: {request.video_url}")
    logger.info(f"Session ID: {request.session_id}")
    logger.info(f"Candidate ID: {request.candidate_id}")
    
    # Initialize processing service
    processor = AudioProcessingService()
    
    # Process the audio
    result = processor.process(
        video_url=str(request.video_url),
        session_id=request.session_id,
        candidate_id=request.candidate_id
    )
    
    # Return result
    if result["status"] == "failed":
        logger.error(f"Processing failed: {result.get('error')}")
        # Still return 200 with error details in body
        # (Alternative: raise HTTPException(status_code=500))
    
    return AudioProcessResponse(**result)