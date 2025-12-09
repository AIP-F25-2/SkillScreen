from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
import uuid
import logging
import os
import sys
from dotenv import load_dotenv

# Add common-service to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common-service'))

# Import local database setup
from db import DBFactory

# Import controllers
from controllers.resume_controller import router as resume_router
from controllers.job_position_controller import router as job_position_controller

# Import services
from services.email_service import EmailService

# Import repositories and models
from repository.interview_repository import InterviewRepository
from models.interview import Interview

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database connection
try:
    DBFactory.init()
    logger.info("Database connection initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")

app = FastAPI(title="Interview Service")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(resume_router)
app.include_router(job_position_controller)

# In-memory storage for sessions
sessions_db = {}

# Initialize email service
email_service = EmailService()

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
        "service": "interview-service",
        "endpoints": {
            "resume_upload": "/resumes/upload",
            "job_positions": "/job-positions",
            "health": "/health"
        }
    })

@app.get("/health")
def health():
    """Detailed health check"""
    return create_response({
        "service": "interview-service",
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "features": ["resume_upload", "file_processing", "email_extraction", "job_positions_crud"]
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

# ========================================
# Interview Management Endpoints
# ========================================

@app.get("/api/interviews")
async def get_all_interviews(organization_id: str = None, limit: int = 100, offset: int = 0):
    """Get all interviews from the database"""
    try:
        session = DBFactory.get_session()
        try:
            interview_repo = InterviewRepository(session)
            interviews = interview_repo.get_all_interviews(organization_id=organization_id, limit=limit, offset=offset)
            
            # Convert to dict format with candidate info if available
            interviews_data = []
            logger.info(f"Fetching interviews for organization_id: {organization_id}")
            for interview in interviews:
                interview_dict = interview.to_dict()
                logger.info(f"Found interview: {interview.id}, org_id: {interview.organization_id}")
                
                # Try to get candidate info if candidate_id exists
                if interview.candidate_id:
                    try:
                        from repository.candidate_repository import CandidateRepository
                        candidate_repo = CandidateRepository(session)
                        candidate = candidate_repo.get_candidate_by_id(str(interview.candidate_id))
                        if candidate:
                            interview_dict['candidate_name'] = candidate.full_name
                            interview_dict['candidate_email'] = candidate.email
                    except Exception as e:
                        logger.warning(f"Could not fetch candidate info for interview {interview.id}: {e}")

                # Try to get job position info if job_position_id exists
                if interview.job_position_id:
                    try:
                        from repository.job_position_repository import JobPositionRepository
                        job_repo = JobPositionRepository(session)
                        job_pos = job_repo.get_job_position_by_id(str(interview.job_position_id))
                        if job_pos:
                            interview_dict['job_position_title'] = job_pos.title
                    except Exception as e:
                        logger.warning(f"Could not fetch job position info for interview {interview.id}: {e}")
                
                interviews_data.append(interview_dict)
            
            return create_response({
                "interviews": interviews_data,
                "count": len(interviews_data)
            })
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Error fetching interviews: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch interviews: {str(e)}")

@app.get("/api/interviews/{interview_id}")
async def get_interview(interview_id: str):
    """Get a specific interview by ID"""
    try:
        session = DBFactory.get_session()
        try:
            interview_repo = InterviewRepository(session)
            interview = interview_repo.get_interview_by_id(interview_id)
            
            if not interview:
                raise HTTPException(status_code=404, detail="Interview not found")
            
            interview_dict = interview.to_dict()
            
            # Try to get candidate info if candidate_id exists
            if interview.candidate_id:
                try:
                    from repository.candidate_repository import CandidateRepository
                    candidate_repo = CandidateRepository(session)
                    candidate = candidate_repo.get_candidate_by_id(str(interview.candidate_id))
                    if candidate:
                        interview_dict['candidate_name'] = candidate.full_name
                        interview_dict['candidate_email'] = candidate.email
                except Exception as e:
                    logger.warning(f"Could not fetch candidate info: {e}")

            # Try to get job position info if job_position_id exists
            if interview.job_position_id:
                try:
                    from repository.job_position_repository import JobPositionRepository
                    job_repo = JobPositionRepository(session)
                    job_pos = job_repo.get_job_position_by_id(str(interview.job_position_id))
                    if job_pos:
                        interview_dict['job_position_title'] = job_pos.title
                except Exception as e:
                    logger.warning(f"Could not fetch job position info: {e}")
            
            return create_response(interview_dict)
        finally:
            session.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching interview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch interview: {str(e)}")

# ========================================
# Token Management Endpoints
# ========================================

from services.token_service import token_service

@app.post("/api/token/validate")
async def validate_token(request: Request):
    """Validate an interview access token and create interview record"""
    try:
        data = await request.json()
        token = data.get('token')
        
        # Use TokenService for validation
        validation_result = token_service.validate_token(token)
        
        if not validation_result['valid']:
            error_msg = validation_result['error']
            status_code = 400 if "required" in error_msg else (404 if "found" in error_msg else 410)
            raise HTTPException(status_code=status_code, detail=error_msg)
        
        token_data = validation_result['data']
        candidate_id = token_data['candidate_id']
        
        # Try to find existing interview for this candidate (created when invitation was sent)
        session = DBFactory.get_session()
        interview_id = None
        try:
            interview_repo = InterviewRepository(session)
            
            # Look for scheduled interview with this candidate_id
            interviews = interview_repo.get_interviews_by_candidate(candidate_id)
            scheduled_interview = None
            for inv in interviews:
                if inv.status == 'scheduled' and inv.settings and inv.settings.get('token') == token:
                    scheduled_interview = inv
                    break
            
            if scheduled_interview:
                # Update existing interview to in_progress
                interview_id = str(scheduled_interview.id)
                interview_repo.update_interview_status(interview_id, 'in_progress')
                session.commit()
                logger.info(f"Updated existing interview {interview_id} to in_progress for candidate {candidate_id}")
            else:
                # Create new interview record if not found
                # Get candidate info to get organization_id
                from repository.candidate_repository import CandidateRepository
                candidate_repo = CandidateRepository(session)
                candidate = candidate_repo.get_candidate_by_id(candidate_id)
                
                organization_id = str(candidate.organization_id) if candidate and candidate.organization_id else None
                
                interview_id = str(uuid.uuid4())
                interview_data = {
                    'organization_id': organization_id,
                    'candidate_id': candidate_id,
                    'status': 'in_progress',
                    'scheduled_at': datetime.now(timezone.utc).isoformat(),
                    'started_at': datetime.now(timezone.utc).isoformat(),
                    'settings': {
                        'token': token,
                        'expires_at': token_data['expires_at']
                    }
                }
                
                interview = interview_repo.create_interview(interview_data)
                session.commit()
                interview_id = str(interview.id)
                logger.info(f"Created new interview {interview_id} in database for candidate {candidate_id}")
                
        except Exception as e:
            logger.error(f"Error creating/updating interview in database: {str(e)}")
            session.rollback()
            # Fallback to in-memory storage if database fails
            interview_id = interview_id or f"interview_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            interview_data = {
                "interview_id": interview_id,
                "session_id": interview_id,
                "candidate_id": candidate_id,
                "candidate_name": token_data['candidate_name'],
                "candidate_email": token_data['candidate_email'],
                "status": "in_progress",
                "token": token,
                "created_at": datetime.utcnow().isoformat(),
                "scheduled_at": datetime.utcnow().isoformat()
            }
            sessions_db[interview_id] = interview_data
        finally:
            session.close()
        
        # Mark token as used
        token_service.mark_token_used(token)
        
        # Update token data with interview_id for future reference
        token_data['interview_id'] = interview_id
        # We need to update the store with this new info
        token_service.store_token(token, token_data)
        
        logger.info(f"Token validated and interview created: {token[:10]}... -> {interview_id} for {token_data['candidate_email']}")
        
        return {
            "valid": True,
            "data": {
                "token": token,
                "candidateId": token_data['candidate_id'],
                "candidateName": token_data['candidate_name'],
                "candidateEmail": token_data['candidate_email'],
                "sessionId": interview_id,  # Use interview_id as session_id
                "interviewId": interview_id,  # Add explicit interview_id
                "expiresAt": token_data['expires_at'],
                "usedAt": datetime.utcnow().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An error occurred while validating the token: {str(e)}")


@app.post("/api/token/store")
async def store_token(request: Request):
    """Store a new interview token"""
    try:
        data = await request.json()
        
        required_fields = ['token', 'candidate_id', 'candidate_name', 'candidate_email', 'session_id', 'expires_at']
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        token = data['token']
        
        if token_service.store_token(token, data):
            return create_response({
                "message": "Token stored successfully"
            })
        else:
            raise HTTPException(status_code=500, detail="Failed to store token")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token storage error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while storing the token")

# ========================================
# Email Endpoints
# ========================================

@app.post("/api/email/send-invitation")
async def send_invitation(request: Request):
    """Send an interview invitation email to a candidate and create interview record in database"""
    try:
        data = await request.json()
        
        # Validate required fields
        required_fields = ['candidate_email', 'candidate_name', 'candidate_id', 'session_id']
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        candidate_id = data['candidate_id']
        candidate_email = data['candidate_email']
        
        # Get candidate info from database to get organization_id and real candidate_id
        session = DBFactory.get_session()
        actual_candidate_id = candidate_id
        organization_id = None
        try:
            from repository.candidate_repository import CandidateRepository
            candidate_repo = CandidateRepository(session)
            
            # Try to find by ID first
            candidate = candidate_repo.get_candidate_by_id(candidate_id)
            
            # If not found and candidate_id looks like a temp ID, try to find by email
            if not candidate and (candidate_id.startswith('temp_') or len(candidate_id) < 36):
                logger.info(f"Candidate ID {candidate_id} appears to be temporary, looking up by email: {candidate_email}")
                
                # Use organization_id from request if available
                req_org_id = data.get('organization_id')
                
                if req_org_id:
                    candidate = candidate_repo.get_candidate_by_email(req_org_id, candidate_email)
                else:
                    logger.warning(f"No organization_id provided for email lookup of {candidate_email}")
                    pass
                
                if candidate:
                    actual_candidate_id = str(candidate.id)
                    logger.info(f"Found candidate by email: {actual_candidate_id}")
            
            if not candidate:
                logger.warning(f"Candidate {candidate_id} (email: {candidate_email}) not found in database, creating interview without organization_id")
                organization_id = data.get('organization_id') # Use request org ID if candidate not found
            else:
                organization_id = str(candidate.organization_id)
                actual_candidate_id = str(candidate.id)  # Use the real database ID
                logger.info(f"Found candidate {actual_candidate_id} with organization {organization_id}")
        except Exception as e:
            logger.error(f"Error fetching candidate from database: {str(e)}")
            organization_id = None
        finally:
            session.close()
        
        # Send invitation email
        result = email_service.send_interview_invitation(
            candidate_email=data['candidate_email'],
            candidate_name=data['candidate_name'],
            candidate_id=candidate_id,
            session_id=data['session_id'],
            recruiter_name=data.get('recruiter_name'),
            company_name=data.get('company_name'),
            job_title=data.get('job_title'),
            expires_in_hours=data.get('expires_in_hours', 48)
        )
        
        # Store token with actual candidate ID using TokenService
        token_data = {
            'candidate_id': actual_candidate_id,
            'candidate_name': result['candidate_name'],
            'candidate_email': result['candidate_email'],
            'session_id': result['session_id'],
            'expires_at': result['expires_at'],
            'used_at': None
        }
        token_service.store_token(result['token'], token_data)
        
        # Create interview record in database
        interview_id = None
        interview_session = DBFactory.get_session()
        try:
            # Only create interview if we have valid organization_id and candidate_id (UUID format)
            if organization_id and actual_candidate_id and len(actual_candidate_id) == 36 and actual_candidate_id.count('-') == 4:
                interview_repo = InterviewRepository(interview_session)
                
                interview_data = {
                    'organization_id': organization_id,
                    'candidate_id': actual_candidate_id,  # Use the real database candidate ID
                    'status': 'scheduled',
                    'scheduled_at': datetime.now(timezone.utc).isoformat(),
                    # Ensure required fields for DB constraints are always populated
                    'mode': data.get('mode', 'chat'),  # Default mode to 'chat' if not provided
                    'settings': {
                        'token': result['token'],
                        'expires_at': result['expires_at'],
                        'recruiter_name': data.get('recruiter_name'),
                        'company_name': data.get('company_name'),
                        'original_candidate_id': candidate_id  # Store original in case it was temp
                    }
                }
                
                # Add optional fields if provided
                if data.get('job_position_id'):
                    interview_data['job_position_id'] = data['job_position_id']
                if data.get('interviewer_id'):
                    interview_data['interviewer_id'] = data['interviewer_id']
                # Use provided template_id or default to dummy template_id
                interview_data['template_id'] = data.get('template_id', '1ef03eb1-4ba0-4e42-a27d-5b5a868640f4')
                
                interview = interview_repo.create_interview(interview_data)
                interview_session.commit()
                interview_id = str(interview.id)
                
                logger.info(f"Created interview record in database: {interview_id} for candidate {actual_candidate_id}")
            else:
                logger.warning(f"Skipping interview creation - missing valid organization_id or candidate_id. org_id={organization_id}, candidate_id={actual_candidate_id}")
                interview_id = data.get('interview_id') or result.get('session_id') or str(uuid.uuid4())
            
        except Exception as e:
            logger.error(f"Failed to create interview record in database: {str(e)}", exc_info=True)
            interview_session.rollback()
            # Don't fail the request if database save fails, email was already sent
            interview_id = interview_id or data.get('interview_id') or result.get('session_id') or str(uuid.uuid4())
        finally:
            interview_session.close()
        
        return create_response({
            "email_id": result['email_id'],
            "token": result['token'],
            "expires_at": result['expires_at'],
            "interview_link": f"{email_service.base_url}/interview-link?token={result['token']}",
            "interview_id": interview_id
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send invitation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/email/send-completion-notification")
async def send_completion_notification(request: Request):
    """Send interview completion notification to recruiter"""
    try:
        data = await request.json()
        
        # Validate required fields
        required_fields = ['recruiter_email', 'recruiter_name', 'candidate_name', 'interview_id', 'session_id']
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Send completion notification
        result = email_service.send_interview_completion_notification(
            recruiter_email=data['recruiter_email'],
            recruiter_name=data['recruiter_name'],
            candidate_name=data['candidate_name'],
            interview_id=data['interview_id'],
            session_id=data['session_id']
        )
        
        return create_response({
            "email_id": result['email_id']
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send completion notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
