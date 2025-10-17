"""
FastAPI production application for SkillScreen
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import uuid
from datetime import datetime
import os

# Import our modules
from database.database import get_db
from database.models import (
    Candidate, Job, Interview, InterviewQuestion, 
    InterviewResponse, InterviewSummary, AuditLog
)
from services.interview_service import InterviewService
from services.nlp_service import NLPService
from services.anti_cheating_service import AntiCheatingService
from schemas.interview_schemas import (
    CandidateCreate, JobCreate, InterviewStart, 
    InterviewResponse as InterviewResponseSchema,
    InterviewSummary as InterviewSummarySchema
)
from utils.logger import log_info, log_error

# Initialize FastAPI app
app = FastAPI(
    title="SkillScreen API",
    description="AI-powered interview platform for automated candidate screening",
    version="2.0.0",
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

# Initialize services
interview_service = InterviewService()
nlp_service = NLPService()
anti_cheating_service = AntiCheatingService()

# Mount static files (for frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "SkillScreen API",
        "version": "2.0.0",
        "status": "active",
        "docs": "/api/docs"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": "connected",
            "nlp": "active",
            "anti_cheating": "active"
        }
    }

# Candidate endpoints
@app.post("/api/candidates/", response_model=dict)
async def create_candidate(
    candidate: CandidateCreate,
    db: Session = Depends(get_db)
):
    """Create a new candidate"""
    try:
        db_candidate = Candidate(
            name=candidate.name,
            email=candidate.email,
            phone=candidate.phone,
            resume_text=candidate.resume_text,
            skills=candidate.skills,
            experience_years=candidate.experience_years,
            education=candidate.education
        )
        
        db.add(db_candidate)
        db.commit()
        db.refresh(db_candidate)
        
        log_info(f"Created candidate: {db_candidate.id}")
        
        return {
            "id": db_candidate.id,
            "name": db_candidate.name,
            "email": db_candidate.email,
            "created_at": db_candidate.created_at.isoformat()
        }
        
    except Exception as e:
        log_error(f"Error creating candidate: {e}")
        raise HTTPException(status_code=500, detail="Failed to create candidate")

@app.get("/api/candidates/{candidate_id}")
async def get_candidate(
    candidate_id: str,
    db: Session = Depends(get_db)
):
    """Get candidate by ID"""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    return {
        "id": candidate.id,
        "name": candidate.name,
        "email": candidate.email,
        "phone": candidate.phone,
        "skills": candidate.skills,
        "experience_years": candidate.experience_years,
        "education": candidate.education,
        "created_at": candidate.created_at.isoformat()
    }

# Job endpoints
@app.post("/api/jobs/", response_model=dict)
async def create_job(
    job: JobCreate,
    db: Session = Depends(get_db)
):
    """Create a new job posting"""
    try:
        db_job = Job(
            title=job.title,
            company=job.company,
            description=job.description,
            requirements=job.requirements,
            skills_required=job.skills_required,
            experience_level=job.experience_level,
            job_type=job.job_type,
            location=job.location,
            salary_range=job.salary_range
        )
        
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        
        log_info(f"Created job: {db_job.id}")
        
        return {
            "id": db_job.id,
            "title": db_job.title,
            "company": db_job.company,
            "created_at": db_job.created_at.isoformat()
        }
        
    except Exception as e:
        log_error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail="Failed to create job")

@app.get("/api/jobs/{job_id}")
async def get_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Get job by ID"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "id": job.id,
        "title": job.title,
        "company": job.company,
        "description": job.description,
        "requirements": job.requirements,
        "skills_required": job.skills_required,
        "experience_level": job.experience_level,
        "job_type": job.job_type,
        "location": job.location,
        "salary_range": job.salary_range,
        "created_at": job.created_at.isoformat()
    }

# Interview endpoints
@app.post("/api/interviews/start")
async def start_interview(
    interview_data: InterviewStart,
    db: Session = Depends(get_db)
):
    """Start a new interview session"""
    try:
        # Get candidate and job
        candidate = db.query(Candidate).filter(Candidate.id == interview_data.candidate_id).first()
        job = db.query(Job).filter(Job.id == interview_data.job_id).first()
        
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Create interview session
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        db_interview = Interview(
            candidate_id=candidate.id,
            job_id=job.id,
            session_id=session_id,
            interview_type=interview_data.interview_type,
            difficulty=interview_data.difficulty,
            max_questions=interview_data.max_questions,
            target_duration_minutes=interview_data.target_duration_minutes,
            status='in_progress',
            start_time=datetime.utcnow()
        )
        
        db.add(db_interview)
        db.commit()
        db.refresh(db_interview)
        
        # Generate initial question
        initial_question = await interview_service.generate_initial_question(
            candidate, job, interview_data.interview_type, db
        )
        
        # Log audit trail
        audit_log = AuditLog(
            action="interview_started",
            entity_type="interview",
            entity_id=db_interview.id,
            metadata={
                "candidate_id": candidate.id,
                "job_id": job.id,
                "session_id": session_id
            }
        )
        db.add(audit_log)
        db.commit()
        
        log_info(f"Started interview: {session_id}")
        
        return {
            "session_id": session_id,
            "interview_id": db_interview.id,
            "candidate_name": candidate.name,
            "job_title": job.title,
            "initial_question": initial_question,
            "status": "in_progress"
        }
        
    except Exception as e:
        log_error(f"Error starting interview: {e}")
        raise HTTPException(status_code=500, detail="Failed to start interview")

@app.post("/api/interviews/{session_id}/respond")
async def submit_response(
    session_id: str,
    response_data: InterviewResponseSchema,
    db: Session = Depends(get_db)
):
    """Submit candidate response and get next question"""
    try:
        # Get interview
        interview = db.query(Interview).filter(Interview.session_id == session_id).first()
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        if interview.status != 'in_progress':
            raise HTTPException(status_code=400, detail="Interview is not active")
        
        # Get current question
        current_question = db.query(InterviewQuestion).filter(
            InterviewQuestion.interview_id == interview.id,
            InterviewQuestion.question_index == interview.current_question_index
        ).first()
        
        if not current_question:
            raise HTTPException(status_code=404, detail="Current question not found")
        
        # Anti-cheating analysis
        cheating_analysis = await anti_cheating_service.analyze_response(
            response_data.response_text, interview.id, db
        )
        
        # NLP evaluation
        nlp_evaluation = await nlp_service.evaluate_response(
            current_question.question_text,
            response_data.response_text,
            interview.candidate_id,
            interview.job_id,
            db
        )
        
        # Create response record
        db_response = InterviewResponse(
            interview_id=interview.id,
            question_id=current_question.id,
            response_text=response_data.response_text,
            response_length=len(response_data.response_text),
            overall_score=nlp_evaluation.get('overall_score', 0.0),
            relevance_score=nlp_evaluation.get('relevance_score', 0.0),
            technical_accuracy_score=nlp_evaluation.get('technical_accuracy_score', 0.0),
            communication_score=nlp_evaluation.get('communication_score', 0.0),
            depth_score=nlp_evaluation.get('depth_score', 0.0),
            job_fit_score=nlp_evaluation.get('job_fit_score', 0.0),
            strengths=nlp_evaluation.get('strengths', []),
            weaknesses=nlp_evaluation.get('weaknesses', []),
            feedback=nlp_evaluation.get('feedback', ''),
            improvement_tips=nlp_evaluation.get('improvement_tips', []),
            is_duplicate=cheating_analysis.get('is_duplicate', False),
            is_off_topic=cheating_analysis.get('is_off_topic', False),
            response_time_seconds=response_data.response_time_seconds
        )
        
        db.add(db_response)
        
        # Update interview progress
        interview.total_responses_received += 1
        interview.current_question_index += 1
        
        # Check if interview should continue
        if (cheating_analysis.get('should_terminate', False) or 
            interview.current_question_index >= interview.max_questions):
            interview.status = 'completed'
            interview.end_time = datetime.utcnow()
            interview.termination_reason = 'completed' if interview.current_question_index >= interview.max_questions else 'anti_cheating'
            
            # Generate final summary
            summary = await interview_service.generate_interview_summary(interview.id, db)
            
            db.commit()
            
            return {
                "status": "completed",
                "summary": summary,
                "termination_reason": interview.termination_reason
            }
        
        # Generate next question
        next_question = await interview_service.generate_next_question(
            interview.id, db
        )
        
        interview.total_questions_asked += 1
        db.commit()
        
        return {
            "status": "continue",
            "next_question": next_question,
            "current_score": nlp_evaluation.get('overall_score', 0.0),
            "anti_cheating_flags": cheating_analysis
        }
        
    except Exception as e:
        log_error(f"Error processing response: {e}")
        raise HTTPException(status_code=500, detail="Failed to process response")

@app.get("/api/interviews/{session_id}/status")
async def get_interview_status(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get current interview status"""
    interview = db.query(Interview).filter(Interview.session_id == session_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    return {
        "session_id": session_id,
        "status": interview.status,
        "current_question_index": interview.current_question_index,
        "total_questions_asked": interview.total_questions_asked,
        "total_responses_received": interview.total_responses_received,
        "overall_score": interview.overall_score,
        "start_time": interview.start_time.isoformat() if interview.start_time else None,
        "end_time": interview.end_time.isoformat() if interview.end_time else None
    }

@app.get("/api/interviews/{session_id}/summary")
async def get_interview_summary(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get interview summary"""
    interview = db.query(Interview).filter(Interview.session_id == session_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    summary = db.query(InterviewSummary).filter(InterviewSummary.interview_id == interview.id).first()
    if not summary:
        # Generate summary if not exists
        summary_data = await interview_service.generate_interview_summary(interview.id, db)
        return summary_data
    
    return {
        "executive_summary": summary.executive_summary,
        "overall_score": summary.overall_score,
        "recommendation": summary.recommendation,
        "recommendation_reason": summary.recommendation_reason,
        "technical_assessment": {
            "score": summary.technical_assessment_score,
            "summary": summary.technical_assessment_summary
        },
        "communication_assessment": {
            "score": summary.communication_assessment_score,
            "summary": summary.communication_assessment_summary
        },
        "cultural_fit": {
            "score": summary.cultural_fit_score,
            "summary": summary.cultural_fit_summary
        },
        "strengths": summary.strengths,
        "areas_for_improvement": summary.areas_for_improvement,
        "key_highlights": summary.key_highlights,
        "red_flags": summary.red_flags,
        "improvement_tips": summary.improvement_tips,
        "next_steps": summary.next_steps,
        "interviewer_notes": summary.interviewer_notes,
        "generated_at": summary.generated_at.isoformat()
    }

# File upload endpoints
@app.post("/api/upload/resume")
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and parse resume file"""
    try:
        # Save uploaded file
        file_path = f"uploads/resumes/{file.filename}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Parse resume using existing parser
        from app_dynamic import SimpleResumeParser
        parser = SimpleResumeParser()
        parsed_data = parser.parse_file(file)
        
        return {
            "filename": file.filename,
            "file_path": file_path,
            "parsed_data": parsed_data
        }
        
    except Exception as e:
        log_error(f"Error uploading resume: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload resume")

# Export endpoints
@app.get("/api/interviews/{session_id}/export/pdf")
async def export_interview_pdf(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Export interview as PDF"""
    try:
        interview = db.query(Interview).filter(Interview.session_id == session_id).first()
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        # Generate PDF report
        pdf_path = await interview_service.generate_pdf_report(interview.id, db)
        
        return FileResponse(
            pdf_path,
            media_type='application/pdf',
            filename=f"interview_report_{session_id}.pdf"
        )
        
    except Exception as e:
        log_error(f"Error exporting PDF: {e}")
        raise HTTPException(status_code=500, detail="Failed to export PDF")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "fastapi_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
