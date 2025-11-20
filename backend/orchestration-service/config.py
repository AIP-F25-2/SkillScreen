import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "orchestration-service"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/skillscreen")
    
    # Service URLs - Internal Docker network communication
    TEXT_SERVICE_URL: str = os.getenv("TEXT_SERVICE_URL", "http://text-service:8080")
    AUDIO_AI_SERVICE_URL: str = os.getenv("AUDIO_AI_SERVICE_URL", "http://audio-ai-service:8080")
    VIDEO_AI_SERVICE_URL: str = os.getenv("VIDEO_AI_SERVICE_URL", "http://video-ai-service:8080")
    MEDIA_SERVICE_URL: str = os.getenv("MEDIA_SERVICE_URL", "http://media-service:8080")
    INTERVIEW_SERVICE_URL: str = os.getenv("INTERVIEW_SERVICE_URL", "http://interview-service:8080")
    USER_SERVICE_URL: str = os.getenv("USER_SERVICE_URL", "http://user-service:8080")
    
    # Timeouts
    SERVICE_TIMEOUT: int = 300  # 5 minutes for service calls
    PROCESSING_TIMEOUT: int = 600  # 10 minutes for heavy processing
    
    # Interview Configuration
    MAX_QUESTIONS_PER_INTERVIEW: int = 15
    DEFAULT_INTERVIEW_DURATION_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

