from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict


class BaseTTSProvider(ABC):
    """Abstract base class for TTS providers"""
    
    @abstractmethod
    async def synthesize(self, text: str, voice: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """
        Convert text to speech
        
        Args:
            text: Text to convert
            voice: Voice identifier
        
        Returns:
            (audio_path, error_message)
        """
        pass
    
    @abstractmethod
    def get_available_voices(self) -> Dict[str, str]:
        """Return available voices for this provider"""
        pass