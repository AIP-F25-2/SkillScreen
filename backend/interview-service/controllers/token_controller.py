"""
Token validation and management for email-based interview access
"""

import logging
from flask import Blueprint, request, jsonify
from services.token_service import token_service

logger = logging.getLogger(__name__)

token_bp = Blueprint('token', __name__)

@token_bp.route('/api/token/validate', methods=['POST'])
def validate_token():
    """
    Validate an interview access token
    """
    try:
        data = request.get_json()
        token = data.get('token')
        
        validation_result = token_service.validate_token(token)
        
        if not validation_result['valid']:
            return jsonify(validation_result), 400 if "required" in validation_result['error'] else (404 if "found" in validation_result['error'] else 410)
        
        token_data = validation_result['data']
        
        # Mark token as used
        token_service.mark_token_used(token)
        
        logger.info(f"Token validated successfully: {token[:10]}... for {token_data['candidate_email']}")
        
        return jsonify({
            "valid": True,
            "data": {
                "token": token,
                "candidateId": token_data['candidate_id'],
                "candidateName": token_data['candidate_name'],
                "candidateEmail": token_data['candidate_email'],
                "sessionId": token_data['session_id'],
                "interviewId": token_data.get('interview_id'),
                "expiresAt": token_data['expires_at'],
                "usedAt": token_data.get('used_at')
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "valid": False,
            "error": f"An error occurred: {str(e)}"
        }), 500


@token_bp.route('/api/token/store', methods=['POST'])
def store_token():
    """
    Store a new interview token (internal use, kept for backward compatibility if needed)
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
        
        if token_service.store_token(token, data):
            return jsonify({
                "success": True,
                "message": "Token stored successfully"
            }), 201
        else:
             return jsonify({
                "success": False,
                "error": "Failed to store token"
            }), 500
        
    except Exception as e:
        logger.error(f"Token storage error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "An error occurred while storing the token"
        }), 500

