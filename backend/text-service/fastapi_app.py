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
import asyncio
import aiofiles

# Import our modules
from database.database import get_db
from database.models import (
    Candidate, JobPosition, Interview, InterviewSession,
    Response, Assessment, AuditLog
)
from services.database_service import InterviewDataService
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

# Mount static files (for frontend) - optional
import os
if os.path.exists("static"):
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
        db_service = InterviewDataService(db)
        
        # Get or create default organization for testing
        org = db_service.get_or_create_default_organization()
        
        # Create candidate using database service
        db_candidate = db_service.create_candidate(
            organization_id=str(org.id),
            full_name=candidate.name,
            email=candidate.email,
            phone=getattr(candidate, 'phone', None),
            skills=candidate.skills or [],
            experience={"years": getattr(candidate, 'experience_years', 0)} if hasattr(candidate, 'experience_years') else None,
            education=candidate.education if hasattr(candidate, 'education') else None
        )
        
        log_info(f"Created candidate: {db_candidate.id}")
        
        return {
            "id": str(db_candidate.id),
            "name": db_candidate.full_name,
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
        "id": str(candidate.id),
        "name": candidate.full_name,
        "email": candidate.email,
        "phone": candidate.phone,
        "skills": candidate.skills,
        "experience": candidate.experience,
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
        db_service = InterviewDataService(db)
        
        # Get or create default organization
        org = db_service.get_or_create_default_organization()
        
        # Create job position using database service
        db_job = db_service.create_job_position(
            organization_id=str(org.id),
            title=job.title,
            description=job.description or f"Position at {job.company}",
            required_skills=job.skills_required or [],
            department=getattr(job, 'job_type', None)
        )
        
        log_info(f"Created job: {db_job.id}")
        
        return {
            "id": str(db_job.id),
            "title": db_job.title,
            "company": job.company,  # From request, not stored in JobPosition
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
    job = db.query(JobPosition).filter(JobPosition.id == job_id).first()
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
        job = db.query(JobPosition).filter(JobPosition.id == interview_data.job_id).first()
        
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Get or create default organization
        db_service = InterviewDataService(db)
        org = db_service.get_or_create_default_organization()
        
        # Create or get User record from Candidate
        # Interview.candidate_id references users.id, not candidates.id
        from database.models import User, UserRole
        candidate_email = getattr(candidate, 'email', f"candidate_{candidate.id}@test.com")
        user = db.query(User).filter(User.email == candidate_email).first()
        
        if not user:
            # Create User from Candidate
            full_name = getattr(candidate, 'full_name', 'Candidate')
            name_parts = full_name.split(' ', 1)
            first_name = name_parts[0] if name_parts else 'Candidate'
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            user = db_service.create_user(
                organization_id=str(org.id),
                email=candidate_email,
                first_name=first_name,
                last_name=last_name,
                role=UserRole.CANDIDATE
            )
            log_info(f"Created User record for candidate: {user.id}")
        
        # Get or create default template
        from database.models import InterviewTemplate
        template = db.query(InterviewTemplate).filter(
            InterviewTemplate.organization_id == org.id
        ).first()
        if not template:
            template = InterviewTemplate(
                organization_id=org.id,
                name="Default Template",
                type=interview_data.interview_type,
                questions=[],
                settings={}
            )
            db.add(template)
            db.commit()
            db.refresh(template)
        
        # Create interview session
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        from database.models import InterviewStatus, InterviewMode
        db_interview = Interview(
            organization_id=org.id,
            job_position_id=job.id,
            candidate_id=user.id,  # Now using User record
            template_id=template.id,
            status=InterviewStatus.IN_PROGRESS.value,
            mode=InterviewMode.CHAT.value,
            started_at=datetime.now(timezone.utc),
            settings={
                "interview_type": interview_data.interview_type,
                "difficulty": interview_data.difficulty,
                "max_questions": interview_data.max_questions,
                "target_duration_minutes": interview_data.target_duration_minutes,
                "session_id": session_id,
                "candidate_record_id": str(candidate.id)  # Store candidate record ID in settings for reference
            }
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
                "job_id": str(job.id),
                "session_id": session_id
            }
        )
        db.add(audit_log)
        db.commit()
        
        log_info(f"Started interview: {session_id}")
        
        return {
            "session_id": session_id,
            "interview_id": str(db_interview.id),
            "candidate_name": getattr(candidate, 'full_name', None) or getattr(candidate, 'name', 'Candidate'),
            "job_title": job.title,
            "initial_question": initial_question,
            "status": "in_progress"
        }
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        log_error(f"Error starting interview: {e}")
        log_error(f"Full traceback:\n{error_traceback}")
        # Also print to console for immediate visibility
        print(f"\n{'='*60}")
        print(f"ERROR in start_interview endpoint:")
        print(f"{'='*60}")
        print(f"Error: {e}")
        print(f"\nTraceback:\n{error_traceback}")
        print(f"{'='*60}\n")
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {str(e)}")

@app.post("/api/interviews/{session_id}/respond")
async def submit_response(
    session_id: str,
    response_data: InterviewResponseSchema,
    db: Session = Depends(get_db)
):
    """Submit candidate response and get next question"""
    try:
        # Get interview by session_id from settings
        interviews = db.query(Interview).all()
        interview = None
        for i in interviews:
            if i.settings and i.settings.get('session_id') == session_id:
                interview = i
                break
        
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        from database.models import InterviewStatus
        if interview.status != InterviewStatus.IN_PROGRESS:
            raise HTTPException(status_code=400, detail="Interview is not active")
        
        # Get current question from InterviewSession
        from database.models import InterviewSession
        current_session = db.query(InterviewSession).filter(
            InterviewSession.interview_id == interview.id
        ).order_by(InterviewSession.created_at.desc()).first()
        
        if not current_session:
            # Create initial session
            current_session = db_service.create_interview_session(
                interview_id=str(interview.id),
                question_id=str(uuid.uuid4()),
                question_text=interview.settings.get('initial_question', 'Tell me about yourself.'),
                question_type='general'
            )
        
        current_question_text = current_session.question_text
        
        # Initialize database service
        db_service = InterviewDataService(db)
        
        # Create or get interview session for this question
        session = db_service.create_interview_session(
            interview_id=str(interview.id),
            question_id=str(current_session.id),
            question_text=current_question_text,
            question_type='general'
        )
        
        # Anti-cheating analysis
        cheating_analysis = await anti_cheating_service.analyze_response(
            response_data.response_text, interview.id, db
        )
        
        # NLP evaluation
        candidate_id_from_settings = interview.settings.get('candidate_id') if interview.settings else None
        nlp_evaluation = await nlp_service.evaluate_response(
            current_question_text,
            response_data.response_text,
            candidate_id_from_settings,
            str(interview.job_position_id),
            db
        )
        
        # Complete the interview session with candidate response
        response_duration = response_data.response_time_seconds if hasattr(response_data, 'response_time_seconds') else None
        completed_session = db_service.complete_interview_session(
            session_id=str(session.id),
            candidate_response=response_data.response_text,
            response_duration=int(response_duration) if response_duration else None
        )
        
        # Create response record
        from database.models import Response
        db_response = Response(
            interview_id=interview.id,
            session_id=session.id,
            responder_id=candidate_id_from_settings or interview.candidate_id or uuid.uuid4(),
            response_text=response_data.response_text,
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
            response_time_seconds=response_duration
        )
        
        db.add(db_response)
        
        # Store AI analysis in ai_analysis table (automatically)
        try:
            # Get candidate and job context for analysis
            candidate = db.query(Candidate).filter(Candidate.id == interview.candidate_id).first() if interview.candidate_id else None
            job = db.query(JobPosition).filter(JobPosition.id == interview.job_position_id).first() if interview.job_position_id else None
            
            candidate_context = None
            job_context = None
            
            if candidate:
                candidate_context = {
                    "name": getattr(candidate, 'full_name', getattr(candidate, 'name', '')),
                    "skills": getattr(candidate, 'skills', [])
                }
            
            if job:
                job_context = {
                    "title": getattr(job, 'title', ''),
                    "required_skills": getattr(job, 'skills_required', getattr(job, 'required_skills', []))
                }
            
            # Automatically evaluate and store AI analysis
            analysis_result = await interview_service.evaluate_and_store_response_analysis(
                interview_id=str(interview.id),
                session_id=str(session.id),
                question_text=current_question.question_text,
                response_text=response_data.response_text,
                response_time_seconds=response_duration,
                question_number=interview.current_question_index,
                candidate_context=candidate_context,
                job_context=job_context,
                db=db
            )
            
            log_info(f"✅ AI analysis stored: {analysis_result.get('analysis_id')} with confidence {analysis_result.get('confidence_score')}")
            
        except Exception as e:
            log_error(f"⚠️ Failed to store AI analysis (continuing anyway): {e}")
            # Don't fail the entire request if AI analysis storage fails
        
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
        
        async with aiofiles.open(file_path, "wb") as buffer:
            content = await file.read()
            await buffer.write(content)
        
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
