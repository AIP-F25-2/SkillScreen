"""
Logger Service - Centralized logging
"""
from flask import Flask, request, jsonify
import logging
import os
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# In-memory log storage (use database in production)
logs_storage = []

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'logger-service',
        'port': 5010,
        'logs_count': len(logs_storage)
    })

@app.route('/info', methods=['GET'])
def service_info():
    """Service information"""
    return jsonify({
        'service': 'Logger Service',
        'version': '1.0.0',
        'description': 'Centralized logging and log management',
        'logs_count': len(logs_storage)
    })

@app.route('/log', methods=['POST'])
def create_log():
    """Create a new log entry"""
    try:
        data = request.get_json()
        if not data or not data.get('message'):
            return jsonify({'error': 'Log message is required'}), 400
        
        # Create log entry
        log_entry = {
            'id': len(logs_storage) + 1,
            'timestamp': datetime.utcnow().isoformat(),
            'level': data.get('level', 'INFO'),
            'service': data.get('service', 'unknown'),
            'message': data['message'],
            'metadata': data.get('metadata', {}),
            'user_id': data.get('user_id'),
            'request_id': data.get('request_id')
        }
        
        logs_storage.append(log_entry)
        return jsonify({'message': 'Log created successfully', 'log_id': log_entry['id']}), 201
        
    except Exception as e:
        logger.error(f"Failed to create log: {str(e)}")
        return jsonify({'error': 'Failed to create log'}), 500

@app.route('/api', methods=['GET'])
def api_endpoint():
    """Standardized API endpoint with consistent response structure"""
    import uuid
    from datetime import datetime
    
    try:
        # Get logs data
        logs = []
        logs_data = [dict(item) for item in logs]
        
        # Calculate pagination
        current_page = 1
        per_page = 20
        total_count = len(logs_data)
        total_pages = (total_count + per_page - 1) // per_page
        
        return jsonify({
            "success": True,
            "data": logs_data,
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
        
        logs_storage.append(log_entry)
        
        # Also log to console
        log_level = getattr(logging, log_entry['level'].upper(), logging.INFO)
        logger.log(log_level, f"[{log_entry['service']}] {log_entry['message']}")
        
        return jsonify({
            'message': 'Log created successfully',
            'log_id': log_entry['id']
        }), 201
    except Exception as e:
        logger.error(f"Failed to create log: {str(e)}")
        return jsonify({'error': 'Failed to create log'}), 500

@app.route('/logs', methods=['GET'])
def get_logs():
    """Get logs with optional filtering"""
    try:
        # Get query parameters
        service = request.args.get('service')
        level = request.args.get('level')
        limit = int(request.args.get('limit', 100))
        
        # Filter logs
        filtered_logs = logs_storage.copy()
        
        if service:
            filtered_logs = [log for log in filtered_logs if log['service'] == service]
        
        if level:
            filtered_logs = [log for log in filtered_logs if log['level'] == level.upper()]
        
        # Limit results
        filtered_logs = filtered_logs[-limit:] if limit > 0 else filtered_logs
        
        return jsonify({
            'logs': filtered_logs,
            'count': len(filtered_logs),
            'total_logs': len(logs_storage)
        })
    except Exception as e:
        logger.error(f"Failed to get logs: {str(e)}")
        return jsonify({'error': 'Failed to retrieve logs'}), 500

@app.route('/logs/<int:log_id>', methods=['GET'])
def get_log(log_id):
    """Get specific log by ID"""
    try:
        if log_id <= 0 or log_id > len(logs_storage):
            return jsonify({'error': 'Log not found'}), 404
        
        log_entry = logs_storage[log_id - 1]
        return jsonify({'log': log_entry})
    except Exception as e:
        logger.error(f"Failed to get log {log_id}: {str(e)}")
        return jsonify({'error': 'Failed to retrieve log'}), 500

@app.route('/logs/stats', methods=['GET'])
def get_log_stats():
    """Get logging statistics"""
    try:
        if not logs_storage:
            return jsonify({
                'total_logs': 0,
                'by_level': {},
                'by_service': {},
                'recent_activity': []
            })
        
        # Calculate statistics
        by_level = {}
        by_service = {}
        
        for log in logs_storage:
            # Count by level
            level = log['level']
            by_level[level] = by_level.get(level, 0) + 1
            
            # Count by service
            service = log['service']
            by_service[service] = by_service.get(service, 0) + 1
        
        # Get recent activity (last 10 logs)
        recent_activity = logs_storage[-10:] if len(logs_storage) >= 10 else logs_storage
        
        return jsonify({
            'total_logs': len(logs_storage),
            'by_level': by_level,
            'by_service': by_service,
            'recent_activity': recent_activity
        })
    except Exception as e:
        logger.error(f"Failed to get log stats: {str(e)}")
        return jsonify({'error': 'Failed to retrieve log statistics'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5010))
    app.run(host='0.0.0.0', port=port, debug=True)
