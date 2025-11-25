import httpx
from config.settings import settings
from config.logger import logger
from typing import Dict

class AudioServiceClient:
    def __init__(self):
        self.base_url = settings.AUDIO_AI_SERVICE_URL
        self.timeout = settings.AUDIO_TTS_TIMEOUT
    
    async def generate_speech(self, text: str, session_id: str) -> Dict:
        """Generate TTS audio"""
        url = f"{self.base_url}/api/tts/generate"
        
        payload = {
            "text": text,
            "voice": "en-US-female",
            "session_id": session_id
        }
        
        try:
            logger.info("🎵 Generating TTS audio")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
                data = response.json()
                return {
                    "status": data.get("status"),
                    "download_url": data.get("download_url"),
                    "filename": data.get("filename")
                }
        except Exception as e:
            logger.error(f"❌ TTS failed: {str(e)}")
            raise