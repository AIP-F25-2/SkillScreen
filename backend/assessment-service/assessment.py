from fastapi import FastAPI
from datetime import datetime
import uuid

app = FastAPI(title="Assessment Service")

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

questions = ["What is Python?", "Explain microservices.", "What is JWT?"]

@app.get("/")
def health_check():
    """Health check endpoint"""
    return create_response({
        "message": "Assessment Service is running",
        "status": "deployed",
        "service": "assessment-service"
    })

@app.get("/health")
def health():
    """Detailed health check"""
    return create_response({
        "service": "assessment-service",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.get("/questions")
def get_questions():
    return create_response({"questions": questions})

@app.post("/submit")
def submit_assessment(answer: dict):
    return create_response({"status": "submitted", "answer": answer})
