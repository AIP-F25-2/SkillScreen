from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "orchestration-service"
    PORT: int = 8080
    HOST: str = "0.0.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    INTERVIEW_SERVICE_URL: str = "http://interview-service:8080"
    TEXT_SERVICE_URL: str = "http://text-ai-service:8080"  # Note: text-ai-service, not text-service
    AUDIO_AI_SERVICE_URL: str = "http://audio-ai-service:8080"
    VIDEO_AI_SERVICE_URL: str = "http://video-ai-service:8080"
    MEDIA_SERVICE_URL: str = "http://media-service:8080"
    ASSESSMENT_SERVICE_URL: str = "http://assessment-service:8005"
    
    INTERVIEW_SERVICE_TIMEOUT: int = 60
    TEXT_SERVICE_TIMEOUT: int = 30
    AUDIO_TTS_TIMEOUT: int = 15
    AUDIO_TRANSCRIPTION_TIMEOUT: int = 600
    MEDIA_SERVICE_TIMEOUT: int = 120
    AI_SERVICE_TIMEOUT: int = 5
    ASSESSMENT_SERVICE_TIMEOUT: int = 30
    
    CORS_ORIGINS: str = "http://localhost:3000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"

settings = Settings()