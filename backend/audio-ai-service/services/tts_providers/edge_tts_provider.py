import edge_tts
import os
from config import logger
from utils.file_utils import create_temp_file
from typing import Optional, Tuple, Dict
from .base_tts import BaseTTSProvider


class EdgeTTSProvider(BaseTTSProvider):
    """EdgeTTS Provider - Microsoft Azure Neural Voices"""
    
    VOICES = {
        "en-US-female": "en-US-AriaNeural",
        "en-US-male": "en-US-GuyNeural",
        "en-GB-female": "en-GB-SoniaNeural",
        "en-GB-male": "en-GB-RyanNeural",
        "en-AU-female": "en-AU-NatashaNeural",
        "en-IN-female": "en-IN-NeerjaNeural",
    }
    
    def __init__(self):
        self.default_voice = "en-US-AriaNeural"
    
    async def synthesize(self, text: str, voice: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """
        Convert text to speech using EdgeTTS
        
        Args:
            text: Text to convert
            voice: Voice identifier
        
        Returns:
            (audio_path, error_message)
        """
        try:
            # Select voice
            voice_name = self.VOICES.get(voice, self.default_voice)
            
            logger.info(f"TTS (EdgeTTS): Generating speech, voice: {voice_name}")
            
            # Create temp file
            audio_path = create_temp_file(suffix=".mp3")
            
            # Create EdgeTTS communicator
            communicate = edge_tts.Communicate(text, voice_name)
            
            # Generate and save audio
            await communicate.save(audio_path)
            
            logger.info(f"TTS (EdgeTTS): Success - {audio_path}")
            return audio_path, None
            
        except Exception as e:
            error_msg = f"EdgeTTS error: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
    
    def get_available_voices(self) -> Dict[str, str]:
        """Return available voices"""
        return self.VOICES