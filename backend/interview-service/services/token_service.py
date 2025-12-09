"""
Shared service for managing interview tokens
"""

import logging
from datetime import datetime
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class TokenService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TokenService, cls).__new__(cls)
            cls._instance.token_store = {}
        return cls._instance

    def store_token(self, token: str, data: Dict[str, Any]) -> bool:
        """
        Store a token with its associated data
        """
        try:
            self.token_store[token] = {
                'candidate_id': data['candidate_id'],
                'candidate_name': data['candidate_name'],
                'candidate_email': data['candidate_email'],
                'session_id': data['session_id'],
                'interview_id': data.get('interview_id'),
                'expires_at': data['expires_at'],
                'used_at': None
            }
            logger.info(f"Token stored in memory: {token[:10]}... for {data['candidate_email']}")
            return True
        except Exception as e:
            logger.error(f"Error storing token in memory: {str(e)}")
            return False

    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate a token and return its status and data
        """
        if not token:
            return {"valid": False, "error": "Token is required"}

        # 1. Check in-memory store first
        if token in self.token_store:
            token_data = self.token_store[token]
            
            # Check expiration
            try:
                expires_at = datetime.fromisoformat(token_data['expires_at'])
                if datetime.utcnow() > expires_at:
                    logger.warning(f"Token expired: {token[:10]}...")
                    return {"valid": False, "error": "This interview link has expired"}
            except ValueError:
                 logger.error(f"Invalid expiration date format for token: {token[:10]}...")
                 return {"valid": False, "error": "Invalid token data"}

            # Check usage
            if token_data.get('used_at'):
                logger.warning(f"Token already used: {token[:10]}...")
                return {"valid": False, "error": "This interview link has already been used"}

            return {
                "valid": True,
                "data": token_data
            }
            
        # 2. Fallback to Database Check
        try:
            from db import DBFactory
            from repository.interview_repository import InterviewRepository
            
            session = DBFactory.get_session()
            try:
                interview_repo = InterviewRepository(session)
                # We need to find an interview where settings->>'token' == token
                # Since we don't have a direct method for this in the repo, we might need to iterate or add one.
                # For now, let's assume we can fetch by candidate_id if we had it, but we don't.
                # So we have to search. This is expensive but necessary for fallback.
                # Ideally, InterviewRepository should have `get_interview_by_token`.
                
                # Let's try to find ANY interview with this token in settings
                # This is a raw query or we need to add a method to the repo.
                # For safety/speed in this hotfix, let's try to add a method to repo or use a raw query here if possible.
                # But we can't easily modify repo from here without circular imports potentially.
                
                # Let's use a raw SQL query for the fallback to avoid complex repo changes right now
                from sqlalchemy import text
                
                # Assuming 'interviews' table and 'settings' is JSONB
                query = text("SELECT id, candidate_id, settings, status FROM interviews WHERE settings->>'token' = :token")
                result = session.execute(query, {"token": token}).fetchone()
                
                if result:
                    interview_id = str(result[0])
                    candidate_id = str(result[1])
                    settings = result[2] or {}
                    status = result[3]
                    
                    logger.info(f"Found token in database fallback: {token[:10]}... -> Interview {interview_id}")
                    
                    # Reconstruct token_data
                    token_data = {
                        'candidate_id': candidate_id,
                        'candidate_name': settings.get('candidate_name', 'Candidate'), # Fallback
                        'candidate_email': settings.get('candidate_email', 'email@example.com'), # Fallback
                        'session_id': interview_id,
                        'interview_id': interview_id,
                        'expires_at': settings.get('expires_at'),
                        'used_at': settings.get('used_at') # Check if used in DB
                    }
                    
                    # Cache it back in memory
                    self.token_store[token] = token_data
                    
                    # Validate expiration
                    if token_data['expires_at']:
                        expires_at = datetime.fromisoformat(token_data['expires_at'])
                        if datetime.utcnow() > expires_at:
                            return {"valid": False, "error": "This interview link has expired"}
                            
                    # Validate usage (if status is not scheduled, it might be used)
                    if status != 'scheduled' and status != 'pending':
                         # If it's in_progress or completed, it's technically "used" but we might want to allow re-entry?
                         # Usually "used_at" logic prevents re-entry.
                         # If settings has used_at, check that.
                         if token_data.get('used_at'):
                             return {"valid": False, "error": "This interview link has already been used"}
                    
                    return {
                        "valid": True,
                        "data": token_data
                    }
                    
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Database fallback error for token {token[:10]}...: {str(e)}")
            
        logger.warning(f"Token not found in memory or database: {token[:10]}...")
        return {"valid": False, "error": "Invalid or expired token"}

    def mark_token_used(self, token: str) -> bool:
        """
        Mark a token as used
        """
        if token in self.token_store:
            self.token_store[token]['used_at'] = datetime.utcnow().isoformat()
            return True
        return False

# Create singleton instance
token_service = TokenService()
