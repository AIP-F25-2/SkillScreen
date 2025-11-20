from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controllers.interview_controller import router as interview_router
from controllers.health_controller import router as health_router
from config import settings
from datetime import datetime
import uuid

app = FastAPI(
    title="SkillScreen Orchestration Service",
    version="1.0.0",
    description="Central orchestration service for managing interview workflows"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, tags=["Health"])
app.include_router(interview_router, prefix="/api/orchestration", tags=["Orchestration"])


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
def root():
    """Root endpoint"""
    return create_response({
        "service": "orchestration-service",
        "status": "running",
        "message": "SkillScreen Interview Orchestration Service"
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "orchestration:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )

