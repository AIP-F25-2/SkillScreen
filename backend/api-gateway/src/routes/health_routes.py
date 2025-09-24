"""
Health Routes - Health check and service info endpoints
"""
from flask import Blueprint
from ..controllers.health_controller import HealthController

# Create blueprint
health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return HealthController.health_check()

@health_bp.route('/info', methods=['GET'])
def service_info():
    """Service information endpoint"""
    return HealthController.service_info()
