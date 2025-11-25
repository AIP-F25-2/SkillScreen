"""
FastAPI production application for SkillScreen
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict
import json
import uuid
from datetime import datetime, timezone
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
from utils.logger import log_info, log_error, log_warning

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
        "timestamp": datetime.now(timezone.utc).isoformat(),
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
    """Create a new candidate - using in-memory storage for testing"""
    try:
        from in_memory_storage import create_candidate as create_candidate_memory, get_candidate as get_candidate_memory
        
        # Store in memory
        candidate_data = {
            "name": candidate.name,
            "email": candidate.email,
            "phone": getattr(candidate, 'phone', None),
            "skills": candidate.skills or [],
            "experience_years": getattr(candidate, 'experience_years', 0.0),
            "education": candidate.education or ""
        }
        
        candidate_id = create_candidate_memory(candidate_data)
        stored_candidate = get_candidate_memory(candidate_id)
        
        log_info(f"Created candidate in memory: {candidate_id}")
        
        return {
            "id": candidate_id,
            "name": stored_candidate["name"],
            "email": stored_candidate["email"],
            "created_at": stored_candidate["created_at"]
        }
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        log_error(f"Error creating candidate: {e}")
        log_error(f"Full traceback:\n{error_traceback}")
        print(f"\n{'='*60}")
        print(f"ERROR in create_candidate endpoint:")
        print(f"{'='*60}")
        print(f"Error: {e}")
        print(f"\nTraceback:\n{error_traceback}")
        print(f"{'='*60}\n")
        raise HTTPException(status_code=500, detail=f"Failed to create candidate: {str(e)}")

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
    """Create a new job posting - using in-memory storage for testing"""
    try:
        from in_memory_storage import create_job as create_job_memory, get_job as get_job_memory
        
        # Store in memory
        job_data = {
            "title": job.title,
            "company": job.company,
            "description": job.description or f"Position at {job.company}",
            "required_skills": job.skills_required or [],
            "experience_level": getattr(job, 'experience_level', 'Mid-level') or 'Mid-level'
        }
        
        job_id = create_job_memory(job_data)
        stored_job = get_job_memory(job_id)
        
        log_info(f"Created job in memory: {job_id}")
        
        return {
            "id": job_id,
            "title": stored_job["title"],
            "company": stored_job["company"],
            "created_at": stored_job["created_at"]
        }
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        log_error(f"Error creating job: {e}")
        log_error(f"Full traceback:\n{error_traceback}")
        print(f"\n{'='*60}")
        print(f"ERROR in create_job endpoint:")
        print(f"{'='*60}")
        print(f"Error: {e}")
        print(f"\nTraceback:\n{error_traceback}")
        print(f"{'='*60}\n")
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")

@app.get("/api/jobs/{job_id}")
async def get_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Get job by ID"""
    job = db.query(JobPosition).filter(JobPosition.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # JobPosition model only has: id, organization_id, title, description, required_skills, department, is_active, created_by
    # Other fields (company, requirements, experience_level, job_type, location, salary_range) are not in the model
    return {
        "id": str(job.id),
        "title": job.title,
        "company": "N/A",  # Not stored in JobPosition model
        "description": job.description,
        "requirements": [],  # Not in model
        "skills_required": job.required_skills or [],
        "experience_level": "Mid-level",  # Not in model, default value
        "job_type": job.department or "Full-time",  # Use department as fallback
        "location": None,  # Not in model
        "salary_range": None,  # Not in model
        "created_at": job.created_at.isoformat()
    }

# Interview endpoints
@app.post("/api/interviews/start")
async def start_interview(
    interview_data: InterviewStart,
    db: Session = Depends(get_db)
):
    """Start a new interview session - using in-memory storage for testing"""
    try:
        from in_memory_storage import (
            get_candidate, get_job, create_interview, 
            add_question, update_interview
        )
        
        # Get candidate and job from memory
        candidate_data = get_candidate(interview_data.candidate_id)
        job_data = get_job(interview_data.job_id)
        
        if not candidate_data:
            raise HTTPException(status_code=404, detail="Candidate not found")
        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Create mock Candidate and JobPosition objects for interview_service
        class MockCandidate:
            def __init__(self, data):
                self.id = data["id"]
                self.full_name = data.get("name", "Unknown")
                self.name = data.get("name", "Unknown")
                self.email = data.get("email", "")
                self.skills = data.get("skills", [])
                self.experience = {"years": data.get("experience_years", 0.0)}
                self.education = data.get("education", {})
        
        class MockJob:
            def __init__(self, data):
                self.id = data["id"]
                self.title = data.get("title", "")
                self.company = data.get("company", "")
                self.required_skills = data.get("required_skills", [])
                self.skills_required = data.get("required_skills", [])
                self.experience_level = data.get("experience_level", "Mid-level")
                self.description = data.get("description", "")
        
        mock_candidate = MockCandidate(candidate_data)
        mock_job = MockJob(job_data)
        
        # Generate initial question using interview service
        initial_question_data = await interview_service.generate_initial_question(
            mock_candidate, mock_job, interview_data.interview_type, None  # Pass None for db
        )
        
        # Extract question text
        if isinstance(initial_question_data, dict):
            initial_question_text = initial_question_data.get('question_text', 'Tell me about yourself.')
        else:
            initial_question_text = str(initial_question_data) if initial_question_data else 'Tell me about yourself.'
        
        # Create interview in memory
        # Ensure max_questions is 10-12 (not 5) for proper interview length
        max_questions = interview_data.max_questions if interview_data.max_questions and interview_data.max_questions >= 10 else 12
        
        session_id = create_interview({
            "candidate_id": interview_data.candidate_id,
            "job_id": interview_data.job_id,
            "interview_type": interview_data.interview_type,
            "difficulty": interview_data.difficulty,
            "max_questions": max_questions,  # Use 10-12 questions
            "target_duration_minutes": interview_data.target_duration_minutes or 20,  # 15-25 mins
            "initial_question": initial_question_text
        })
        
        # Store initial question
        add_question(session_id, {
            "question_text": initial_question_text,
            "question_type": "general",
            "question_index": 0
        })
        
        log_info(f"Started interview in memory: {session_id}")
        
        return {
            "session_id": session_id,
            "interview_id": session_id,  # Use session_id as interview_id for simplicity
            "candidate_name": candidate_data.get("name", "Candidate"),
            "job_title": job_data.get("title", "Job"),
            "initial_question": initial_question_text,
            "status": "in_progress"
        }
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        log_error(f"Error starting interview: {e}")
        log_error(f"Full traceback:\n{error_traceback}")
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
    """Submit candidate response and get next question - using in-memory storage for testing"""
    try:
        from in_memory_storage import (
            get_interview_by_session, get_candidate, get_job,
            add_response, add_question, update_interview,
            get_questions, get_responses
        )
        
        # Get interview from memory
        interview_data = get_interview_by_session(session_id)
        if not interview_data:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        if interview_data.get("status") != "in_progress":
            raise HTTPException(status_code=400, detail="Interview is not active")
        
        # Get current question
        questions = get_questions(session_id)
        if not questions:
            current_question_text = interview_data.get("initial_question", "Tell me about yourself.")
        else:
            current_question_text = questions[-1].get("question_text", "Tell me about yourself.")
        
        # Get candidate and job data
        candidate_data = get_candidate(interview_data["candidate_id"])
        job_data = get_job(interview_data["job_id"])
        
        # Create mock objects for services
        class MockCandidate:
            def __init__(self, data):
                self.id = data["id"]
                self.full_name = data.get("name", "Unknown")
                self.name = data.get("name", "Unknown")
                self.email = data.get("email", "")
                self.skills = data.get("skills", [])
                self.experience = {"years": data.get("experience_years", 0.0)}
                self.education = data.get("education", {})
        
        class MockJob:
            def __init__(self, data):
                self.id = data["id"]
                self.title = data.get("title", "")
                self.company = data.get("company", "")
                self.required_skills = data.get("required_skills", [])
                self.skills_required = data.get("required_skills", [])
                self.experience_level = data.get("experience_level", "Mid-level")
                self.description = data.get("description", "")
        
        class MockInterview:
            def __init__(self, data):
                self.id = data["id"]
                self.settings = data.get("settings", {})
                self.candidate_id = data.get("candidate_id")
                self.job_position_id = data.get("job_id")
                self.current_question_index = data.get("current_question_index", 0)
                self.max_questions = data.get("max_questions", 15)
        
        mock_candidate = MockCandidate(candidate_data)
        mock_job = MockJob(job_data)
        mock_interview = MockInterview(interview_data)
        
        # Anti-cheating analysis
        cheating_analysis = await anti_cheating_service.analyze_response(
            response_data.response_text, session_id, None  # Pass None for db
        )
        
        # NLP evaluation
        nlp_evaluation = await nlp_service.evaluate_response(
            current_question_text,
            response_data.response_text,
            interview_data["candidate_id"],
            interview_data["job_id"],
            None  # Pass None for db
        )
        
        # Store response in memory
        response_duration = getattr(response_data, 'response_time_seconds', None)
        add_response(session_id, {
            "response_text": response_data.response_text,
            "question_text": current_question_text,
            "scores": nlp_evaluation,
            "response_time_seconds": response_duration,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Update interview progress
        responses = get_responses(session_id)
        current_index = len(responses)  # This is the count AFTER adding the current response
        max_questions = interview_data.get("max_questions", 12)  # Default to 12
        
        # Ensure max_questions is at least 10
        if max_questions < 10:
            max_questions = 12
            log_warning(f"[INTERVIEW] max_questions was {interview_data.get('max_questions')}, setting to 12")
        
        update_interview(session_id, {
            "current_question_index": current_index,
            "total_responses_received": len(responses),
            "max_questions": max_questions  # Ensure it's saved
        })
        
        # Check if interview should continue
        # After answering Q1, current_index = 1, we should continue (1 < 12)
        # After answering Q12, current_index = 12, we should stop (12 >= 12)
        # So we check: current_index >= max_questions
        
        log_info(f"[INTERVIEW PROGRESS] Questions answered: {current_index}/{max_questions}")
        log_info(f"[INTERVIEW PROGRESS] Will continue: {current_index < max_questions} (anti-cheat termination: {cheating_analysis.get('should_terminate', False)})")
        
        if (cheating_analysis.get('should_terminate', False) or 
            current_index >= max_questions):
            # Generate interview summary before completing
            try:
                from in_memory_storage import get_responses, get_questions
                all_responses = get_responses(session_id)
                all_questions = get_questions(session_id)
                
                # Calculate overall score from responses
                overall_score = 0.0
                if all_responses:
                    scores = [r.get("scores", {}).get("overall_score", 0.0) for r in all_responses]
                    overall_score = sum(scores) / len(scores) if scores else 0.0
                
                # Generate summary
                summary = {
                    "executive_summary": f"Interview completed with {len(all_responses)} responses. Overall score: {overall_score:.1f}/10.",
                    "overall_score": round(overall_score, 1),
                    "total_questions": len(all_questions),
                    "total_responses": len(all_responses),
                    "recommendation": "Consider" if overall_score >= 5.0 else "Do Not Hire",
                    "recommendation_reason": f"Overall performance score of {overall_score:.1f}/10",
                    "strengths": ["Completed all interview questions"] if len(all_responses) >= max_questions else [],
                    "areas_for_improvement": ["Continue developing interview skills"],
                    "improvement_tips": [
                        "Provide more detailed responses",
                        "Use specific examples from your experience",
                        "Structure answers using the STAR method"
                    ]
                }
                
                update_interview(session_id, {
                    "status": "completed",
                    "end_time": datetime.now(timezone.utc).isoformat(),
                    "summary": summary
                })
                
                log_info(f"Interview completed. Generated summary with score {overall_score:.1f}/10")
                
                return {
                    "status": "completed",
                    "summary": summary,
                    "termination_reason": "completed" if current_index >= max_questions else "anti_cheating"
                }
            except Exception as e:
                log_error(f"Error generating summary: {e}")
                update_interview(session_id, {
                    "status": "completed",
                    "end_time": datetime.now(timezone.utc).isoformat()
                })
                return {
                    "status": "completed",
                    "summary": {"message": "Interview completed"},
                    "termination_reason": "completed" if current_index >= max_questions else "anti_cheating"
                }
        
        # Generate next question - THIS IS WHERE CODING QUESTIONS ARE GENERATED
        # The interview_service will check if we're in the last 1-2 questions
        next_question_data = await interview_service.generate_next_question(
            session_id, None  # Pass None for db, but we need to adapt this
        )
        
        # Extract question text
        if isinstance(next_question_data, dict):
            next_question_text = next_question_data.get('question_text', 'Next question')
            is_coding = next_question_data.get('is_coding_question', False)
            coding_data = next_question_data.get('coding_data', {})
        else:
            next_question_text = str(next_question_data)
            is_coding = False
            coding_data = {}
        
        # Store next question with proper question type
        question_type = next_question_data.get('question_type', 'general') if isinstance(next_question_data, dict) else 'general'
        add_question(session_id, {
            "question_text": next_question_text,
            "question_type": question_type,  # Use actual question type from generation
            "question_index": current_index,
            "is_coding_question": is_coding,
            "coding_data": coding_data
        })
        
        update_interview(session_id, {
            "total_questions_asked": len(get_questions(session_id))
        })
        
        # Return response
        response_dict = {
            "status": "continue",
            "next_question": next_question_text,
            "current_score": nlp_evaluation.get('overall_score', 0.0),
            "anti_cheating_flags": cheating_analysis
        }
        
        # Include coding question data if it's a coding question
        if is_coding:
            response_dict["is_coding_question"] = True
            response_dict["coding_session_id"] = next_question_data.get('coding_session_id')
            response_dict["coding_data"] = coding_data
        
        log_info(f"Response processed. Next question: {'CODING' if is_coding else 'REGULAR'}")
        
        return response_dict
        
    except Exception as e:
        import traceback
        log_error(f"Error processing response: {e}")
        log_error(f"Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to process response: {str(e)}")

@app.get("/api/interviews/{session_id}/status")
async def get_interview_status(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get current interview status - using in-memory storage for testing"""
    from in_memory_storage import get_interview_by_session, get_responses, get_questions
    
    interview_data = get_interview_by_session(session_id)
    if not interview_data:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    responses = get_responses(session_id)
    questions = get_questions(session_id)
    
    return {
        "session_id": session_id,
        "status": interview_data.get("status", "in_progress"),
        "current_question_index": len(questions),
        "total_questions_asked": len(questions),
        "responses_received": len(responses),
        "total_responses_received": len(responses),
        "overall_score": 0.0,  # Calculate from responses if needed
        "start_time": interview_data.get("started_at"),
        "end_time": interview_data.get("end_time")
    }

# Coding question endpoints
@app.post("/api/interviews/{session_id}/coding-question")
async def generate_coding_question(
    session_id: str,
    difficulty: str = "medium",
    db: Session = Depends(get_db)
):
    """Generate a coding question for the interview"""
    try:
        # Get interview by session_id
        interviews = db.query(Interview).all()
        interview = None
        for i in interviews:
            if i.settings and i.settings.get('session_id') == session_id:
                interview = i
                break
        
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        # Get job and candidate
        job = db.query(JobPosition).filter(JobPosition.id == interview.job_position_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        candidate_id = interview.settings.get('candidate_record_id') if interview.settings else None
        candidate = None
        if candidate_id:
            candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        
        if not candidate:
            # Try to get from User email
            from database.models import User
            user = db.query(User).filter(User.id == interview.candidate_id).first()
            if user:
                candidate = db.query(Candidate).filter(Candidate.email == user.email).first()
        
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Generate coding question
        from services.coding_question_service import coding_question_service
        coding_question = await coding_question_service.generate_coding_question(
            interview_id=str(interview.id),
            job=job,
            candidate=candidate,
            difficulty=difficulty,
            db=db
        )
        
        log_info(f"✅ Generated coding question for interview {interview.id}")
        return coding_question
        
    except Exception as e:
        log_error(f"Error generating coding question: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate coding question: {str(e)}")

@app.post("/api/coding-sessions/{session_id}/submit")
async def submit_code_solution(
    session_id: str,
    code: str = Body(...),
    language: str = Body(...),
    db: Session = Depends(get_db)
):
    """Submit code solution for a coding session"""
    try:
        from services.coding_question_service import coding_question_service
        
        result = await coding_question_service.submit_code_solution(
            session_id=session_id,
            code=code,
            language=language,
            db=db
        )
        
        log_info(f"✅ Code solution submitted for session {session_id}")
        return result
        
    except Exception as e:
        log_error(f"Error submitting code solution: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit code: {str(e)}")

@app.get("/api/coding-sessions/{session_id}/status")
async def get_coding_session_status(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get status of a coding session"""
    try:
        from services.coding_question_service import coding_question_service
        
        status = await coding_question_service.get_coding_session_status(
            session_id=session_id,
            db=db
        )
        
        return status
        
    except Exception as e:
        log_error(f"Error getting coding session status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@app.post("/api/coding-sessions/{session_id}/execute")
async def execute_code(
    session_id: str,
    code: str = Body(...),
    language: str = Body(...),
    db: Session = Depends(get_db)
):
    """Execute code without submitting (for testing)"""
    try:
        from services.code_execution_service import code_execution_service
        
        # Get coding session to check if it exists
        from database.models import CodingSession
        coding_session = db.query(CodingSession).filter(CodingSession.id == session_id).first()
        if not coding_session:
            raise HTTPException(status_code=404, detail="Coding session not found")
        
        # Execute code
        result = await code_execution_service.execute_code(
            code=code,
            language=language,
            test_cases=None,  # Don't run test cases for execution-only
            timeout=10
        )
        
        return {
            'success': result.get('success', False),
            'output': result.get('output', ''),
            'error': result.get('error', ''),
            'execution_time': result.get('execution_time', 0)
        }
        
    except Exception as e:
        log_error(f"Error executing code: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute code: {str(e)}")

@app.post("/api/code-editor/sessions")
async def create_code_editor_session(
    coding_session_id: str = Body(...),
    question_data: Dict = Body(...),
    language: str = Body("python")
):
    """Create a new code editor session"""
    try:
        from services.code_editor_service import code_editor_service
        
        result = code_editor_service.create_editor_session(
            coding_session_id=coding_session_id,
            question_data=question_data,
            language=language
        )
        
        return result
        
    except Exception as e:
        log_error(f"Error creating code editor session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create code editor session: {str(e)}")

@app.put("/api/code-editor/sessions/{editor_session_id}/code")
async def update_code_in_editor(
    editor_session_id: str,
    code: str = Body(...),
    language: Optional[str] = Body(None)
):
    """Update code in an editor session"""
    try:
        from services.code_editor_service import code_editor_service
        
        result = code_editor_service.update_code(
            editor_session_id=editor_session_id,
            code=code,
            language=language
        )
        
        return result
        
    except Exception as e:
        log_error(f"Error updating code: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update code: {str(e)}")

@app.post("/api/code-editor/sessions/{editor_session_id}/execute")
async def execute_code_from_editor(
    editor_session_id: str,
    code: Optional[str] = Body(None)
):
    """Execute code from an editor session"""
    try:
        from services.code_editor_service import code_editor_service
        
        result = await code_editor_service.execute_code(
            editor_session_id=editor_session_id,
            code=code
        )
        
        return result
        
    except Exception as e:
        log_error(f"Error executing code: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute code: {str(e)}")

@app.post("/api/code-editor/sessions/{editor_session_id}/run-tests")
async def run_tests_for_editor(
    editor_session_id: str,
    code: Optional[str] = Body(None)
):
    """Run test cases for code in an editor session"""
    try:
        from services.code_editor_service import code_editor_service
        
        result = await code_editor_service.run_tests(
            editor_session_id=editor_session_id,
            code=code
        )
        
        return result
        
    except Exception as e:
        log_error(f"Error running tests: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to run tests: {str(e)}")

@app.get("/api/code-editor/sessions/{editor_session_id}")
async def get_editor_session(editor_session_id: str):
    """Get editor session details"""
    try:
        from services.code_editor_service import code_editor_service
        
        session = code_editor_service.get_editor_session(editor_session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Editor session not found")
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error getting editor session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get editor session: {str(e)}")

@app.get("/api/code-editor/languages")
async def get_supported_languages():
    """Get list of supported programming languages"""
    try:
        from services.code_editor_service import code_editor_service
        
        languages = code_editor_service.get_supported_languages()
        return {"languages": languages}
        
    except Exception as e:
        log_error(f"Error getting supported languages: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get supported languages: {str(e)}")

@app.get("/api/interviews/{session_id}/summary")
async def get_interview_summary(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get interview summary - supports both database and in-memory storage"""
    try:
        from in_memory_storage import get_interview_by_session, get_responses, get_questions, get_candidate, get_job
        
        # Try in-memory storage first
        interview_data = get_interview_by_session(session_id)
        if interview_data:
            # Generate summary from in-memory data
            all_responses = get_responses(session_id)
            all_questions = get_questions(session_id)
            candidate_data = get_candidate(interview_data["candidate_id"])
            job_data = get_job(interview_data["job_id"])
            
            if not all_responses:
                return {
                    "executive_summary": "Interview in progress. No responses yet.",
                    "overall_score": 0.0,
                    "total_questions": len(all_questions),
                    "total_responses": 0,
                    "status": "in_progress"
                }
            
            # Calculate overall score
            overall_score = 0.0
            if all_responses:
                scores = [r.get("scores", {}).get("overall_score", 0.0) for r in all_responses if r.get("scores")]
                overall_score = sum(scores) / len(scores) if scores else 0.0
            
            # Generate comprehensive summary using LLM
            try:
                from services.llm_service import llm_service
                
                # Build context for summary generation
                candidate_context = {
                    'name': candidate_data.get("name", "Candidate"),
                    'skills': candidate_data.get("skills", []),
                    'experience_years': candidate_data.get("experience_years", 0)
                }
                
                job_context = {
                    'title': job_data.get("title", ""),
                    'company': job_data.get("company", ""),
                    'required_skills': job_data.get("required_skills", [])
                }
                
                # Generate summary using LLM
                summary_prompt = f"""Generate a comprehensive interview summary for a candidate interview.

Candidate: {candidate_context['name']} with {candidate_context['experience_years']} years of experience
Skills: {', '.join(candidate_context['skills'][:10])}
Job: {job_context['title']} at {job_context['company']}
Required Skills: {', '.join(job_context['required_skills'][:10])}

Interview Statistics:
- Total Questions: {len(all_questions)}
- Total Responses: {len(all_responses)}
- Overall Score: {overall_score:.1f}/10

Responses Summary:
{chr(10).join([f"Q{i+1}: {q.get('question_text', '')[:100]}... | Response: {r.get('response_text', '')[:150]}..." for i, (q, r) in enumerate(zip(all_questions[:5], all_responses[:5]))])}

Generate a professional interview summary with:
1. Executive Summary (2-3 sentences)
2. Overall Assessment
3. Strengths (3-5 points)
4. Areas for Improvement (3-5 points)
5. Recommendation (Hire/Strong Consider/Consider/Do Not Hire)
6. Recommendation Reason
7. Improvement Tips (3-5 actionable tips)

Format as JSON with keys: executive_summary, overall_assessment, strengths (array), areas_for_improvement (array), recommendation, recommendation_reason, improvement_tips (array)"""
                
                if llm_service.gemini_model:
                    import asyncio
                    loop = asyncio.get_event_loop()
                    llm_summary = await loop.run_in_executor(
                        None,
                        lambda: llm_service.gemini_model.generate_content(summary_prompt)
                    )
                    if llm_summary and llm_summary.text:
                        import json
                        try:
                            summary_json = json.loads(llm_summary.text)
                            return {
                                "executive_summary": summary_json.get("executive_summary", f"Interview completed with overall score {overall_score:.1f}/10"),
                                "overall_score": round(overall_score, 1),
                                "recommendation": summary_json.get("recommendation", "Consider"),
                                "recommendation_reason": summary_json.get("recommendation_reason", f"Overall performance score of {overall_score:.1f}/10"),
                                "strengths": summary_json.get("strengths", []),
                                "areas_for_improvement": summary_json.get("areas_for_improvement", []),
                                "improvement_tips": summary_json.get("improvement_tips", []),
                                "total_questions": len(all_questions),
                                "total_responses": len(all_responses),
                                "generated_at": datetime.now(timezone.utc).isoformat()
                            }
                        except:
                            pass
            except Exception as e:
                log_warning(f"LLM summary generation failed: {e}. Using fallback.")
            
            # Fallback summary
            return {
                "executive_summary": f"Interview completed for {candidate_data.get('name', 'Candidate')}. Overall score: {overall_score:.1f}/10 based on {len(all_responses)} responses.",
                "overall_score": round(overall_score, 1),
                "recommendation": "Hire" if overall_score >= 7.0 else "Strong Consider" if overall_score >= 5.0 else "Consider" if overall_score >= 3.0 else "Do Not Hire",
                "recommendation_reason": f"Overall performance score of {overall_score:.1f}/10 based on {len(all_responses)} responses",
                "strengths": ["Completed all interview questions"] if len(all_responses) >= interview_data.get("max_questions", 12) else [],
                "areas_for_improvement": ["Continue developing interview skills"],
                "improvement_tips": [
                    "Provide more detailed responses",
                    "Use specific examples from your experience",
                    "Structure answers using the STAR method"
                ],
                "total_questions": len(all_questions),
                "total_responses": len(all_responses),
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        
        # Database path (original logic)
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
        
    except Exception as e:
        log_error(f"Error getting interview summary: {e}")
        import traceback
        log_error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get interview summary: {str(e)}")

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

# ML-Specific API Endpoints
@app.get("/api/interviews/{interview_id}/behavioral-analysis")
async def get_behavioral_analysis(
    interview_id: str,
    db: Session = Depends(get_db)
):
    """Get behavioral analysis for an interview"""
    try:
        from services.behavioral_analysis_service import behavioral_analysis_service
        from database.models import Interview, Response
        
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        # Get all responses
        responses = db.query(Response).filter(
            Response.interview_id == interview_id
        ).order_by(Response.created_at).all()
        
        if not responses:
            return {
                "interview_id": interview_id,
                "status": "no_responses",
                "message": "No responses found for this interview"
            }
        
        # Aggregate behavioral analysis
        behavioral_patterns = []
        for idx, response in enumerate(responses):
            pattern = await behavioral_analysis_service.analyze_behavioral_patterns(
                response_text=response.response_text,
                interview_id=interview_id,
                response_time_seconds=response.response_time_seconds,
                question_number=idx + 1
            )
            behavioral_patterns.append(pattern)
        
        # Get overall behavioral summary
        behavior_types = [p.get('behavior_type') for p in behavioral_patterns if p.get('behavior_type')]
        most_common_behavior = max(set(behavior_types), key=behavior_types.count) if behavior_types else 'unknown'
        
        return {
            "interview_id": interview_id,
            "total_responses": len(responses),
            "behavioral_patterns": behavioral_patterns,
            "overall_behavior_type": most_common_behavior,
            "summary": {
                "consistent_behavior": len(set(behavior_types)) == 1 if behavior_types else False,
                "behavior_diversity": len(set(behavior_types)) if behavior_types else 0
            }
        }
        
    except Exception as e:
        log_error(f"Error getting behavioral analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get behavioral analysis: {str(e)}")

@app.get("/api/interviews/{interview_id}/bias-report")
async def get_bias_report(
    interview_id: str,
    db: Session = Depends(get_db)
):
    """Generate comprehensive bias detection report"""
    try:
        from services.bias_detection_service import bias_detection_service
        from database.models import Interview, Response, Candidate
        
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        # Get candidate
        candidate = db.query(Candidate).filter(Candidate.id == interview.candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Get all responses and scores
        responses = db.query(Response).filter(
            Response.interview_id == interview_id
        ).all()
        
        if not responses:
            return {
                "interview_id": interview_id,
                "status": "no_data",
                "message": "No responses found for bias analysis"
            }
        
        # Perform bias detection
        scores = {
            'overall_score': [r.overall_score if hasattr(r, 'overall_score') else 5.0 for r in responses],
            'technical_score': [r.technical_accuracy_score if hasattr(r, 'technical_accuracy_score') else 5.0 for r in responses],
            'communication_score': [r.communication_score if hasattr(r, 'communication_score') else 5.0 for r in responses]
        }
        
        bias_result = await bias_detection_service.detect_bias_in_scoring(
            interview_id=interview_id,
            candidate_id=str(candidate.id),
            scores=scores,
            db=db
        )
        
        # Get bias summary
        bias_summary = bias_detection_service.get_bias_summary()
        
        return {
            "interview_id": interview_id,
            "bias_detected": bias_result.get('bias_detected', False),
            "bias_type": bias_result.get('bias_type', 'none'),
            "bias_details": bias_result,
            "bias_summary": bias_summary,
            "recommendations": bias_result.get('recommendations', []),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        log_error(f"Error generating bias report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate bias report: {str(e)}")

@app.get("/api/interviews/{interview_id}/ml-predictions")
async def get_ml_predictions(
    interview_id: str,
    db: Session = Depends(get_db)
):
    """Get all ML predictions for an interview"""
    try:
        from services.quality_prediction_service import quality_prediction_service
        from services.behavioral_analysis_service import behavioral_analysis_service
        from database.models import Interview, Response, Candidate, JobPosition
        
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        candidate = db.query(Candidate).filter(Candidate.id == interview.candidate_id).first()
        job = db.query(JobPosition).filter(JobPosition.id == interview.job_position_id).first()
        
        responses = db.query(Response).filter(
            Response.interview_id == interview_id
        ).order_by(Response.created_at).all()
        
        predictions = []
        for idx, response in enumerate(responses):
            # Quality prediction
            candidate_ctx = {
                'experience_years': candidate.experience.get('years', 0) if candidate and candidate.experience else 0,
                'skills': candidate.skills if candidate else []
            } if candidate else {}
            
            job_ctx = {
                'title': job.title if job else '',
                'required_skills': getattr(job, 'required_skills', getattr(job, 'skills_required', [])),
                'experience_level': getattr(job, 'experience_level', 'mid')
            } if job else {}
            
            ml_pred = await quality_prediction_service.predict_quality_score(
                question="",  # Question not needed for prediction
                response=response.response_text,
                candidate_context=candidate_ctx,
                job_context=job_ctx
            )
            
            # Behavioral analysis
            behavioral = await behavioral_analysis_service.analyze_behavioral_patterns(
                response_text=response.response_text,
                interview_id=interview_id,
                response_time_seconds=response.response_time_seconds,
                question_number=idx + 1
            )
            
            predictions.append({
                "response_id": str(response.id),
                "quality_prediction": ml_pred,
                "behavioral_analysis": behavioral,
                "timestamp": response.created_at.isoformat() if response.created_at else None
            })
        
        return {
            "interview_id": interview_id,
            "total_predictions": len(predictions),
            "predictions": predictions
        }
        
    except Exception as e:
        log_error(f"Error getting ML predictions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get ML predictions: {str(e)}")

@app.post("/api/ml/train-quality-model")
async def train_quality_model(
    training_data: List[Dict] = Body(...),
    db: Session = Depends(get_db)
):
    """Train the quality prediction model on provided data"""
    try:
        from services.quality_prediction_service import quality_prediction_service
        
        if len(training_data) < 10:
            raise HTTPException(
                status_code=400,
                detail="Insufficient training data. Need at least 10 samples."
            )
        
        result = await quality_prediction_service.train_model(training_data)
        
        if not result.get('success'):
            raise HTTPException(
                status_code=400,
                detail=result.get('message', 'Training failed')
            )
        
        return {
            "status": "success",
            "message": "Model trained successfully",
            "training_result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error training model: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to train model: {str(e)}")

@app.get("/api/ml/model-info")
async def get_model_info():
    """Get model information and performance metrics"""
    try:
        from services.quality_prediction_service import quality_prediction_service
        from services.model_monitoring_service import model_monitoring_service
        
        model_info = {
            "quality_prediction": {
                "model_trained": quality_prediction_service.model_trained,
                "models_available": list(quality_prediction_service.models.keys()),
                "feature_count": len(quality_prediction_service.feature_names),
                "features": quality_prediction_service.feature_names
            }
        }
        
        # Get performance metrics if available
        performance = model_monitoring_service.get_performance_metrics("quality_prediction")
        if performance.get('status') == 'active':
            model_info["quality_prediction"]["performance"] = performance.get('metrics')
        
        return model_info
        
    except Exception as e:
        log_error(f"Error getting model info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")

@app.post("/api/ml/retrain")
async def retrain_model(
    use_historical_data: bool = Body(True),
    db: Session = Depends(get_db)
):
    """Trigger model retraining"""
    try:
        from services.quality_prediction_service import quality_prediction_service
        from database.models import Interview, Response, Score
        
        if use_historical_data:
            # Collect training data from database
            interviews = db.query(Interview).filter(
                Interview.status == 'completed'
            ).limit(100).all()
            
            training_data = []
            for interview in interviews:
                responses = db.query(Response).filter(
                    Response.interview_id == interview.id
                ).all()
                
                for response in responses:
                    scores = db.query(Score).filter(
                        Score.response_id == response.id
                    ).first()
                    
                    if scores:
                        training_data.append({
                            'question': '',  # Question text not stored
                            'response': response.response_text,
                            'actual_score': scores.overall_score if hasattr(scores, 'overall_score') else 5.0,
                            'candidate_context': {},
                            'job_context': {}
                        })
            
            if len(training_data) < 10:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient historical data. Found {len(training_data)} samples, need at least 10."
                )
            
            result = await quality_prediction_service.train_model(training_data)
            
            return {
                "status": "success" if result.get('success') else "failed",
                "message": "Model retrained using historical data",
                "training_samples": len(training_data),
                "result": result
            }
        else:
            return {
                "status": "pending",
                "message": "Manual retraining requires training data to be provided via /api/ml/train-quality-model"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error retraining model: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrain model: {str(e)}")

@app.get("/api/ml/feature-importance")
async def get_feature_importance():
    """Get feature importance for models"""
    try:
        from services.quality_prediction_service import quality_prediction_service
        
        importance = quality_prediction_service._get_feature_importance()
        
        return {
            "model": "quality_prediction",
            "feature_importance": importance,
            "total_features": len(quality_prediction_service.feature_names),
            "features": quality_prediction_service.feature_names
        }
        
    except Exception as e:
        log_error(f"Error getting feature importance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get feature importance: {str(e)}")

@app.post("/api/ml/explain-prediction")
async def explain_prediction(
    question: str = Body(...),
    response: str = Body(...),
    candidate_context: Optional[Dict] = Body(None),
    job_context: Optional[Dict] = Body(None)
):
    """Get SHAP/LIME explanation for a prediction"""
    try:
        from services.quality_prediction_service import quality_prediction_service
        from services.model_interpretability_service import model_interpretability_service
        import numpy as np
        
        # Get prediction
        prediction = await quality_prediction_service.predict_quality_score(
            question=question,
            response=response,
            candidate_context=candidate_context or {},
            job_context=job_context or {}
        )
        
        # Extract features
        features = quality_prediction_service._extract_features(
            question=question,
            response=response,
            candidate_context=candidate_context,
            job_context=job_context
        )
        
        # Convert to numpy array
        feature_array = np.array([list(features.values())])
        feature_names = list(features.keys())
        
        # Get primary model
        primary_model = quality_prediction_service.models.get('primary')
        if not primary_model:
            primary_model = quality_prediction_service.models.get('random_forest')
        
        # Generate SHAP explanation
        shap_explanation = await model_interpretability_service.explain_prediction_with_shap(
            model=primary_model,
            features=feature_array,
            feature_names=feature_names
        )
        
        return {
            "prediction": prediction,
            "shap_explanation": shap_explanation,
            "features_used": features
        }
        
    except Exception as e:
        log_error(f"Error explaining prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to explain prediction: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "fastapi_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
