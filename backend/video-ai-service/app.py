"""
Simple Video AI Service
"""
from flask import Flask, jsonify
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

@app.route('/', methods=['GET'])
def root():
    """Root endpoint - check if service is deployed and working"""
    return jsonify({
        'message': 'Video AI Service is running',
        'status': 'deployed',
        'service': 'video-ai-service',
        'port': os.getenv('PORT')
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT'))
    print(f"Starting Video AI Service on port {port}")
    app.run(host='0.0.0.0', port=port)
