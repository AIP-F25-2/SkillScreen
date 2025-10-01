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
    
    # Database
    DATABASE_URL: str = "mock://localhost"
    
    # API Keys
    API_KEY_HEADER: str = "X-API-Key"
    API_KEY: Optional[str] = None
    
    # Next service URL (for passing results)
    NEXT_SERVICE_API_URL: Optional[str] = None
    
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