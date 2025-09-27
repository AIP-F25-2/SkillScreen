from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from jose import jwt
from datetime import datetime, timedelta
import uuid

SECRET_KEY = "supersecret"
ALGORITHM = "HS256"

app = FastAPI(title="Auth Service")

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

class LoginRequest(BaseModel):
    username: str
    password: str

# User mock data
users_db = {
    "admin": {"password": "password", "role": "admin"},
    "ashish": {"password": "1234", "role": "user"}
}

@app.get("/")
def health_check():
    """Health check endpoint"""
    return create_response({
        "message": "Auth Service is running",
        "status": "deployed",
        "service": "auth-service"
    })

@app.get("/health")
def health():
    """Detailed health check"""
    return create_response({
        "service": "auth-service",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.post("/auth/login")
def login(req: LoginRequest):
    """User login endpoint"""
    user = users_db.get(req.username)
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    expire = datetime.utcnow() + timedelta(hours=1)
    token = jwt.encode(
        {"sub": req.username, "role": user["role"], "exp": expire},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return create_response({
        "access_token": token, 
        "role": user["role"],
        "expires_in": 3600
    })
