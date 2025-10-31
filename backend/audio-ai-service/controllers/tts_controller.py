from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from services.text_to_speech_service import TextToSpeechService
from config import logger
import os

router = APIRouter()


class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = None
    session_id: Optional[str] = None


@router.post("/generate")
async def generate_speech(request: TTSRequest):
    """
    Generate speech from text (2-step: generate then download)
    
    Use this for pre-recorded questions or when you need the download URL
    """
    try:
        logger.info("TTS request received")
        logger.info(f"Text preview: {request.text[:100]}...")
        logger.info(f"Voice: {request.voice}")
        logger.info(f"Session ID: {request.session_id}")
        
        # Initialize TTS service
        tts_service = TextToSpeechService()
        
        # Generate speech
        audio_path, error = await tts_service.synthesize(
            text=request.text,
            voice=request.voice
        )
        
        if error or not audio_path:
            logger.error(f"TTS generation failed: {error}")
            raise HTTPException(
                status_code=500,
                detail=f"Speech generation failed: {error}"
            )
        
        filename = os.path.basename(audio_path)
        download_url = f"/api/tts/download/{filename}"
        
        logger.info(f"TTS generated successfully: {filename}")
        
        return {
            "status": "success",
            "message": "Speech generated successfully",
            "filename": filename,
            "download_url": download_url,
            "text": request.text,
            "voice": request.voice,
            "session_id": request.session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS generation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/download/{filename}")
async def download_audio(filename: str):
    """Download generated audio file"""
    try:
        # Construct file path
        file_path = os.path.join("temp_audio", filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail="Audio file not found"
            )
        
        return FileResponse(
            path=file_path,
            media_type="audio/mpeg",
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Download failed: {str(e)}"
        )


@router.post("/generate-stream")
async def generate_speech_stream(request: TTSRequest):
    """
    Generate speech and return audio file directly (single API call)
    
    Use this for live interviews - returns MP3 audio immediately
    """
    try:
        logger.info("TTS streaming request received")
        logger.info(f"Text preview: {request.text[:100]}...")
        logger.info(f"Voice: {request.voice}")
        
        # Initialize TTS service
        tts_service = TextToSpeechService()
        
        # Generate speech
        audio_path, error = await tts_service.synthesize(
            text=request.text,
            voice=request.voice
        )
        
        if error or not audio_path:
            logger.error(f"TTS generation failed: {error}")
            raise HTTPException(
                status_code=500,
                detail=f"Speech generation failed: {error}"
            )
        
        logger.info(f"TTS streaming generated successfully: {audio_path}")
        
        # Return audio file directly
        return FileResponse(
            path=audio_path,
            media_type="audio/mpeg",
            filename="question.mp3",
            headers={
                "Content-Disposition": "inline; filename=question.mp3",
                "Cache-Control": "no-cache"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS streaming error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/voices")
async def get_available_voices():
    """Get list of available voices"""
    try:
        tts_service = TextToSpeechService()
        voices = tts_service.get_available_voices()
        
        return {
            "status": "success",
            "provider": tts_service.get_current_provider(),
            "fallback": tts_service.get_fallback_provider(),
            "voices": voices
        }
        
    except Exception as e:
        logger.error(f"Error getting voices: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get voices: {str(e)}"
        )