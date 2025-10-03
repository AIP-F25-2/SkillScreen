"""
Simple test FastAPI application to verify the core functionality works
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
from datetime import datetime

# Create FastAPI app
app = FastAPI(
    title="SkillScreen Test API",
    description="Test version of SkillScreen FastAPI backend",
    version="1.0.0"
)

# Simple models for testing
class TestResponse(BaseModel):
    message: str
    timestamp: str
    status: str

class InterviewTestRequest(BaseModel):
    candidate_name: str
    job_title: str
    resume_text: Optional[str] = None
    job_description: Optional[str] = None

# In-memory storage for testing
test_sessions = {}
test_counter = 0

@app.get("/")
async def root():
    """Root endpoint"""
    return TestResponse(
        message="SkillScreen Test API is running!",
        timestamp=datetime.now().isoformat(),
        status="success"
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return TestResponse(
        message="API is healthy",
        timestamp=datetime.now().isoformat(),
        status="healthy"
    )

@app.post("/test/interview/start")
async def start_test_interview(request: InterviewTestRequest):
    """Test interview start endpoint"""
    global test_counter
    test_counter += 1
    session_id = f"test_session_{test_counter}"
    
    # Store test session
    test_sessions[session_id] = {
        "session_id": session_id,
        "candidate_name": request.candidate_name,
        "job_title": request.job_title,
        "resume_text": request.resume_text,
        "job_description": request.job_description,
        "start_time": datetime.now().isoformat(),
        "status": "active",
        "questions_asked": 0,
        "responses_received": 0
    }
    
    return {
        "session_id": session_id,
        "message": f"Test interview started for {request.candidate_name}",
        "status": "started",
        "first_question": "Tell me about yourself and your experience with this role."
    }

@app.get("/test/interview/{session_id}")
async def get_test_interview(session_id: str):
    """Get test interview status"""
    if session_id not in test_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return test_sessions[session_id]

class ResponseRequest(BaseModel):
    response: str

@app.post("/test/interview/{session_id}/respond")
async def submit_test_response(session_id: str, request: ResponseRequest):
    """Submit test response"""
    if session_id not in test_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = test_sessions[session_id]
    session["responses_received"] += 1
    session["last_response"] = request.response
    session["last_response_time"] = datetime.now().isoformat()
    
    # Simple test logic
    if session["responses_received"] >= 3:
        session["status"] = "completed"
        return {
            "status": "completed",
            "message": "Test interview completed",
            "summary": {
                "total_questions": 3,
                "total_responses": session["responses_received"],
                "candidate": session["candidate_name"],
                "job": session["job_title"],
                "recommendation": "Test completed successfully"
            }
        }
    else:
        # Generate next question
        questions = [
            "What are your key strengths for this role?",
            "Describe a challenging project you worked on.",
            "Why are you interested in this position?"
        ]
        
        next_question = questions[session["responses_received"]] if session["responses_received"] < len(questions) else "Any final questions for us?"
        session["questions_asked"] += 1
        
        return {
            "status": "continue",
            "next_question": next_question,
            "question_number": session["questions_asked"],
            "response_received": request.response
        }

@app.get("/test/sessions")
async def list_test_sessions():
    """List all test sessions"""
    return {
        "sessions": list(test_sessions.values()),
        "total_sessions": len(test_sessions)
    }

@app.delete("/test/sessions")
async def clear_test_sessions():
    """Clear all test sessions"""
    global test_sessions
    test_sessions = {}
    return {"message": "All test sessions cleared"}

if __name__ == "__main__":
    import uvicorn
    print("Starting SkillScreen Test API...")
    print("API will be available at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
