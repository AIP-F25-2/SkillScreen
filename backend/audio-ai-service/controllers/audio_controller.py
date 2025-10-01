from fastapi import APIRouter, HTTPException
from config import logger
from schemas.audio_schemas import AudioProcessRequest, AudioProcessResponse

router = APIRouter()

@router.post("/process", response_model=AudioProcessResponse)
async def process_audio(request: AudioProcessRequest):
    """
    Process audio from video URL
    This is a stub for Phase 1 - returns mock data
    """
    logger.info(f"Received audio processing request for video: {request.video_url}")
    
    # TODO: Phase 2 - Implement actual processing
    # For now, return mock response
    
    return AudioProcessResponse(
        status="success",
        message="Audio processing completed (mock)",
        video_url=request.video_url,
        transcript="This is a mock transcript for Phase 1 testing.",
        duration_seconds=120.5,
        word_count=25
    )