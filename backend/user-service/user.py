from fastapi import FastAPI
from datetime import datetime
import uuid
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

PORT = int(os.getenv("PORT", 8080))

app = FastAPI(title="User Service")

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

users = [
    {"id": 1, "name": "Ashish"},
    {"id": 2, "name": "Lama"},
]

@app.get("/")
def health_check():
    """Health check endpoint"""
    return create_response({
        "message": "User Service is running",
        "status": "deployed",
        "service": "user-service"
    })

@app.get("/health")
def health():
    """Detailed health check"""
    return create_response({
        "service": "user-service",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.get("/users")
def get_users():
    return create_response({"users": users})

@app.get("/users/{user_id}")
def get_user(user_id: int):
    user = next((u for u in users if u["id"] == user_id), None)
    if user:
        return create_response({"user": user})
    else:
        return create_response({"error": "User not found"}, success=False)