"""
Interview Service - Interview management
"""
from flask import Flask, request, jsonify
import logging
import sys
import os

# Add shared directory to path
sys.path.append('/app/shared')

from database import db, init_database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    db_healthy = db.health_check()
    return jsonify({
        'status': 'healthy' if db_healthy else 'unhealthy',
        'service': 'interview-service',
        'port': 5003,
        'database': 'connected' if db_healthy else 'disconnected'
    })

@app.route('/info', methods=['GET'])
def service_info():
    """Service information"""
    return jsonify({
        'service': 'Interview Service',
        'version': '1.0.0',
        'description': 'Interview management and scheduling'
    })

@app.route('/api', methods=['GET'])
def api_endpoint():
    """Standardized API endpoint with consistent response structure"""
    import uuid
    from datetime import datetime
    
    try:
        # Mock interview data
        interviews = [
            {
                'id': 1,
                'title': 'Software Engineer Interview',
                'candidate': 'John Doe',
                'status': 'scheduled',
                'date': '2024-01-15T10:00:00Z'
            },
            {
                'id': 2,
                'title': 'Data Scientist Interview',
                'candidate': 'Jane Smith',
                'status': 'completed',
                'date': '2024-01-14T14:00:00Z'
            }
        ]
        
        # Calculate pagination
        current_page = 1
        per_page = 20
        total_count = len(interviews)
        total_pages = (total_count + per_page - 1) // per_page
        
        return jsonify({
            "success": True,
            "data": interviews,
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

@app.route('/interviews', methods=['GET'])
def get_interviews():
    """Get all interviews (mock data)"""
    try:
        # Mock interview data
        interviews = [
            {
                'id': 1,
                'title': 'Software Engineer Interview',
                'candidate': 'John Doe',
                'status': 'scheduled',
                'date': '2024-01-15T10:00:00Z'
            },
            {
                'id': 2,
                'title': 'Data Scientist Interview',
                'candidate': 'Jane Smith',
                'status': 'completed',
                'date': '2024-01-14T14:00:00Z'
            }
        ]
        
        return jsonify({
            'message': 'Interviews retrieved successfully',
            'interviews': interviews,
            'count': len(interviews)
        })
        
    except Exception as e:
        logger.error(f"Failed to get interviews: {str(e)}")
        return jsonify({'error': 'Failed to retrieve interviews'}), 500

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    port = int(os.getenv('PORT', 5003))
    app.run(host='0.0.0.0', port=port, debug=True)
