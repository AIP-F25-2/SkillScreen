from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "text-ai-service"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Logging
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = ""  # Will be set via environment variable

    # LLM Configuration
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    MAX_TOKENS_RESPONSE: int = 2000
    TEMPERATURE: float = 0.7

    # Interview Settings
    DEFAULT_INTERVIEW_DURATION_MINUTES: int = 30
    QUESTIONS_PER_INTERVIEW: int = 5
    ENABLE_FOLLOW_UP_QUESTIONS: bool = True
    ENABLE_NLP_EVALUATION: bool = True

    # TTS Configuration
    TTS_PROVIDER: str = "edge"  # Options: gtts, edge, azure, aws
    TTS_DEFAULT_VOICE: str = "en-US-AriaNeural"
    AZURE_TTS_KEY: Optional[str] = None
    AZURE_TTS_REGION: Optional[str] = None
    AWS_ACCESS_KEY: Optional[str] = None
    AWS_SECRET_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"

    # Service URLs
    SERVICE_BASE_URL: str = "http://text-ai-service:8000"
    AUDIO_SERVICE_URL: Optional[str] = None
    ORCHESTRATION_SERVICE_URL: Optional[str] = None

    # API Keys
    API_KEY_HEADER: str = "X-API-Key"
    API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True

    def is_debug(self) -> bool:
        """Check if running in debug mode"""
        return self.DEBUG


# Global settings instance
settings = Settings()
