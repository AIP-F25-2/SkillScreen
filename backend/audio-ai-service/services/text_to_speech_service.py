from config import logger, settings
from typing import Optional, Tuple, Dict
from services.tts_providers.gtts_provider import GTTSProvider
from services.tts_providers.edge_tts_provider import EdgeTTSProvider
from services.tts_providers.base_tts import BaseTTSProvider


class TTSProviderError(Exception):
    """Exception raised when a TTS provider fails to synthesize speech"""
    pass


class TextToSpeechService:
    """TTS service with configurable provider and automatic fallback"""
    
    def __init__(self):
        self.primary_provider = self._get_provider(settings.TTS_PROVIDER)
        self.fallback_provider = GTTSProvider()  # Always use gTTS as fallback
        logger.info(f"TTS Service initialized with primary: {settings.TTS_PROVIDER}, fallback: gTTS")
    
    def _get_provider(self, provider_name: str) -> BaseTTSProvider:
        """Factory method to get TTS provider based on name"""
        provider_name = provider_name.lower()
        
        if provider_name == "gtts":
            return GTTSProvider()
        elif provider_name == "edge" or provider_name == "edgetts":
            return EdgeTTSProvider()
        else:
            logger.warning(f"Unknown TTS provider '{provider_name}', defaulting to gTTS")
            return GTTSProvider()
    
    async def synthesize(self, text: str, voice: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """
        Synthesize speech with automatic fallback
        
        Tries primary provider first, falls back to gTTS if it fails
        """
        # Try primary provider
        try:
            logger.info(f"Attempting TTS with primary provider: {settings.TTS_PROVIDER}")
            audio_path, error = await self.primary_provider.synthesize(text, voice)

            if audio_path:
                logger.info(f"✅ Primary provider ({settings.TTS_PROVIDER}) succeeded")
                return audio_path, None
            else:
                logger.warning(f"⚠️ Primary provider ({settings.TTS_PROVIDER}) failed: {error}")
                raise TTSProviderError(error)

        except TTSProviderError as e:
            logger.error(f"❌ Primary provider ({settings.TTS_PROVIDER}) error: {str(e)}")
            logger.info("🔄 Falling back to gTTS...")

            # Fallback to gTTS
            try:
                audio_path, error = await self.fallback_provider.synthesize(text, voice)

                if audio_path:
                    logger.info("✅ Fallback provider (gTTS) succeeded")
                    return audio_path, None
                else:
                    logger.error(f"❌ Fallback provider (gTTS) also failed: {error}")
                    return None, f"Both providers failed. Primary: {str(e)}, Fallback: {error}"

            except TTSProviderError as fallback_error:
                logger.error(f"❌ Fallback provider (gTTS) error: {str(fallback_error)}")
                return None, f"Both providers failed. Primary: {str(e)}, Fallback: {str(fallback_error)}"
    
    def get_available_voices(self) -> Dict[str, str]:
        """Get voices from primary provider"""
        return self.primary_provider.get_available_voices()
    
    def get_current_provider(self) -> str:
        """Return current provider name"""
        return settings.TTS_PROVIDER
    
    def get_fallback_provider(self) -> str:
        """Return fallback provider name"""
        return "gTTS"