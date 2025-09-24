"""
Routing Controller - Request routing and forwarding
"""
from flask import request, jsonify
import requests
import logging

logger = logging.getLogger(__name__)

class RoutingController:
    """Controller for request routing and forwarding"""
    
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
    
    @classmethod
    def forward_request(cls, service_name, path, method='GET', data=None):
        """Forward request to appropriate service"""
        try:
            service_url = cls.SERVICES.get(service_name)
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
    
    @classmethod
    def route_request(cls, service_name, path):
        """Route requests to appropriate services"""
        data = request.get_json() if request.is_json else None
        return cls.forward_request(service_name, f'/{path}', request.method, data)
    
    @classmethod
    def route_service_request(cls, service_name):
        """Route requests to service root"""
        data = request.get_json() if request.is_json else None
        return cls.forward_request(service_name, '/', request.method, data)
    
    @classmethod
    def route_test(cls):
        """Test routing to all services"""
        results = {}
        for service_name, service_url in cls.SERVICES.items():
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
