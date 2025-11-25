from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    
    # Database Configuration
    database_url: str = Field(..., alias="DATABASE_URL")
    
    # Service Configuration
    service_name: str = Field(default="assessment-service", alias="SERVICE_NAME")
    service_port: int = Field(default=8005, alias="SERVICE_PORT")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    
    # Assessment Scheduler Configuration
    assessment_check_interval_minutes: int = Field(default=10, alias="ASSESSMENT_CHECK_INTERVAL_MINUTES")
    assessment_grace_period_minutes: int = Field(default=5, alias="ASSESSMENT_GRACE_PERIOD_MINUTES")
    
    # LLM Configuration (Groq API)
    groq_api_key: str = Field(..., alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.1-70b-versatile", alias="GROQ_MODEL")
    llm_max_tokens: int = Field(default=4096, alias="LLM_MAX_TOKENS")
    llm_temperature: float = Field(default=0.3, alias="LLM_TEMPERATURE")
    use_llm_weights: bool = Field(default=True, alias="USE_LLM_WEIGHTS")  # Enable/disable LLM weight determination
    
    # Default Scoring Weights (with coding)
    default_weight_coding: float = Field(default=0.40, alias="DEFAULT_WEIGHT_CODING")
    default_weight_text: float = Field(default=0.20, alias="DEFAULT_WEIGHT_TEXT")
    default_weight_audio: float = Field(default=0.20, alias="DEFAULT_WEIGHT_AUDIO")
    default_weight_video: float = Field(default=0.20, alias="DEFAULT_WEIGHT_VIDEO")
    
    # Default Weights (no coding)
    default_weight_text_no_coding: float = Field(default=0.34, alias="DEFAULT_WEIGHT_TEXT_NO_CODING")
    default_weight_audio_no_coding: float = Field(default=0.33, alias="DEFAULT_WEIGHT_AUDIO_NO_CODING")
    default_weight_video_no_coding: float = Field(default=0.33, alias="DEFAULT_WEIGHT_VIDEO_NO_CODING")
    
    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")
    
    # CORS Settings
    # Must be set via ALLOWED_ORIGINS environment variable
    allowed_origins: str = Field( 
        default="",
        alias="ALLOWED_ORIGINS"
    )
    
    # Health Check
    health_check_timeout_seconds: int = Field(default=30, alias="HEALTH_CHECK_TIMEOUT_SECONDS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"
    
   
    @property
    def cors_origins_list(self) -> list[str]:
        """Convert comma-separated CORS origins to list"""
        if not self.allowed_origins:
            raise ValueError(
                "ALLOWED_ORIGINS environment variable is required. "
                "Example: ALLOWED_ORIGINS=https://app.example.com"
        )
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    
    @property
    def default_weights_with_coding(self) -> dict[str, float]:
        """Get default weights when coding is included"""
        return {
            "coding": self.default_weight_coding,
            "text": self.default_weight_text,
            "audio": self.default_weight_audio,
            "video": self.default_weight_video
        }
    
    @property
    def default_weights_without_coding(self) -> dict[str, float]:
        """Get default weights when coding is not included"""
        return {
            "text": self.default_weight_text_no_coding,
            "audio": self.default_weight_audio_no_coding,
            "video": self.default_weight_video_no_coding
        }


# Create global settings instance
settings = Settings()