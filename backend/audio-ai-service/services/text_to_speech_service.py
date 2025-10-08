from config import logger, settings
from typing import Optional, Tuple, Dict
from services.tts_providers.gtts_provider import GTTSProvider
from services.tts_providers.base_tts import BaseTTSProvider


class TextToSpeechService:
    """TTS service with configurable provider"""
    
    def __init__(self):
        self.provider = self._get_provider()
        logger.info(f"TTS Service initialized with provider: {settings.TTS_PROVIDER}")
    
    def _get_provider(self) -> BaseTTSProvider:
        """Factory method to get TTS provider based on config"""
        provider_name = settings.TTS_PROVIDER.lower()
        
        if provider_name == "gtts":
            return GTTSProvider()
        
        # Add more providers here:
        # elif provider_name == "azure":
        #     return AzureTTSProvider()
        # elif provider_name == "aws":
        #     return AWSPollyProvider()
        else:
            logger.warning(f"Unknown TTS provider '{provider_name}', defaulting to gTTS")
            return GTTSProvider()
    
    async def synthesize(self, text: str, voice: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """Delegate to configured provider"""
        return await self.provider.synthesize(text, voice)
    
    def get_available_voices(self) -> Dict[str, str]:
        """Get voices from configured provider"""
        return self.provider.get_available_voices()
    
    def get_current_provider(self) -> str:
        """Return current provider name"""
        return settings.TTS_PROVIDER