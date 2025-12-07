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
from controllers.resume_controller import router as resume_router, set_email_service
from controllers.job_position_controller import router as job_position_controller

# Import services
from services.email_service import EmailService

# Import repositories and models
from repository.interview_repository import InterviewRepository
from repository.interview_token_repository import InterviewTokenRepository
from models.interview import Interview
from models.interview_token import InterviewToken

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
token_store = {}

# Initialize email service with token_store reference
email_service = EmailService(token_store=token_store)

# Inject email_service into resume_controller so it has the token_store reference
set_email_service(email_service)

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

    return create_response(
        data=sessions_db[session_id],
        success=True
    )

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
            for interview in interviews:
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
                        logger.warning(f"Could not fetch candidate info for interview {interview.id}: {e}")
                
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

@app.post("/api/token/validate")
async def validate_token(request: Request):
    """Validate an interview access token and create interview record"""
    try:
        data = await request.json()
        token = data.get('token')

        if not token:
            raise HTTPException(status_code=400, detail="Token is required")

        # First try to validate from database
        interview_token = InterviewTokenRepository.validate_token(token)

        if not interview_token:
            # Fallback to in-memory token_store if database lookup fails
            if token not in token_store:
                logger.warning(f"Token not found in database or memory: {token[:10]}...")
                raise HTTPException(status_code=404, detail="Invalid or expired token")

            # Use in-memory token data
            token_data = token_store[token]
            candidate_id = token_data['candidate_id']
            candidate_name = token_data['candidate_name']
            candidate_email = token_data['candidate_email']
            expires_at_str = token_data['expires_at']
        else:
            # Use database token data
            candidate_id = str(interview_token.candidate_id)
            candidate_name = interview_token.candidate_name
            candidate_email = interview_token.candidate_email
            expires_at_str = interview_token.expires_at.isoformat()
            token_data = {
                'candidate_id': candidate_id,
                'candidate_name': candidate_name,
                'candidate_email': candidate_email,
                'expires_at': expires_at_str
            }

        candidate_id = token_data['candidate_id']
        
        # Try to find existing interview for this candidate (created when invitation was sent)
        session = DBFactory.get_session()
        interview_id = None
        try:
            interview_repo = InterviewRepository(session)
            
            # Look for ANY scheduled interview with this candidate_id
            interviews = interview_repo.get_interviews_by_candidate(candidate_id)
            scheduled_interview = None
            for inv in interviews:
                if inv.status == 'scheduled':
                    scheduled_interview = inv
                    break

            if scheduled_interview:
                # Update existing interview to in_progress
                interview_id = str(scheduled_interview.id)
                interview_repo.update_interview_status(interview_id, 'in_progress')
                session.commit()
                logger.info(f"✅ Updated existing interview {interview_id} to in_progress for candidate {candidate_id}")
            else:
                # No scheduled interview found - create new one as fallback
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

        # Mark token as used in database
        try:
            InterviewTokenRepository.mark_token_used(token)
            logger.info(f"Token marked as used in database: {token[:10]}...")
        except Exception as e:
            logger.warning(f"Failed to mark token as used in database: {str(e)}")
            # Fallback: mark in memory
            token_data['used_at'] = datetime.utcnow().isoformat()

        logger.info(f"Token validated and interview created: {token[:10]}... -> {interview_id} for {token_data['candidate_email']}")

        # Return camelCase format that frontend expects (InterviewToken interface)
        expires_at = token_data.get('expires_at', expires_at_str)
        return create_response(
            data={
                "token": token,
                "candidateId": token_data['candidate_id'],
                "candidateName": token_data['candidate_name'],
                "candidateEmail": token_data['candidate_email'],
                "sessionId": interview_id,
                "interviewId": interview_id,
                "expiresAt": expires_at
            },
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while validating the token")


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
        
        # Store token data
        token_store[token] = {
            'candidate_id': data['candidate_id'],
            'candidate_name': data['candidate_name'],
            'candidate_email': data['candidate_email'],
            'session_id': data['session_id'],
            'expires_at': data['expires_at'],
            'used_at': None
        }
        
        logger.info(f"Token stored: {token[:10]}... for {data['candidate_email']}")
        
        return create_response({
            "message": "Token stored successfully"
        })
        
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
                # Try to find by email - we need organization_id for this, but we can try common org
                # Or we can search across all orgs (less ideal but works for now)
                # Actually, let's use the hardcoded org ID for now
                hardcoded_org_id = "e5d2d50b-6c07-43cd-8a78-ffd7b5b377bb"
                candidate = candidate_repo.get_candidate_by_email(hardcoded_org_id, candidate_email)
                
                if candidate:
                    actual_candidate_id = str(candidate.id)
                    logger.info(f"Found candidate by email: {actual_candidate_id}")
            
            if not candidate:
                logger.warning(f"Candidate {candidate_id} (email: {candidate_email}) not found in database, creating interview without organization_id")
                organization_id = None
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
            expires_in_hours=data.get('expires_in_hours', 48)
        )
        
        # Store token with actual candidate ID
        token_store[result['token']] = {
            'candidate_id': actual_candidate_id,  # Use the real database candidate ID
            'candidate_name': result['candidate_name'],
            'candidate_email': result['candidate_email'],
            'session_id': result['session_id'],
            'expires_at': result['expires_at'],
            'used_at': None
        }
        
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
