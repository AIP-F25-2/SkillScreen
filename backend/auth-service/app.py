"""
Auth Service - Authentication and JWT management
"""
from flask import Flask, request, jsonify
import logging
import sys
import os
import hashlib

# Add shared directory to path
sys.path.append('/app/shared')

from database import db, init_database
from jwt_utils import generate_token, validate_token, get_user_from_token

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def hash_password(password):
    """Simple password hashing (use bcrypt in production)"""
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    db_healthy = db.health_check()
    return jsonify({
        'status': 'healthy' if db_healthy else 'unhealthy',
        'service': 'auth-service',
        'port': 5002,
        'database': 'connected' if db_healthy else 'disconnected'
    })

@app.route('/info', methods=['GET'])
def service_info():
    """Service information"""
    return jsonify({
        'service': 'Auth Service',
        'version': '1.0.0',
        'description': 'Authentication and JWT token management'
    })

@app.route('/api', methods=['GET'])
def api_endpoint():
    """Standardized API endpoint with consistent response structure"""
    import uuid
    from datetime import datetime
    
    try:
        # Get authentication sessions/tokens data
        sessions = db.execute_query("SELECT id, username, created_at FROM users")
        sessions_data = [dict(session) for session in sessions]
        
        # Calculate pagination
        current_page = 1
        per_page = 20
        total_count = len(sessions_data)
        total_pages = (total_count + per_page - 1) // per_page
        
        return jsonify({
            "success": True,
            "data": sessions_data,
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

@app.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        if not data or not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Username, email, and password are required'}), 400
        
        # Check if user already exists
        existing = db.execute_query("SELECT id FROM users WHERE username = %s OR email = %s", 
                                  (data['username'], data['email']))
        if existing:
            return jsonify({'error': 'User already exists'}), 409
        
        # Hash password and create user
        password_hash = hash_password(data['password'])
        db.execute_query(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
            (data['username'], data['email'], password_hash)
        )
        
        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/login', methods=['POST'])
def login():
    """Login user and return JWT token"""
    try:
        data = request.get_json()
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password are required'}), 400
        
        # Find user
        users = db.execute_query("SELECT id, username, password_hash FROM users WHERE username = %s", 
                               (data['username'],))
        if not users:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        user = users[0]
        password_hash = hash_password(data['password'])
        
        if user['password_hash'] != password_hash:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Generate JWT token
        token = generate_token(user['id'], user['username'])
        if not token:
            return jsonify({'error': 'Token generation failed'}), 500
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username']
            }
        })
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/validate-token', methods=['POST'])
def validate_token_endpoint():
    """Validate JWT token"""
    try:
        data = request.get_json()
        if not data or not data.get('token'):
            return jsonify({'error': 'Token is required'}), 400
        
        payload = validate_token(data['token'])
        if payload:
            return jsonify({
                'valid': True,
                'user': {
                    'user_id': payload.get('user_id'),
                    'username': payload.get('username')
                }
            })
        else:
            return jsonify({'valid': False, 'error': 'Invalid token'}), 401
    except Exception as e:
        logger.error(f"Token validation failed: {str(e)}")
        return jsonify({'error': 'Token validation failed'}), 500

@app.route('/protected', methods=['GET'])
def protected_endpoint():
    """Protected endpoint that requires valid JWT token"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization header required'}), 401
        
        token = auth_header.split(' ')[1]
        user = get_user_from_token(token)
        
        if user:
            return jsonify({
                'message': 'Access granted',
                'user': user
            })
        else:
            return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        logger.error(f"Protected endpoint access failed: {str(e)}")
        return jsonify({'error': 'Access denied'}), 401

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    port = int(os.getenv('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=True)
