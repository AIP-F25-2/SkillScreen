from fastapi import APIRouter
from fastapi.responses import FileResponse
from config import logger
from schemas.audio_schemas import TTSRequest, TTSResponse
from services.text_to_speech_service import TextToSpeechService
from services.audio_extractor import AudioExtractor
import os

router = APIRouter()


@router.post("/generate", response_model=TTSResponse)
async def generate_speech(request: TTSRequest):
    """
    Generate speech from text
    
    Other services call this endpoint to convert interview questions to audio
    """
    logger.info(f"TTS request received")
    logger.info(f"Text preview: {request.text[:100]}...")
    logger.info(f"Voice: {request.voice}")
    logger.info(f"Session ID: {request.session_id}")
    
    tts_service = TextToSpeechService()
    extractor = AudioExtractor()
    
    try:
        # Use async method directly (not sync wrapper)
        audio_path, error = await tts_service.synthesize(request.text, request.voice)
        
        if error:
            return TTSResponse(
                status="failed",
                message="Speech generation failed",
                text=request.text,
                session_id=request.session_id,
                error=error
            )
        
        duration = extractor.get_audio_duration(audio_path)
        
        logger.info(f"TTS: Audio generated at {audio_path}, duration: {duration}s")
        
        return TTSResponse(
            status="success",
            message="Speech generated successfully",
            audio_file_path=audio_path,
            text=request.text,
            voice=request.voice or "en-US-female",
            duration_seconds=duration,
            session_id=request.session_id
        )
        
    except Exception as e:
        logger.error(f"TTS generation failed: {str(e)}")
        return TTSResponse(
            status="failed",
            message="Unexpected error during speech generation",
            text=request.text,
            session_id=request.session_id,
            error=str(e)
        )
    
@router.get("/info")
async def get_tts_info():
    """Get current TTS provider configuration"""
    tts_service = TextToSpeechService()
    return {
        "provider": tts_service.get_current_provider(),
        "available_voices": tts_service.get_available_voices()
    }    

@router.get("/voices")
async def get_voices():
    """Get available TTS voices"""
    tts_service = TextToSpeechService()
    return {"voices": tts_service.get_available_voices()}


@router.get("/download/{filename}")
async def download_audio(filename: str):
    """Download generated audio file"""
    file_path = os.path.join("temp_audio", filename)
    
    if not os.path.exists(file_path):
        return {"status": "failed", "error": "File not found"}
    
    return FileResponse(
        file_path,
        media_type="audio/mpeg",
        filename=filename
    )