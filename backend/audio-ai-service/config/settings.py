from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "audio-ai-service"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # File Storage
    TEMP_AUDIO_DIR: str = "./temp_audio"
    MAX_FILE_SIZE_MB: int = 500
    
    # Model Settings
    WHISPER_MODEL_SIZE: str = "base"  # tiny, base, small, medium, large
    WHISPER_DEVICE: str = "cpu"  # cpu or cuda
    MODEL_CACHE_DIR: str = "./models"
    
    # Processing Settings
    MAX_VIDEO_DURATION_MINUTES: int = 30
    PROCESSING_TIMEOUT_SECONDS: int = 600
    ENABLE_DIARIZATION: bool = True
    ENABLE_FILLER_DETECTION: bool = True
    
    # Database
    DATABASE_URL: str = "mock://localhost"
    
    # API Keys
    API_KEY_HEADER: str = "X-API-Key"
    API_KEY: Optional[str] = None
    
    # HuggingFace (for pyannote.audio)
    HUGGINGFACE_TOKEN: Optional[str] = None  # Token for accessing Hugging Face models
    
    # Next service URL (for passing results)
    NEXT_SERVICE_API_URL: Optional[str] = None


        # TTS Configuration
    TTS_PROVIDER: str = "gtts"  # Options: gtts, edge, azure, aws
    TTS_DEFAULT_VOICE: str = "en-US-female"
    
    # Azure TTS (if using Azure)
    AZURE_TTS_KEY: Optional[str] = None
    AZURE_TTS_REGION: Optional[str] = None
    
    # AWS Polly (if using AWS)
    AWS_ACCESS_KEY: Optional[str] = None
    AWS_SECRET_KEY: Optional[str] = None
    AWS_REGION: Optional[str] = "us-east-1"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def create_directories(self):
        """Create necessary directories if they don't exist"""
        Path(self.TEMP_AUDIO_DIR).mkdir(parents=True, exist_ok=True)
        Path(self.MODEL_CACHE_DIR).mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
settings.create_directories()