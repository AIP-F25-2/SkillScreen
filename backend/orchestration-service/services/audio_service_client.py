import httpx
from config.settings import settings
from config.logger import logger
from typing import Dict

class AudioServiceClient:
    def __init__(self):
        self.base_url = settings.AUDIO_AI_SERVICE_URL
        self.timeout = settings.AUDIO_TTS_TIMEOUT
    
    async def generate_speech(self, text: str, session_id: str = None, interview_id: str = None) -> Dict:
        """Generate TTS audio

        Args:
            text: Text to convert to speech
            session_id: Session ID (for legacy compatibility)
            interview_id: Interview ID (new approach)

        Returns:
            { success, data: { audio_url, ... } }
        """
        url = f"{self.base_url}/api/tts/generate"

        payload = {
            "text": text,
            "voice": "en-US-female"
        }

        # Support both session_id and interview_id
        if session_id:
            payload["session_id"] = session_id
        if interview_id:
            payload["interview_id"] = interview_id

        try:
            logger.info("🎵 Generating TTS audio")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

                data = response.json()

                # Handle standardized response format
                if data.get("success"):
                    return {
                        "success": True,
                        "data": {
                            "audio_url": data.get("data", {}).get("audio_url") or data.get("download_url"),
                            "filename": data.get("data", {}).get("filename") or data.get("filename")
                        }
                    }
                else:
                    # Legacy response format
                    return {
                        "success": True,
                        "data": {
                            "audio_url": data.get("download_url"),
                            "filename": data.get("filename")
                        }
                    }
        except Exception as e:
            logger.error(f"❌ TTS failed: {str(e)}")
            return {
                "success": False,
                "message": f"TTS generation failed: {str(e)}"
            }