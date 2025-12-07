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

    async def get_live_transcription(self, session_id: str) -> Dict:
        """Get live transcription from audio-ai service

        Args:
            session_id: Session ID to get transcription for

        Returns:
            { transcript: "what candidate said..." }
        """
        url = f"{self.base_url}/api/transcription/live/{session_id}"

        try:
            logger.info(f"🎤 Getting live transcription for session {session_id}")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()

                data = response.json()

                # Handle standardized response format
                if data.get("success"):
                    return {
                        "transcript": data.get("data", {}).get("transcript", "")
                    }
                else:
                    # Legacy response format
                    return {
                        "transcript": data.get("transcript", "")
                    }
        except Exception as e:
            logger.error(f"❌ Transcription failed: {str(e)}")
            raise

    async def analyze_audio(self, interview_id: str, session_id: str, media_file_id: str) -> Dict:
        """Trigger audio analysis (async, fire-and-forget)

        Args:
            interview_id: Interview ID
            session_id: Session ID
            media_file_id: Media file ID to analyze

        Returns:
            { success: true/false }
        """
        url = f"{self.base_url}/api/analysis/audio"

        payload = {
            "interview_id": interview_id,
            "session_id": session_id,
            "media_file_id": media_file_id
        }

        try:
            logger.info(f"🎵 Triggering audio analysis for media {media_file_id}")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"❌ Audio analysis trigger failed: {str(e)}")
            raise

    async def analyze_video(self, interview_id: str, session_id: str, media_file_id: str) -> Dict:
        """Trigger video analysis (async, fire-and-forget)

        Args:
            interview_id: Interview ID
            session_id: Session ID
            media_file_id: Media file ID to analyze

        Returns:
            { success: true/false }
        """
        url = f"{self.base_url}/api/analysis/video"

        payload = {
            "interview_id": interview_id,
            "session_id": session_id,
            "media_file_id": media_file_id
        }

        try:
            logger.info(f"📹 Triggering video analysis for media {media_file_id}")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"❌ Video analysis trigger failed: {str(e)}")
            raise

    async def transcribe_audio(self, media_url: str) -> Dict:
        """Transcribe audio file from media URL

        Args:
            media_url: URL to audio/video file to transcribe

        Returns:
            { transcript: "transcribed text..." }
        """
        url = f"{self.base_url}/api/audio/transcribe"

        payload = {
            "media_url": media_url
        }

        try:
            logger.info(f"🎤 Transcribing audio from {media_url}")
            # Transcription takes much longer, use dedicated timeout (600s = 10 minutes)
            transcription_timeout = settings.AUDIO_TRANSCRIPTION_TIMEOUT
            async with httpx.AsyncClient(timeout=transcription_timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

                data = response.json()

                if data.get("success"):
                    return {
                        "transcript": data.get("data", {}).get("transcript", "")
                    }
                else:
                    return {
                        "transcript": data.get("transcript", "")
                    }
        except Exception as e:
            logger.error(f"❌ Audio transcription failed: {str(e)}")
            raise