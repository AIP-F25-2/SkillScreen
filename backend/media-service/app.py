"""
Media Service - File upload and management
"""
from flask import Flask, request, jsonify
import logging
import os
import uuid
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure upload settings
UPLOAD_FOLDER = '/app/storage/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mp3', 'wav'}

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'media-service',
        'port': 5004,
        'storage': 'available'
    })

@app.route('/info', methods=['GET'])
def service_info():
    """Service information"""
    return jsonify({
        'service': 'Media Service',
        'version': '1.0.0',
        'description': 'File upload, download and media management'
    })

@app.route('/api', methods=['GET'])
def api_endpoint():
    """Standardized API endpoint with consistent response structure"""
    import uuid
    from datetime import datetime
    
    try:
        # Get media files data
        files = []
        for filename in os.listdir(UPLOAD_FOLDER):
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(filepath):
                files.append({
                    'id': len(files) + 1,
                    'filename': filename,
                    'size': os.path.getsize(filepath),
                    'created_at': datetime.fromtimestamp(os.path.getctime(filepath)).isoformat() + "Z"
                })
        
        # Calculate pagination
        current_page = 1
        per_page = 20
        total_count = len(files)
        total_pages = (total_count + per_page - 1) // per_page
        
        return jsonify({
            "success": True,
            "data": files,
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

@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload a file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Generate unique filename
            unique_filename = f"{uuid.uuid4()}_{filename}"
            filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
            file.save(filepath)
            
            return jsonify({
                'message': 'File uploaded successfully',
                'filename': unique_filename,
                'original_name': filename,
                'size': os.path.getsize(filepath)
            }), 201
        else:
            return jsonify({'error': 'File type not allowed'}), 400
    except Exception as e:
        logger.error(f"File upload failed: {str(e)}")
        return jsonify({'error': 'File upload failed'}), 500

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download a file"""
    try:
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(filepath):
            return jsonify({
                'message': 'File found',
                'filename': filename,
                'size': os.path.getsize(filepath),
                'path': filepath
            })
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        logger.error(f"File download failed: {str(e)}")
        return jsonify({'error': 'File download failed'}), 500

@app.route('/files', methods=['GET'])
def list_files():
    """List all uploaded files"""
    try:
        files = []
        for filename in os.listdir(UPLOAD_FOLDER):
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(filepath):
                files.append({
                    'filename': filename,
                    'size': os.path.getsize(filepath)
                })
        
        return jsonify({
            'files': files,
            'count': len(files)
        })
    except Exception as e:
        logger.error(f"Failed to list files: {str(e)}")
        return jsonify({'error': 'Failed to list files'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5004))
    app.run(host='0.0.0.0', port=port, debug=True)
