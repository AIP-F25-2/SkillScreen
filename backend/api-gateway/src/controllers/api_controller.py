"""
API Controller - Main API endpoints
"""
from flask import jsonify
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class ApiController:
    """Controller for main API endpoints"""
    
    @staticmethod
    def api_endpoint():
        """Standardized API endpoint for API Gateway"""
        try:
            # API Gateway routing information
            routing_info = [
                {
                    'id': 1,
                    'service': 'user-service',
                    'port': 5001,
                    'status': 'available',
                    'endpoints': ['/api', '/health', '/info']
                },
                {
                    'id': 2,
                    'service': 'auth-service', 
                    'port': 5002,
                    'status': 'available',
                    'endpoints': ['/api', '/health', '/info']
                },
                {
                    'id': 3,
                    'service': 'interview-service',
                    'port': 5003,
                    'status': 'available',
                    'endpoints': ['/api', '/health', '/info']
                },
                {
                    'id': 4,
                    'service': 'media-service',
                    'port': 5004,
                    'status': 'available',
                    'endpoints': ['/api', '/health', '/info']
                }
            ]
            
            # Calculate pagination
            current_page = 1
            per_page = 20
            total_count = len(routing_info)
            total_pages = (total_count + per_page - 1) // per_page
            
            return jsonify({
                "success": True,
                "data": routing_info,
                "meta": {
                    "pagination": {
                        "current_page": current_page,
                        "per_page": per_page,
                        "total_pages": total_pages,
                        "total_count": total_count
                    },
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "request_id": f"req_{str(uuid.uuid4())[:8]}"
                }
            })
        except Exception as e:
            logger.error(f"Failed to get API data: {str(e)}")
            return jsonify({
                "success": False,
                "data": [],
                "meta": {
                    "pagination": {
                        "current_page": 1,
                        "per_page": 20,
                        "total_pages": 0,
                        "total_count": 0
                    },
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "request_id": f"req_{str(uuid.uuid4())[:8]}",
                    "error": str(e)
                }
            }), 500
