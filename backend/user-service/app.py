"""
User Service - User management
"""
from flask import Flask, request, jsonify
import logging
import sys
import os

# Add shared directory to path
sys.path.append('/app/shared')

from database import db, init_database
from jwt_utils import get_user_from_token

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
        'service': 'user-service',
        'port': 5001,
        'database': 'connected' if db_healthy else 'disconnected'
    })

@app.route('/info', methods=['GET'])
def service_info():
    """Service information"""
    return jsonify({
        'service': 'User Service',
        'version': '1.0.0',
        'description': 'User management and CRUD operations'
    })

@app.route('/api', methods=['GET'])
def api_endpoint():
    """Standardized API endpoint with consistent response structure"""
    import uuid
    from datetime import datetime
    
    try:
        # Get users data
        users = db.execute_query("SELECT id, username, email, created_at FROM users")
        users_data = [dict(user) for user in users]
        
        # Calculate pagination
        current_page = 1
        per_page = 20
        total_count = len(users_data)
        total_pages = (total_count + per_page - 1) // per_page
        
        return jsonify({
            "success": True,
            "data": users_data,
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

@app.route('/users', methods=['GET'])
def get_users():
    """Get all users"""
    try:
        users = db.execute_query("SELECT id, username, email, created_at FROM users")
        return jsonify({
            'users': [dict(user) for user in users],
            'count': len(users)
        })
    except Exception as e:
        logger.error(f"Failed to get users: {str(e)}")
        return jsonify({'error': 'Failed to retrieve users'}), 500

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get user by ID"""
    try:
        users = db.execute_query("SELECT id, username, email, created_at FROM users WHERE id = %s", (user_id,))
        if users:
            return jsonify({'user': dict(users[0])})
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        logger.error(f"Failed to get user {user_id}: {str(e)}")
        return jsonify({'error': 'Failed to retrieve user'}), 500

@app.route('/users', methods=['POST'])
def create_user():
    """Create a new user"""
    try:
        data = request.get_json()
        if not data or not data.get('username') or not data.get('email'):
            return jsonify({'error': 'Username and email are required'}), 400
        
        # Check if user already exists
        existing = db.execute_query("SELECT id FROM users WHERE username = %s OR email = %s", 
                                  (data['username'], data['email']))
        if existing:
            return jsonify({'error': 'User already exists'}), 409
        
        # Create user (simplified - no password hashing for demo)
        db.execute_query(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
            (data['username'], data['email'], 'demo_password_hash')
        )
        
        return jsonify({'message': 'User created successfully'}), 201
    except Exception as e:
        logger.error(f"Failed to create user: {str(e)}")
        return jsonify({'error': 'Failed to create user'}), 500

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete user by ID"""
    try:
        result = db.execute_query("DELETE FROM users WHERE id = %s", (user_id,))
        if result > 0:
            return jsonify({'message': 'User deleted successfully'})
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        logger.error(f"Failed to delete user {user_id}: {str(e)}")
        return jsonify({'error': 'Failed to delete user'}), 500

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
