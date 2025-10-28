"""
Simplified FastAPI application for SkillScreen Text Service
Designed to work as a microservice without requiring API keys upfront
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
import json
import uuid
from datetime import datetime
import os
import logging

# Initialize FastAPI app
app = FastAPI(
    title="SkillScreen Text Service",
    description="AI-powered text processing service for interview platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "text-service",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

# Resume parsing endpoint
@app.post("/resumes/parse")
async def parse_resume(file: UploadFile = File(...)):
    """Parse resume file and extract candidate information"""
    try:
        logger.info(f"Processing resume: {file.filename}")
        
        # For now, return mock data since we don't have API keys
        # In production, this would use actual AI services
        mock_candidate_data = {
            "candidate_id": str(uuid.uuid4()),
            "candidate_name": "John Doe",
            "candidate_email": "john.doe@example.com",
            "candidate_phone": "+1-555-0123",
            "skills": ["Python", "JavaScript", "React", "Node.js", "SQL"],
            "experience_years": 3,
            "education": [
                {
                    "degree": "Bachelor of Science",
                    "field": "Computer Science",
                    "institution": "University of Technology",
                    "year": 2020
                }
            ],
            "work_experience": [
                {
                    "title": "Software Developer",
                    "company": "Tech Corp",
                    "duration": "2 years",
                    "description": "Developed web applications using React and Node.js"
                }
            ],
            "parsed_at": datetime.utcnow().isoformat()
        }
        
        return {
            "success": True,
            "data": mock_candidate_data,
            "message": "Resume parsed successfully (mock data)"
        }
        
    except Exception as e:
        logger.error(f"Error parsing resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error parsing resume: {str(e)}")

# Create candidate endpoint
@app.post("/candidates")
async def create_candidate(candidate_data: Dict[str, Any]):
    """Create a new candidate record"""
    try:
        logger.info(f"Creating candidate: {candidate_data.get('candidate_name', 'Unknown')}")
        
        # Generate candidate ID
        candidate_id = str(uuid.uuid4())
        
        # Return success response
        return {
            "success": True,
            "data": {
                "candidate_id": candidate_id,
                "status": "created",
                "created_at": datetime.utcnow().isoformat()
            },
            "message": "Candidate created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating candidate: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating candidate: {str(e)}")

# Create job endpoint
@app.post("/jobs")
async def create_job(job_data: Dict[str, Any]):
    """Create a new job posting"""
    try:
        logger.info(f"Creating job: {job_data.get('title', 'Unknown')}")
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Return success response
        return {
            "success": True,
            "data": {
                "job_id": job_id,
                "status": "created",
                "created_at": datetime.utcnow().isoformat()
            },
            "message": "Job created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating job: {str(e)}")

# Start interview endpoint
@app.post("/interviews/start")
async def start_interview(interview_data: Dict[str, Any]):
    """Start a new interview session"""
    try:
        logger.info(f"Starting interview for job: {interview_data.get('job_id', 'Unknown')}")
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Return success response
        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "status": "started",
                "started_at": datetime.utcnow().isoformat()
            },
            "message": "Interview started successfully"
        }
        
    except Exception as e:
        logger.error(f"Error starting interview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting interview: {str(e)}")

# Get interview questions endpoint
@app.get("/interviews/{session_id}/questions")
async def get_interview_questions(session_id: str):
    """Get interview questions for a session"""
    try:
        logger.info(f"Getting questions for session: {session_id}")
        
        # Mock questions for now
        mock_questions = [
            {
                "question_id": str(uuid.uuid4()),
                "question": "Tell me about yourself and your experience with Python.",
                "type": "general",
                "difficulty": "medium",
                "expected_answer_length": "2-3 minutes"
            },
            {
                "question_id": str(uuid.uuid4()),
                "question": "Explain the difference between a list and a tuple in Python.",
                "type": "technical",
                "difficulty": "easy",
                "expected_answer_length": "1-2 minutes"
            },
            {
                "question_id": str(uuid.uuid4()),
                "question": "How would you handle a situation where your code is running slower than expected?",
                "type": "behavioral",
                "difficulty": "medium",
                "expected_answer_length": "2-3 minutes"
            }
        ]
        
        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "questions": mock_questions,
                "total_questions": len(mock_questions),
                "generated_at": datetime.utcnow().isoformat()
            },
            "message": "Questions generated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error getting questions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting questions: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
