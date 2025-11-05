"""
Email controller for sending interview invitations
"""

import logging
from flask import Blueprint, request, jsonify
from services.email_service import email_service
import requests
import os

logger = logging.getLogger(__name__)

email_bp = Blueprint('email', __name__)

API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5001')

@email_bp.route('/api/email/send-invitation', methods=['POST'])
def send_invitation():
    """
    Send an interview invitation email to a candidate
    
    Request:
        {
            "candidate_email": "string",
            "candidate_name": "string",
            "candidate_id": "string",
            "session_id": "string",
            "recruiter_name": "string" (optional),
            "company_name": "string" (optional),
            "expires_in_hours": int (optional, default 48)
        }
    
    Response:
        {
            "success": true,
            "data": {
                "email_id": "string",
                "token": "string",
                "expires_at": "ISO date string",
                "interview_link": "string"
            }
        }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['candidate_email', 'candidate_name', 'candidate_id', 'session_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        # Send invitation email
        result = email_service.send_interview_invitation(
            candidate_email=data['candidate_email'],
            candidate_name=data['candidate_name'],
            candidate_id=data['candidate_id'],
            session_id=data['session_id'],
            recruiter_name=data.get('recruiter_name'),
            company_name=data.get('company_name'),
            expires_in_hours=data.get('expires_in_hours', 48)
        )
        
        # Store token in token service
        try:
            token_response = requests.post(
                f'{API_BASE_URL}/interview/api/token/store',
                json={
                    'token': result['token'],
                    'candidate_id': result['candidate_id'],
                    'candidate_name': result['candidate_name'],
                    'candidate_email': result['candidate_email'],
                    'session_id': result['session_id'],
                    'expires_at': result['expires_at']
                }
            )
            
            if not token_response.ok:
                logger.error(f"Failed to store token: {token_response.text}")
                
        except Exception as e:
            logger.error(f"Error storing token: {str(e)}")
        
        return jsonify({
            "success": True,
            "data": {
                "email_id": result['email_id'],
                "token": result['token'],
                "expires_at": result['expires_at'],
                "interview_link": f"{email_service.base_url}/interview-link?token={result['token']}"
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to send invitation: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@email_bp.route('/api/email/send-completion-notification', methods=['POST'])
def send_completion_notification():
    """
    Send interview completion notification to recruiter
    
    Request:
        {
            "recruiter_email": "string",
            "recruiter_name": "string",
            "candidate_name": "string",
            "interview_id": "string",
            "session_id": "string"
        }
    
    Response:
        {
            "success": true,
            "data": {
                "email_id": "string"
            }
        }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['recruiter_email', 'recruiter_name', 'candidate_name', 'interview_id', 'session_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        # Send completion notification
        result = email_service.send_interview_completion_notification(
            recruiter_email=data['recruiter_email'],
            recruiter_name=data['recruiter_name'],
            candidate_name=data['candidate_name'],
            interview_id=data['interview_id'],
            session_id=data['session_id']
        )
        
        return jsonify({
            "success": True,
            "data": {
                "email_id": result['email_id']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to send completion notification: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

