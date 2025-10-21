from fastapi import FastAPI, Request
from datetime import datetime
import uuid

app = FastAPI(title="Interview Service")

# In-memory storage for sessions
sessions_db = {}

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

@app.post("/api/session/create")
async def create_session(request: Request):
    """Create a new interview session"""
    body = await request.json()
    user_id = body.get("user_id")
    candidate_id = body.get("candidate_id")
    
    # Generate session ID
    session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Create session data
    session_data = {
        "session_id": session_id,
        "user_id": user_id,
        "candidate_id": candidate_id,
        "status": "created",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    # Store session
    sessions_db[session_id] = session_data
    
    return create_response(session_data)

@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """Get session details"""
    if session_id not in sessions_db:
        return create_response({"error": "Session not found"}, success=False)
    
    return create_response(sessions_db[session_id])

@app.patch("/api/session/{session_id}/status")
async def update_session_status(session_id: str, request: Request):
    """Update session status"""
    body = await request.json()
    status = body.get("status")
    
    if session_id not in sessions_db:
        return create_response({"error": "Session not found"}, success=False)
    
    sessions_db[session_id]["status"] = status
    sessions_db[session_id]["updated_at"] = datetime.utcnow().isoformat()
    
    return create_response(sessions_db[session_id])

@app.post("/api/session/{session_id}/transcript")
async def save_session_transcript(session_id: str, request: Request):
    """Save session transcript"""
    body = await request.json()
    
    if session_id not in sessions_db:
        return create_response({"error": "Session not found"}, success=False)
    
    sessions_db[session_id]["transcript"] = body
    sessions_db[session_id]["updated_at"] = datetime.utcnow().isoformat()
    
    return create_response(sessions_db[session_id])
