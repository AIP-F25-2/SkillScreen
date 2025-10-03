from fastapi import FastAPI
from datetime import datetime
import uuid

# Import controllers
from controllers import interviews_controller, questions_controller, sessions_controller, resumes_controller

app = FastAPI(title="Interview Service")

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
        "service": "interview-service"
    })

@app.get("/health")
def health():
    """Detailed health check"""
    return create_response({
        "service": "interview-service",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    })

# Mount Routers
app.include_router(interviews_controller.router, prefix="/interviews", tags=["Interviews"])
app.include_router(questions_controller.router, prefix="/interviews", tags=["Questions"])
app.include_router(sessions_controller.router, prefix="/interviews", tags=["Sessions"])
app.include_router(resumes_controller.router, prefix="/resumes", tags=["Resumes"])