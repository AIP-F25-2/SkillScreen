from fastapi import FastAPI, Request, HTTPException
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

# Import resume controller
from controllers.resume_controller import router as resume_router

# Import email service
from services.email_service import email_service

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

# Include resume router
app.include_router(resume_router)

# In-memory storage for sessions
sessions_db = {}
token_store = {}

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
        "features": ["resume_upload", "file_processing", "email_extraction"]
    })

@app.post("/api/session/create")
async def create_session(request: Request):
    """Create one or more interview sessions
    
    Accepts either:
    - Single candidate_id (backwards compatible)
    - Array of candidate_ids (for bulk creation)
    """
    try:
        body = await request.json()
        user_id = body.get("user_id")
        candidate_id = body.get("candidate_id")
        candidate_ids = body.get("candidate_ids")  # Array of candidate IDs
        
        # Validate user_id is provided
        if not user_id:
            raise HTTPException(status_code=400, detail="Missing required field: user_id")
        
        # Determine if we're creating single or multiple sessions
        if candidate_ids:
            # Bulk creation: array of candidate_ids
            if not isinstance(candidate_ids, list):
                raise HTTPException(status_code=400, detail="candidate_ids must be an array")
            
            if len(candidate_ids) == 0:
                raise HTTPException(status_code=400, detail="candidate_ids array cannot be empty")
            
            # Create sessions for each candidate
            created_sessions = []
            base_timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            
            for index, cid in enumerate(candidate_ids):
                if not cid:
                    logger.warning(f"Skipping empty candidate_id at index {index}")
                    continue
                
                # Generate unique session ID with timestamp and index
                session_id = f"session_{base_timestamp}_{index:04d}"
                
                # Create session data
                session_data = {
                    "session_id": session_id,
                    "user_id": user_id,
                    "candidate_id": cid,
                    "status": "created",
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                # Store session
                sessions_db[session_id] = session_data
                created_sessions.append(session_data)
            
            logger.info(f"Created {len(created_sessions)} sessions for user {user_id}")
            
            return create_response({
                "sessions": created_sessions,
                "total_created": len(created_sessions),
                "requested_count": len(candidate_ids)
            })
            
        elif candidate_id:
            # Single session creation (backwards compatible)
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
        else:
            raise HTTPException(status_code=400, detail="Missing required field: candidate_id or candidate_ids")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating session(s): {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred while creating session(s): {str(e)}")

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
        
        # Check if token exists
        if token not in token_store:
            logger.warning(f"Token not found: {token[:10]}...")
            raise HTTPException(status_code=404, detail="Invalid or expired token")
        
        token_data = token_store[token]
        
        # Check if token is expired
        expires_at = datetime.fromisoformat(token_data['expires_at'])
        if datetime.utcnow() > expires_at:
            logger.warning(f"Token expired: {token[:10]}...")
            raise HTTPException(status_code=410, detail="This interview link has expired")
        
        # Check if token was already used
        if token_data.get('used_at'):
            logger.warning(f"Token already used: {token[:10]}...")
            raise HTTPException(status_code=410, detail="This interview link has already been used")
        
        # Create interview record in media service
        interview_id = f"interview_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create interview data matching media service format
        interview_data = {
            "interview_id": interview_id,
            "session_id": interview_id,  # Keep for backwards compatibility
            "candidate_id": token_data['candidate_id'],
            "candidate_name": token_data['candidate_name'],
            "candidate_email": token_data['candidate_email'],
            "assigned_user": "system",  # Token-based interviews are system-assigned
            "user_id": "system",  # Add this for backwards compatibility
            "status": "in_progress",  # Interview is starting
            "token": token,  # Store token for reference
            "created_at": datetime.utcnow().isoformat(),
            "scheduled_at": datetime.utcnow().isoformat()
        }
        
        # Store interview in our local database (in production, this would call media service)
        sessions_db[interview_id] = interview_data
        
        # Mark token as used
        token_data['used_at'] = datetime.utcnow().isoformat()
        token_data['interview_id'] = interview_id  # Link token to interview
        
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
                "usedAt": token_data.get('used_at')
            }
        }
        
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
    """Send an interview invitation email to a candidate
    
    Accepts either:
    - Single invitation (backwards compatible)
    - Array of invitations (for bulk sending)
    """
    try:
        data = await request.json()
        invitations = data.get("invitations")  # Array of invitation objects
        
        # Check if bulk sending
        if invitations:
            # Bulk sending: array of invitations
            if not isinstance(invitations, list):
                raise HTTPException(status_code=400, detail="invitations must be an array")
            
            if len(invitations) == 0:
                raise HTTPException(status_code=400, detail="invitations array cannot be empty")
            
            # Process each invitation
            results = []
            errors = []
            
            for index, invitation in enumerate(invitations):
                try:
                    # Validate required fields
                    required_fields = ['candidate_email', 'candidate_name', 'candidate_id', 'session_id']
                    missing_field = None
                    for field in required_fields:
                        if field not in invitation:
                            missing_field = field
                            break
                    
                    if missing_field:
                        errors.append({
                            "index": index,
                            "error": f"Missing required field: {missing_field}",
                            "candidate_id": invitation.get('candidate_id', 'unknown')
                        })
                        continue
                    
                    # Send invitation email
                    result = email_service.send_interview_invitation(
                        candidate_email=invitation['candidate_email'],
                        candidate_name=invitation['candidate_name'],
                        candidate_id=invitation['candidate_id'],
                        session_id=invitation['session_id'],
                        recruiter_name=invitation.get('recruiter_name') or data.get('recruiter_name'),
                        company_name=invitation.get('company_name') or data.get('company_name'),
                        expires_in_hours=invitation.get('expires_in_hours') or data.get('expires_in_hours', 48)
                    )
                    
                    # Store token
                    token_store[result['token']] = {
                        'candidate_id': result['candidate_id'],
                        'candidate_name': result['candidate_name'],
                        'candidate_email': result['candidate_email'],
                        'session_id': result['session_id'],
                        'expires_at': result['expires_at'],
                        'used_at': None
                    }
                    
                    results.append({
                        "candidate_id": result['candidate_id'],
                        "candidate_email": result['candidate_email'],
                        "session_id": result['session_id'],
                        "email_id": result['email_id'],
                        "token": result['token'],
                        "expires_at": result['expires_at'],
                        "interview_link": f"{email_service.base_url}/interview-link?token={result['token']}",
                        "status": "sent"
                    })
                    
                except Exception as e:
                    logger.error(f"Error sending invitation for candidate {invitation.get('candidate_id', 'unknown')}: {str(e)}")
                    errors.append({
                        "index": index,
                        "error": str(e),
                        "candidate_id": invitation.get('candidate_id', 'unknown'),
                        "candidate_email": invitation.get('candidate_email', 'unknown')
                    })
            
            logger.info(f"Bulk email sending completed: {len(results)} sent, {len(errors)} failed")
            
            return create_response({
                "sent": results,
                "errors": errors,
                "total_requested": len(invitations),
                "total_sent": len(results),
                "total_failed": len(errors)
            })
            
        else:
            # Single invitation (backwards compatible)
            required_fields = ['candidate_email', 'candidate_name', 'candidate_id', 'session_id']
            for field in required_fields:
                if field not in data:
                    raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
            
            # Send invitation email
            result = email_service.send_interview_invitation(
                candidate_email=data['candidate_email'],
                candidate_name=data['candidate_name'],
                candidate_id=data['candidate_id'],
                session_id=data['session_id'],
                recruiter_name=data.get('recruiter_name'),
                company_name=data.get('company_name'),
                expires_in_hours=data.get('expires_in_hours', 48)
            )
            
            # Store token
            token_store[result['token']] = {
                'candidate_id': result['candidate_id'],
                'candidate_name': result['candidate_name'],
                'candidate_email': result['candidate_email'],
                'session_id': result['session_id'],
                'expires_at': result['expires_at'],
                'used_at': None
            }
            
            return create_response({
                "email_id": result['email_id'],
                "token": result['token'],
                "expires_at": result['expires_at'],
                "interview_link": f"{email_service.base_url}/interview-link?token={result['token']}"
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
