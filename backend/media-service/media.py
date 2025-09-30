from fastapi import FastAPI
from datetime import datetime
import uuid

app = FastAPI(title="Media Service")

def create_response(data, success=True):
    """Create standardized API response"""
    return {
        "success": success,
        "data": data,
        "meta": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": f"req_{uuid.uuid4().hex[:8]}",
            "version": "v1"
        }
    }

@app.get("/")
def health_check():
    """Health check endpoint"""
    return create_response({
        "message": "Media Service is running",
        "status": "deployed",
        "service": "media-service"
    })

@app.get("/health")
def health():
    """Detailed health check"""
    return create_response({
        "service": "media-service",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    })
