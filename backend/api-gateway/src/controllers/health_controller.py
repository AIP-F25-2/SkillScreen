"""
Health Controller - Health check endpoints
"""
from flask import jsonify
import logging

logger = logging.getLogger(__name__)

class HealthController:
    """Controller for health-related endpoints"""
    
    @staticmethod
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'service': 'api-gateway',
            'port': 5000
        })
    
    @staticmethod
    def service_info():
        """Service information endpoint"""
        return jsonify({
            'service': 'API Gateway',
            'version': '1.0.0',
            'description': 'Entry point for all API requests',
            'available_services': [
                'user', 'auth', 'interview', 'media', 
                'video-ai', 'audio-ai', 'text-ai', 
                'assessment', 'coding', 'logger', 'notification'
            ]
        })
