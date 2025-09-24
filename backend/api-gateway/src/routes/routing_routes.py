"""
Routing Routes - Request routing and forwarding endpoints
"""
from flask import Blueprint
from ..controllers.routing_controller import RoutingController

# Create blueprint
routing_bp = Blueprint('routing', __name__)

@routing_bp.route('/route-test', methods=['GET'])
def route_test():
    """Test routing to all services"""
    return RoutingController.route_test()

@routing_bp.route('/<service_name>/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def route_request(service_name, path):
    """Route requests to appropriate services"""
    return RoutingController.route_request(service_name, path)

@routing_bp.route('/<service_name>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def route_service_request(service_name):
    """Route requests to service root"""
    return RoutingController.route_service_request(service_name)
