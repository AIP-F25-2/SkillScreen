"""
Simple FastAPI application for SkillScreen Text Service
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import uuid
from datetime import datetime
import os
import aiofiles
from utils.resume_parser import ResumeParser

# Initialize FastAPI app
app = FastAPI(
    title="SkillScreen Text Service",
    description="Text processing service for resume parsing and interview management",
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

# Initialize resume parser
resume_parser = ResumeParser()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "SkillScreen Text Service",
        "version": "1.0.0",
        "status": "active",
        "docs": "/api/docs"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "text-service"
    }

@app.get("/health")
async def health_check_simple():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "text-service"
    }

@app.post("/resumes/parse")
async def parse_resume(file: UploadFile = File(...)):
    """Parse resume PDF and extract candidate information"""
    try:
        # Read file content
        content = await file.read()
        
        # Parse resume
        parsed_data = resume_parser.parse_resume_from_pdf(content)
        
        return {
            "status": "success",
            "data": parsed_data,
            "message": "Resume parsed successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse resume: {str(e)}")

@app.post("/api/resumes/parse")
async def parse_resume_api(file: UploadFile = File(...)):
    """Parse resume PDF and extract candidate information (API version)"""
    try:
        # Read file content
        content = await file.read()
        
        # Parse resume
        parsed_data = resume_parser.parse_resume_from_pdf(content)
        
        return {
            "status": "success",
            "data": parsed_data,
            "message": "Resume parsed successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse resume: {str(e)}")

@app.post("/candidates")
async def create_candidate(candidate_data: dict):
    """Create a new candidate record"""
    try:
        # For now, just return success - in production this would save to database
        return {
            "status": "success",
            "data": {
                "candidate_id": f"cand_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "name": candidate_data.get("name", "Unknown Candidate"),
                "email": candidate_data.get("email", "candidate@example.com"),
                "status": "created"
            },
            "message": "Candidate created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create candidate: {str(e)}")

@app.post("/jobs")
async def create_job(job_data: dict):
    """Create a new job posting"""
    try:
        # For now, just return success - in production this would save to database
        return {
            "status": "success",
            "data": {
                "job_id": f"job_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "title": job_data.get("title", "Software Engineer"),
                "company": job_data.get("company", "TechCorp"),
                "status": "created"
            },
            "message": "Job created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")

@app.post("/interviews/start")
async def start_interview(interview_data: dict):
    """Start a new interview session"""
    try:
        # For now, just return success - in production this would save to database
        return {
            "status": "success",
            "data": {
                "session_id": f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "interview_id": f"interview_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "status": "started"
            },
            "message": "Interview started successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)