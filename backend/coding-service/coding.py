from fastapi import FastAPI
from datetime import datetime
import uuid

app = FastAPI(title="Coding Service")

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
        "message": "Coding Service is running",
        "status": "deployed",
        "service": "coding-service"
    })

@app.get("/health")
def health():
    """Detailed health check"""
    return create_response({
        "service": "coding-service",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.get("/problems")
def get_problems():
    return create_response({"problems": ["FizzBuzz", "Reverse String", "Palindrome Checker"]})

@app.post("/submit")
def submit_solution(solution: dict):
    return create_response({"status": "submitted", "solution": solution})
