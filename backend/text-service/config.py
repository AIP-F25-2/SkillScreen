"""
Configuration management for SkillScreen Text Service
"""

import os
import json
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for SkillScreen Text Service"""
    
    def __init__(self):
        self.config_file = "config.json"
        self.config_data = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from config.json file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            else:
                return self._get_default_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "debug": False,
            "environment": "development",
            "version": "1.0.0",
            "database": {
                "url": os.getenv("DATABASE_URL", "sqlite:///./text_service.db"),
                "echo": False
            },
            "llm": {
                "api_key": os.getenv("GEMINI_API_KEY", ""),
                "model_name": "models/gemini-2.5-flash",
                "temperature": 1.0,
                "max_tokens": 200,
                "timeout": 30
            },
            "logging": {
                "level": "INFO",
                "file_path": "logs/skillscreen.log",
                "max_file_size": "10MB",
                "backup_count": 5,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "date_format": "%Y-%m-%d %H:%M:%S"
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        keys = key.split('.')
        value = self.config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_database_url(self) -> str:
        """Get database URL"""
        return self.get("database.url", "sqlite:///./text_service.db")
    
    def get_llm_api_key(self) -> str:
        """Get LLM API key"""
        return self.get("llm.api_key", "")
    
    def is_debug(self) -> bool:
        """Check if debug mode is enabled"""
        return self.get("debug", False)

# Global config instance
config = Config()
