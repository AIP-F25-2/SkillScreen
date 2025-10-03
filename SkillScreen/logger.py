"""
Logging utilities for SkillScreen
Provides structured logging for different components
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from functools import wraps

class SkillScreenLogger:
    """Custom logger for SkillScreen with structured logging"""
    
    def __init__(self, name: str = "SkillScreen"):
        """Initialize logger"""
        self.logger = logging.getLogger(name)
        self.log_file = Path("logs/skillscreen.log")
        self.audit_file = Path("logs/audit.log")
        self.error_file = Path("logs/errors.log")
        
        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def info(self, message: str, **kwargs):
        """Log info message with additional context"""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with additional context"""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with additional context"""
        self._log(logging.ERROR, message, **kwargs)
        self._log_to_file(self.error_file, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with additional context"""
        self._log(logging.DEBUG, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with additional context"""
        self._log(logging.CRITICAL, message, **kwargs)
        self._log_to_file(self.error_file, message, **kwargs)
    
    def _log(self, level: int, message: str, **kwargs):
        """Internal logging method"""
        if kwargs:
            context = json.dumps(kwargs, default=str)
            full_message = f"{message} | Context: {context}"
        else:
            full_message = message
        
        self.logger.log(level, full_message)
    
    def _log_to_file(self, file_path: Path, message: str, **kwargs):
        """Log to specific file"""
        try:
            with open(file_path, 'a') as f:
                timestamp = datetime.now().isoformat()
                context = json.dumps(kwargs, default=str) if kwargs else "{}"
                f.write(f"{timestamp} - {message} | Context: {context}\n")
        except Exception as e:
            print(f"Error writing to log file: {e}")
    
    def log_interview_start(self, session_id: str, candidate_name: str, job_title: str, company: str):
        """Log interview start"""
        self.info(
            "Interview started",
            session_id=session_id,
            candidate_name=candidate_name,
            job_title=job_title,
            company=company,
            event_type="interview_start"
        )
        self._log_to_audit("interview_start", {
            "session_id": session_id,
            "candidate_name": candidate_name,
            "job_title": job_title,
            "company": company
        })
    
    def log_interview_end(self, session_id: str, total_questions: int, total_responses: int, overall_score: float):
        """Log interview end"""
        self.info(
            "Interview completed",
            session_id=session_id,
            total_questions=total_questions,
            total_responses=total_responses,
            overall_score=overall_score,
            event_type="interview_end"
        )
        self._log_to_audit("interview_end", {
            "session_id": session_id,
            "total_questions": total_questions,
            "total_responses": total_responses,
            "overall_score": overall_score
        })
    
    def log_question_generated(self, session_id: str, question: str, question_type: str, difficulty: str):
        """Log question generation"""
        self.debug(
            "Question generated",
            session_id=session_id,
            question=question[:100] + "..." if len(question) > 100 else question,
            question_type=question_type,
            difficulty=difficulty,
            event_type="question_generated"
        )
    
    def log_response_received(self, session_id: str, response: str, relevance_score: float, 
                             technical_accuracy: float, communication_quality: float):
        """Log response received and evaluated"""
        self.info(
            "Response received and evaluated",
            session_id=session_id,
            response_length=len(response),
            relevance_score=relevance_score,
            technical_accuracy=technical_accuracy,
            communication_quality=communication_quality,
            event_type="response_evaluated"
        )
    
    def log_off_topic_detected(self, session_id: str, response: str, off_topic_count: int):
        """Log off-topic response detection"""
        self.warning(
            "Off-topic response detected",
            session_id=session_id,
            response=response[:100] + "..." if len(response) > 100 else response,
            off_topic_count=off_topic_count,
            event_type="off_topic_detected"
        )
    
    def log_api_call(self, api_name: str, success: bool, response_time: float, **kwargs):
        """Log API calls"""
        level = logging.INFO if success else logging.ERROR
        self._log(
            level,
            f"API call to {api_name}",
            success=success,
            response_time=response_time,
            **kwargs
        )
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log error with context"""
        self.error(
            f"Error occurred: {str(error)}",
            error_type=type(error).__name__,
            context=context or {},
            event_type="error"
        )
    
    def log_performance(self, operation: str, duration: float, **kwargs):
        """Log performance metrics"""
        self.info(
            f"Performance: {operation}",
            duration=duration,
            operation=operation,
            **kwargs
        )
    
    def _log_to_audit(self, event_type: str, data: Dict[str, Any]):
        """Log to audit file"""
        try:
            with open(self.audit_file, 'a') as f:
                audit_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "event_type": event_type,
                    "data": data
                }
                f.write(json.dumps(audit_entry) + "\n")
        except Exception as e:
            print(f"Error writing to audit log: {e}")

def log_function_call(func):
    """Decorator to log function calls"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = SkillScreenLogger()
        logger.debug(f"Calling function: {func.__name__}", args=str(args)[:100], kwargs=str(kwargs)[:100])
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Function {func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Function {func.__name__} failed", error=str(e))
            raise
    return wrapper

def log_execution_time(func):
    """Decorator to log function execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = SkillScreenLogger()
        start_time = datetime.now()
        
        try:
            result = func(*args, **kwargs)
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.log_performance(f"Function {func.__name__}", execution_time)
            return result
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Function {func.__name__} failed after {execution_time}s", error=str(e))
            raise
    return wrapper

# Global logger instance
logger = SkillScreenLogger()

# Convenience functions
def log_info(message: str, **kwargs):
    """Log info message"""
    logger.info(message, **kwargs)

def log_warning(message: str, **kwargs):
    """Log warning message"""
    logger.warning(message, **kwargs)

def log_error(message: str, **kwargs):
    """Log error message"""
    logger.error(message, **kwargs)

def log_debug(message: str, **kwargs):
    """Log debug message"""
    logger.debug(message, **kwargs)

def log_critical(message: str, **kwargs):
    """Log critical message"""
    logger.critical(message, **kwargs)

