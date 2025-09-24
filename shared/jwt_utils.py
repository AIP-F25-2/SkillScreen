"""
JWT utility functions for authentication
"""
import jwt
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# JWT secret key (in production, use environment variable)
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

def generate_token(user_id, username):
    """Generate JWT token for user"""
    try:
        payload = {
            'user_id': user_id,
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            'iat': datetime.utcnow()
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        logger.info(f"Token generated for user: {username}")
        return token
    except Exception as e:
        logger.error(f"Token generation failed: {str(e)}")
        return None

def validate_token(token):
    """Validate JWT token and return payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        logger.info(f"Token validated for user: {payload.get('username')}")
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Token validation failed: {str(e)}")
        return None

def get_user_from_token(token):
    """Extract user information from token"""
    payload = validate_token(token)
    if payload:
        return {
            'user_id': payload.get('user_id'),
            'username': payload.get('username')
        }
    return None
