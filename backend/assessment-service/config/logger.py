import structlog
import logging
import sys
from config.settings import settings


def configure_logging():
    """
    Configure structured logging with structlog
    """
    # Set log level from settings
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if settings.log_format == "json" 
            else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


# Initialize logging
configure_logging()

# Create logger instance
logger = structlog.get_logger()


# Utility functions for common logging patterns
def log_assessment_started(interview_id: str):
    """Log when assessment generation starts"""
    logger.info(
        "assessment_generation_started",
        interview_id=interview_id
    )


def log_assessment_completed(interview_id: str, assessment_id: str, overall_score: float, recommendation: str):
    """Log when assessment is completed"""
    logger.info(
        "assessment_generation_completed",
        interview_id=interview_id,
        assessment_id=assessment_id,
        overall_score=overall_score,
        recommendation=recommendation
    )


def log_assessment_failed(interview_id: str, error: str):
    """Log when assessment generation fails"""
    logger.error(
        "assessment_generation_failed",
        interview_id=interview_id,
        error=error
    )


def log_scheduler_run(interviews_found: int, processed: int, skipped: int, errors: int):
    """Log scheduler run statistics"""
    logger.info(
        "scheduler_check_completed",
        interviews_found=interviews_found,
        processed=processed,
        skipped=skipped,
        errors=errors
    )


def log_llm_call(operation: str, model: str, success: bool, tokens_used: int = None):
    """Log LLM API calls"""
    logger.info(
        "llm_api_call",
        operation=operation,
        model=model,
        success=success,
        tokens_used=tokens_used
    )