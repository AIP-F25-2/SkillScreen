"""
API Gateway - Entry point for all requests
"""
from flask import Flask, request, jsonify
import requests
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Service URLs
SERVICES = {
    'user': 'http://user-service:5001',
    'auth': 'http://auth-service:5002',
    'interview': 'http://interview-service:5003',
    'media': 'http://media-service:5004',
    'video-ai': 'http://video-ai-service:5005',
    'audio-ai': 'http://audio-ai-service:5006',
    'text-ai': 'http://text-ai-service:5007',
    'assessment': 'http://assessment-service:5008',
    'coding': 'http://coding-service:5009',
    'logger': 'http://logger-service:5010',
    'notification': 'http://notification-service:5011'
}

def forward_request(service_name, path, method='GET', data=None):
    """Forward request to appropriate service"""
    try:
        service_url = SERVICES.get(service_name)
        if not service_url:
            return jsonify({'error': f'Service {service_name} not found'}), 404
        
        url = f"{service_url}{path}"
        headers = {'Content-Type': 'application/json'}
        
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=10)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=10)
        elif method == 'PUT':
            response = requests.put(url, json=data, headers=headers, timeout=10)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            return jsonify({'error': f'Method {method} not supported'}), 405
        
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to {service_name} failed: {str(e)}")
        return jsonify({'error': f'Service {service_name} unavailable'}), 503

@app.route('/api', methods=['GET'])
def api_endpoint():
    """Standardized API endpoint for API Gateway"""
    import uuid
    from datetime import datetime
    
    try:
        # API Gateway doesn't have its own data, so return routing info
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

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'api-gateway',
        'port': 5000
    })

@app.route('/info', methods=['GET'])
def service_info():
    """Service information"""
    return jsonify({
        'service': 'API Gateway',
        'version': '1.0.0',
        'description': 'Entry point for all API requests',
        'available_services': list(SERVICES.keys())
    })

@app.route('/route-test', methods=['GET'])
def route_test():
    """Test routing to all services"""
    results = {}
    for service_name, service_url in SERVICES.items():
        try:
            response = requests.get(f"{service_url}/health", timeout=5)
            results[service_name] = {
                'status': 'connected',
                'response_time': response.elapsed.total_seconds(),
                'status_code': response.status_code
            }
        except Exception as e:
            results[service_name] = {
                'status': 'disconnected',
                'error': str(e)
            }
    
    return jsonify({
        'gateway_status': 'healthy',
        'services': results
    })

# Route all other requests to appropriate services
@app.route('/<service_name>/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def route_request(service_name, path):
    """Route requests to appropriate services"""
    data = request.get_json() if request.is_json else None
    return forward_request(service_name, f'/{path}', request.method, data)

@app.route('/<service_name>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def route_service_request(service_name):
    """Route requests to service root"""
    data = request.get_json() if request.is_json else None
    return forward_request(service_name, '/', request.method, data)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
