from gtts import gTTS
from config import logger
from utils.file_utils import create_temp_file
from typing import Optional, Tuple, Dict
from .base_tts import BaseTTSProvider


class GTTSProvider(BaseTTSProvider):
    """Google TTS provider"""
    
    VOICES = {
        "en-US": "en",
        "en-GB": "en-gb",
        "en-IN": "en-in",
        "en-AU": "en-au"
    }
    
    def __init__(self):
        self.default_lang = "en"
    
    async def synthesize(self, text: str, voice: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        try:
            lang = voice or self.default_lang
            if lang not in self.VOICES.values():
                lang = self.VOICES.get(voice, self.default_lang)
            
            logger.info(f"TTS (gTTS): Generating speech, lang: {lang}")
            
            audio_path = create_temp_file(suffix=".mp3")
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(audio_path)
            
            logger.info(f"TTS (gTTS): Success - {audio_path}")
            return audio_path, None
            
        except Exception as e:
            error_msg = f"gTTS error: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
    
    def get_available_voices(self) -> Dict[str, str]:
        return self.VOICES