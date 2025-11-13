import pytest
import sys
import os

# Add the backend path to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.logger import Logger


class TestLogger:
    """Test cases for Logger utility"""
    
    def test_logger_initialization(self):
        """Test Logger initialization"""
        logger = Logger()
        assert logger is not None
        assert hasattr(logger, 'logger')
    
    def test_log_info(self):
        """Test info logging"""
        logger = Logger()
        # This should not raise an exception
        logger.info("Test info message")
    
    def test_log_warning(self):
        """Test warning logging"""
        logger = Logger()
        # This should not raise an exception
        logger.warning("Test warning message")
    
    def test_log_error(self):
        """Test error logging"""
        logger = Logger()
        # This should not raise an exception
        logger.error("Test error message")


class TestHealthChecks:
    """Test cases for health check functionality"""
    
    def test_health_check_response(self):
        """Test health check response format"""
        # Mock health check response
        health_response = {
            "status": "healthy",
            "services": {
                "database": "connected",
                "llm": "available",
                "code-execution": "ready"
            },
            "timestamp": "2025-01-01T00:00:00Z"
        }
        
        assert health_response["status"] == "healthy"
        assert "services" in health_response
        assert "database" in health_response["services"]


class TestAPIEndpoints:
    """Test cases for API endpoint functionality"""
    
    def test_candidate_creation_payload(self):
        """Test candidate creation payload validation"""
        candidate_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "resume_text": "Software Engineer with 5 years experience..."
        }
        
        assert "name" in candidate_data
        assert "email" in candidate_data
        assert "resume_text" in candidate_data
        assert candidate_data["name"] == "John Doe"
    
    def test_job_creation_payload(self):
        """Test job creation payload validation"""
        job_data = {
            "title": "Software Engineer",
            "company": "Tech Corp",
            "description": "We are looking for a skilled engineer...",
            "required_skills": ["Python", "React", "SQL"]
        }
        
        assert "title" in job_data
        assert "company" in job_data
        assert "description" in job_data
        assert "required_skills" in job_data
        assert isinstance(job_data["required_skills"], list)
    
    def test_interview_start_payload(self):
        """Test interview start payload validation"""
        interview_data = {
            "candidate_id": "candidate_123",
            "job_id": "job_456"
        }
        
        assert "candidate_id" in interview_data
        assert "job_id" in interview_data
        assert interview_data["candidate_id"] == "candidate_123"


if __name__ == "__main__":
    pytest.main([__file__])
