from fastapi import FastAPI
from datetime import datetime
import uuid

app = FastAPI(title="Text AI Service")

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
        "message": "Text AI Service is running",
        "status": "deployed",
        "service": "text-ai-service"
    })

@app.get("/health")
def health():
    """Detailed health check"""
    return create_response({
        "service": "text-ai-service",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    })
