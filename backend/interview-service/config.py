"""
Configuration management for SkillScreen
Handles all application settings and environment variables
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class InterviewConfig:
    """Interview-specific configuration"""
    max_questions: int = 15
    min_questions: int = 10
    target_duration_minutes: int = 12
    general_questions: int = 4
    technical_questions: int = 6
    theoretical_questions: int = 5
    off_topic_threshold: float = 0.3
    max_off_topic_responses: int = 3
    default_interview_type: str = "mixed"
    default_difficulty: str = "medium"
    context_window: int = 5

@dataclass
class LLMConfig:
    """LLM integration configuration"""
    api_key: str = ""
    model_name: str = "gemini-pro"
    temperature: float = 0.7
    max_tokens: int = 200
    timeout: int = 30

@dataclass
class UIConfig:
    """User interface configuration"""
    server_port: int = 8501
    server_address: str = "0.0.0.0"
    theme: str = "light"
    page_title: str = "SkillScreen - AI Interview Assistant"
    page_icon: str = "🎯"

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    file_path: str = "logs/skillscreen.log"
    max_file_size: str = "10MB"
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"

@dataclass
class SecurityConfig:
    """Security configuration"""
    secret_key: str = ""
    session_timeout: int = 3600  # 1 hour
    max_sessions: int = 100
    enable_encryption: bool = True

@dataclass
class AppConfig:
    """Main application configuration"""
    debug: bool = False
    environment: str = "development"
    version: str = "1.0.0"
    interview: InterviewConfig = None
    llm: LLMConfig = None
    ui: UIConfig = None
    logging: LoggingConfig = None
    security: SecurityConfig = None
    
    def __post_init__(self):
        if self.interview is None:
            self.interview = InterviewConfig()
        if self.llm is None:
            self.llm = LLMConfig()
        if self.ui is None:
            self.ui = UIConfig()
        if self.logging is None:
            self.logging = LoggingConfig()
        if self.security is None:
            self.security = SecurityConfig()

class ConfigManager:
    """Configuration manager for SkillScreen"""
    
    def __init__(self, config_file: str = "config.json"):
        """Initialize configuration manager"""
        self.config_file = Path(config_file)
        self.config = AppConfig()
        self._load_config()
        self._setup_logging()
    
    def _load_config(self):
        """Load configuration from file and environment variables"""
        # Load from config file if it exists
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    self._update_config_from_dict(config_data)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
        
        # Override with environment variables
        self._load_from_environment()
    
    def _update_config_from_dict(self, config_data: Dict[str, Any]):
        """Update configuration from dictionary"""
        try:
            # Update main config
            if 'debug' in config_data:
                self.config.debug = config_data['debug']
            if 'environment' in config_data:
                self.config.environment = config_data['environment']
            if 'version' in config_data:
                self.config.version = config_data['version']
            
            # Update interview config
            if 'interview' in config_data:
                interview_data = config_data['interview']
                self.config.interview.max_questions = interview_data.get('max_questions', self.config.interview.max_questions)
                self.config.interview.min_questions = interview_data.get('min_questions', self.config.interview.min_questions)
                self.config.interview.off_topic_threshold = interview_data.get('off_topic_threshold', self.config.interview.off_topic_threshold)
                self.config.interview.max_off_topic_responses = interview_data.get('max_off_topic_responses', self.config.interview.max_off_topic_responses)
                self.config.interview.default_interview_type = interview_data.get('default_interview_type', self.config.interview.default_interview_type)
                self.config.interview.default_difficulty = interview_data.get('default_difficulty', self.config.interview.default_difficulty)
                self.config.interview.context_window = interview_data.get('context_window', self.config.interview.context_window)
            
            # Update LLM config
            if 'llm' in config_data:
                llm_data = config_data['llm']
                self.config.llm.api_key = llm_data.get('api_key', self.config.llm.api_key)
                self.config.llm.model_name = llm_data.get('model_name', self.config.llm.model_name)
                self.config.llm.temperature = llm_data.get('temperature', self.config.llm.temperature)
                self.config.llm.max_tokens = llm_data.get('max_tokens', self.config.llm.max_tokens)
                self.config.llm.timeout = llm_data.get('timeout', self.config.llm.timeout)
            
            # Update UI config
            if 'ui' in config_data:
                ui_data = config_data['ui']
                self.config.ui.server_port = ui_data.get('server_port', self.config.ui.server_port)
                self.config.ui.server_address = ui_data.get('server_address', self.config.ui.server_address)
                self.config.ui.theme = ui_data.get('theme', self.config.ui.theme)
                self.config.ui.page_title = ui_data.get('page_title', self.config.ui.page_title)
                self.config.ui.page_icon = ui_data.get('page_icon', self.config.ui.page_icon)
            
            # Update logging config
            if 'logging' in config_data:
                logging_data = config_data['logging']
                self.config.logging.level = logging_data.get('level', self.config.logging.level)
                self.config.logging.file_path = logging_data.get('file_path', self.config.logging.file_path)
                self.config.logging.max_file_size = logging_data.get('max_file_size', self.config.logging.max_file_size)
                self.config.logging.backup_count = logging_data.get('backup_count', self.config.logging.backup_count)
                self.config.logging.format = logging_data.get('format', self.config.logging.format)
                self.config.logging.date_format = logging_data.get('date_format', self.config.logging.date_format)
            
            # Update security config
            if 'security' in config_data:
                security_data = config_data['security']
                self.config.security.secret_key = security_data.get('secret_key', self.config.security.secret_key)
                self.config.security.session_timeout = security_data.get('session_timeout', self.config.security.session_timeout)
                self.config.security.max_sessions = security_data.get('max_sessions', self.config.security.max_sessions)
                self.config.security.enable_encryption = security_data.get('enable_encryption', self.config.security.enable_encryption)
                
        except Exception as e:
            print(f"Warning: Error updating config from dictionary: {e}")
    
    def _load_from_environment(self):
        """Load configuration from environment variables"""
        # Main config
        self.config.debug = os.getenv('DEBUG', str(self.config.debug)).lower() == 'true'
        self.config.environment = os.getenv('ENVIRONMENT', self.config.environment)
        
        # Interview config
        self.config.interview.max_questions = int(os.getenv('MAX_QUESTIONS', self.config.interview.max_questions))
        self.config.interview.min_questions = int(os.getenv('MIN_QUESTIONS', self.config.interview.min_questions))
        self.config.interview.off_topic_threshold = float(os.getenv('OFF_TOPIC_THRESHOLD', self.config.interview.off_topic_threshold))
        self.config.interview.max_off_topic_responses = int(os.getenv('MAX_OFF_TOPIC_RESPONSES', self.config.interview.max_off_topic_responses))
        self.config.interview.default_interview_type = os.getenv('DEFAULT_INTERVIEW_TYPE', self.config.interview.default_interview_type)
        self.config.interview.default_difficulty = os.getenv('DEFAULT_DIFFICULTY', self.config.interview.default_difficulty)
        
        # LLM config
        self.config.llm.api_key = os.getenv('GEMINI_API_KEY', self.config.llm.api_key)
        self.config.llm.model_name = os.getenv('LLM_MODEL_NAME', self.config.llm.model_name)
        self.config.llm.temperature = float(os.getenv('LLM_TEMPERATURE', self.config.llm.temperature))
        self.config.llm.max_tokens = int(os.getenv('LLM_MAX_TOKENS', self.config.llm.max_tokens))
        self.config.llm.timeout = int(os.getenv('LLM_TIMEOUT', self.config.llm.timeout))
        
        # UI config
        self.config.ui.server_port = int(os.getenv('STREAMLIT_SERVER_PORT', self.config.ui.server_port))
        self.config.ui.server_address = os.getenv('STREAMLIT_SERVER_ADDRESS', self.config.ui.server_address)
        self.config.ui.theme = os.getenv('UI_THEME', self.config.ui.theme)
        
        # Logging config
        self.config.logging.level = os.getenv('LOG_LEVEL', self.config.logging.level)
        self.config.logging.file_path = os.getenv('LOG_FILE_PATH', self.config.logging.file_path)
        self.config.logging.max_file_size = os.getenv('MAX_LOG_SIZE', self.config.logging.max_file_size)
        self.config.logging.backup_count = int(os.getenv('LOG_BACKUP_COUNT', self.config.logging.backup_count))
        
        # Security config
        self.config.security.secret_key = os.getenv('SECRET_KEY', self.config.security.secret_key)
        self.config.security.session_timeout = int(os.getenv('SESSION_TIMEOUT', self.config.security.session_timeout))
        self.config.security.max_sessions = int(os.getenv('MAX_SESSIONS', self.config.security.max_sessions))
        self.config.security.enable_encryption = os.getenv('ENABLE_ENCRYPTION', str(self.config.security.enable_encryption)).lower() == 'true'
    
    def _setup_logging(self):
        """Setup logging configuration"""
        # Create logs directory if it doesn't exist
        log_path = Path(self.config.logging.file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, self.config.logging.level.upper()),
            format=self.config.logging.format,
            datefmt=self.config.logging.date_format,
            handlers=[
                logging.FileHandler(log_path),
                logging.StreamHandler()
            ]
        )
        
        # Set up log rotation
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=self._parse_size(self.config.logging.max_file_size),
            backupCount=self.config.logging.backup_count
        )
        file_handler.setFormatter(logging.Formatter(self.config.logging.format, self.config.logging.date_format))
        
        # Add file handler to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string to bytes"""
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            config_dict = {
                'debug': self.config.debug,
                'environment': self.config.environment,
                'version': self.config.version,
                'interview': asdict(self.config.interview),
                'llm': asdict(self.config.llm),
                'ui': asdict(self.config.ui),
                'logging': asdict(self.config.logging),
                'security': asdict(self.config.security),
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            logging.info(f"Configuration saved to {self.config_file}")
            
        except Exception as e:
            logging.error(f"Error saving configuration: {e}")
    
    def get_config(self) -> AppConfig:
        """Get current configuration"""
        return self.config
    
    def update_config(self, **kwargs):
        """Update configuration values"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            elif hasattr(self.config.interview, key):
                setattr(self.config.interview, key, value)
            elif hasattr(self.config.llm, key):
                setattr(self.config.llm, key, value)
            elif hasattr(self.config.ui, key):
                setattr(self.config.ui, key, value)
            elif hasattr(self.config.logging, key):
                setattr(self.config.logging, key, value)
            elif hasattr(self.config.security, key):
                setattr(self.config.security, key, value)
    
    def validate_config(self) -> bool:
        """Validate configuration"""
        errors = []
        
        # Check required fields
        if not self.config.llm.api_key:
            errors.append("LLM API key is required")
        
        if self.config.interview.max_questions < self.config.interview.min_questions:
            errors.append("Max questions must be greater than or equal to min questions")
        
        if self.config.interview.off_topic_threshold < 0 or self.config.interview.off_topic_threshold > 1:
            errors.append("Off-topic threshold must be between 0 and 1")
        
        if self.config.ui.server_port < 1 or self.config.ui.server_port > 65535:
            errors.append("Server port must be between 1 and 65535")
        
        if errors:
            for error in errors:
                logging.error(f"Configuration error: {error}")
            return False
        
        return True

# Global configuration instance
config_manager = ConfigManager()
config = config_manager.get_config()

