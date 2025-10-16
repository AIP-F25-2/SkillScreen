from fastapi import FastAPI
from datetime import datetime
import uuid
import logging

# Import resume controller
from controllers.resume_controller import router as resume_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Interview Service")

# Include resume router
app.include_router(resume_router)

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
        "message": "Interview Service is running",
        "status": "deployed",
        "service": "interview-service",
        "endpoints": {
            "resume_upload": "/resumes/upload",
            "health": "/health"
        }
    })

@app.get("/health")
def health():
    """Detailed health check"""
    return create_response({
        "service": "interview-service",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "features": ["resume_upload", "file_processing", "email_extraction"]
    })
