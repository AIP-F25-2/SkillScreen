"""
Token validation and management for email-based interview access
"""

import logging
from datetime import datetime
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

# In-memory token store (in production, use Redis or database)
# Format: { token: { candidate_id, candidate_name, candidate_email, session_id, expires_at, used_at } }
token_store = {}

token_bp = Blueprint('token', __name__)

@token_bp.route('/api/token/validate', methods=['POST'])
def validate_token():
    """
    Validate an interview access token
    
    Request:
        {
            "token": "string"
        }
    
    Response:
        {
            "valid": true/false,
            "data": {
                "token": "string",
                "candidateId": "string",
                "candidateName": "string",
                "candidateEmail": "string",
                "sessionId": "string",
                "expiresAt": "ISO date string",
                "usedAt": "ISO date string" (optional)
            },
            "error": "string" (if invalid)
        }
    """
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({
                "valid": False,
                "error": "Token is required"
            }), 400
        
        # Check if token exists
        if token not in token_store:
            logger.warning(f"Token not found: {token[:10]}...")
            return jsonify({
                "valid": False,
                "error": "Invalid or expired token"
            }), 404
        
        token_data = token_store[token]
        
        # Check if token is expired
        expires_at = datetime.fromisoformat(token_data['expires_at'])
        if datetime.utcnow() > expires_at:
            logger.warning(f"Token expired: {token[:10]}...")
            return jsonify({
                "valid": False,
                "error": "This interview link has expired"
            }), 410
        
        # Check if token was already used
        if token_data.get('used_at'):
            logger.warning(f"Token already used: {token[:10]}...")
            return jsonify({
                "valid": False,
                "error": "This interview link has already been used"
            }), 410
        
        # Mark token as used
        token_data['used_at'] = datetime.utcnow().isoformat()
        
        logger.info(f"Token validated successfully: {token[:10]}... for {token_data['candidate_email']}")
        
        return jsonify({
            "valid": True,
            "data": {
                "token": token,
                "candidateId": token_data['candidate_id'],
                "candidateName": token_data['candidate_name'],
                "candidateEmail": token_data['candidate_email'],
                "sessionId": token_data['session_id'],
                "expiresAt": token_data['expires_at'],
                "usedAt": token_data.get('used_at')
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        return jsonify({
            "valid": False,
            "error": "An error occurred while validating the token"
        }), 500


@token_bp.route('/api/token/store', methods=['POST'])
def store_token():
    """
    Store a new interview token (called internally when sending email)
    
    Request:
        {
            "token": "string",
            "candidate_id": "string",
            "candidate_name": "string",
            "candidate_email": "string",
            "session_id": "string",
            "expires_at": "ISO date string"
        }
    
    Response:
        {
            "success": true,
            "message": "Token stored successfully"
        }
    """
    try:
        data = request.get_json()
        
        required_fields = ['token', 'candidate_id', 'candidate_name', 'candidate_email', 'session_id', 'expires_at']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        token = data['token']
        
        # Store token data
        token_store[token] = {
            'candidate_id': data['candidate_id'],
            'candidate_name': data['candidate_name'],
            'candidate_email': data['candidate_email'],
            'session_id': data['session_id'],
            'expires_at': data['expires_at'],
            'used_at': None
        }
        
        logger.info(f"Token stored: {token[:10]}... for {data['candidate_email']}")
        
        return jsonify({
            "success": True,
            "message": "Token stored successfully"
        }), 201
        
    except Exception as e:
        logger.error(f"Token storage error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "An error occurred while storing the token"
        }), 500

