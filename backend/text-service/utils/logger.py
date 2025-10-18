"""
Enhanced logging utilities for SkillScreen production system
"""

import logging
import os
from datetime import datetime
from typing import Optional
import json
from pathlib import Path

class SkillScreenLogger:
    """Enhanced logger for SkillScreen with structured logging"""
    
    def __init__(self, name: str = "SkillScreen"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Setup formatters
        self.detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        self.json_formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
        )
        
        # Setup handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup logging handlers"""
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(self.detailed_formatter)
        self.logger.addHandler(console_handler)
        
        # Main log file handler
        main_handler = logging.FileHandler('logs/skillscreen.log')
        main_handler.setLevel(logging.INFO)
        main_handler.setFormatter(self.detailed_formatter)
        self.logger.addHandler(main_handler)
        
        # Error log file handler
        error_handler = logging.FileHandler('logs/errors.log')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(self.detailed_formatter)
        self.logger.addHandler(error_handler)
        
        # Audit log file handler (JSON format)
        audit_handler = logging.FileHandler('logs/audit.log')
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(self.json_formatter)
        self.logger.addHandler(audit_handler)
    
    def info(self, message: str, extra: Optional[dict] = None):
        """Log info message"""
        if extra:
            message = f"{message} | Extra: {json.dumps(extra)}"
        self.logger.info(message)
    
    def error(self, message: str, extra: Optional[dict] = None):
        """Log error message"""
        if extra:
            message = f"{message} | Extra: {json.dumps(extra)}"
        self.logger.error(message)
    
    def warning(self, message: str, extra: Optional[dict] = None):
        """Log warning message"""
        if extra:
            message = f"{message} | Extra: {json.dumps(extra)}"
        self.logger.warning(message)
    
    def debug(self, message: str, extra: Optional[dict] = None):
        """Log debug message"""
        if extra:
            message = f"{message} | Extra: {json.dumps(extra)}"
        self.logger.debug(message)
    
    def audit(self, action: str, entity_type: str, entity_id: str, 
              user_id: Optional[str] = None, metadata: Optional[dict] = None):
        """Log audit trail"""
        audit_data = {
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "user_id": user_id,
            "metadata": metadata,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        audit_message = json.dumps(audit_data)
        
        # Create audit logger
        audit_logger = logging.getLogger("SkillScreen.Audit")
        audit_logger.setLevel(logging.INFO)
        
        # Add audit handler if not exists
        if not audit_logger.handlers:
            audit_handler = logging.FileHandler('logs/audit.log')
            audit_handler.setFormatter(self.json_formatter)
            audit_logger.addHandler(audit_handler)
            audit_logger.propagate = False
        
        audit_logger.info(audit_message)

# Global logger instance
logger = SkillScreenLogger()

# Convenience functions
def log_info(message: str, extra: Optional[dict] = None):
    """Log info message"""
    logger.info(message, extra)

def log_error(message: str, extra: Optional[dict] = None):
    """Log error message"""
    logger.error(message, extra)

def log_warning(message: str, extra: Optional[dict] = None):
    """Log warning message"""
    logger.warning(message, extra)

def log_debug(message: str, extra: Optional[dict] = None):
    """Log debug message"""
    logger.debug(message, extra)

def log_audit(action: str, entity_type: str, entity_id: str, 
              user_id: Optional[str] = None, metadata: Optional[dict] = None):
    """Log audit trail"""
    logger.audit(action, entity_type, entity_id, user_id, metadata)
