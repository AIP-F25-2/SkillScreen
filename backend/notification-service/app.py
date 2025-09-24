"""
Notification Service
"""
from flask import Flask, request, jsonify
import logging
import sys
import os

# Add shared directory to path
sys.path.append('/app/shared')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'notification-service',
        'port': 5011
    })

@app.route('/info', methods=['GET'])
def service_info():
    """Service information"""
    return jsonify({
        'service': 'Notification Service',
        'version': '1.0.0',
        'description': 'Notification Service'
    })

@app.route('/api', methods=['GET'])
def api_endpoint():
    """Standardized API endpoint with consistent response structure"""
    import uuid
    from datetime import datetime
    
    try:
        # Mock data for notification-service
        mock_data = [
            {
                'id': 1,
                'name': 'Sample Notification Service Item',
                'status': 'active',
                'created_at': datetime.utcnow().isoformat() + "Z"
            },
            {
                'id': 2,
                'name': 'Another Notification Service Item',
                'status': 'pending',
                'created_at': datetime.utcnow().isoformat() + "Z"
            }
        ]
        
        # Calculate pagination
        current_page = 1
        per_page = 20
        total_count = len(mock_data)
        total_pages = (total_count + per_page - 1) // per_page
        
        return jsonify({
            "success": True,
            "data": mock_data,
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

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5011))
    app.run(host='0.0.0.0', port=port, debug=True)
