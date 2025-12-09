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

        if token not in self.token_store:
            logger.warning(f"Token not found in memory: {token[:10]}...")
            return {"valid": False, "error": "Invalid or expired token"}

        token_data = self.token_store[token]

        # Check expiration
        try:
            expires_at = datetime.fromisoformat(token_data['expires_at'])
            if datetime.utcnow() > expires_at:
                logger.warning(f"Token expired: {token[:10]}...")
                return {"valid": False, "error": "This interview link has expired"}
        except ValueError:
             # Handle case where expires_at might not be in isoformat or valid
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
