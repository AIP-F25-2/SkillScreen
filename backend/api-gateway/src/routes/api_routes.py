"""
API Routes - Main API endpoints
"""
from flask import Blueprint
from ..controllers.api_controller import ApiController

# Create blueprint
api_bp = Blueprint('api', __name__)

@api_bp.route('/api', methods=['GET'])
def api_endpoint():
    """Standardized API endpoint for API Gateway"""
    return ApiController.api_endpoint()
