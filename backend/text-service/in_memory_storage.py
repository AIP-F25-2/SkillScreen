"""
In-memory storage for testing without database
"""
from typing import Dict, Optional, List
import uuid
from datetime import datetime, timezone

# In-memory storage
_interviews: Dict[str, Dict] = {}
_candidates: Dict[str, Dict] = {}
_jobs: Dict[str, Dict] = {}
_responses: Dict[str, List[Dict]] = {}
_questions: Dict[str, List[Dict]] = {}

def create_candidate(data: Dict) -> str:
    """Create candidate in memory"""
    candidate_id = str(uuid.uuid4())
    _candidates[candidate_id] = {
        "id": candidate_id,
        "name": data.get("name", "Unknown"),
        "email": data.get("email", "unknown@example.com"),
        "phone": data.get("phone"),
        "skills": data.get("skills", []),
        "experience_years": data.get("experience_years", 0.0),
        "education": data.get("education", ""),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    return candidate_id

def get_candidate(candidate_id: str) -> Optional[Dict]:
    """Get candidate from memory"""
    return _candidates.get(candidate_id)

def create_job(data: Dict) -> str:
    """Create job in memory"""
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "id": job_id,
        "title": data.get("title", ""),
        "company": data.get("company", ""),
        "description": data.get("description", ""),
        "required_skills": data.get("required_skills", []),
        "experience_level": data.get("experience_level", "Mid-level"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    return job_id

def get_job(job_id: str) -> Optional[Dict]:
    """Get job from memory"""
    return _jobs.get(job_id)

def create_interview(data: Dict) -> str:
    """Create interview in memory"""
    interview_id = str(uuid.uuid4())
    session_id = data.get("session_id", f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}")
    
    _interviews[session_id] = {
        "id": interview_id,
        "session_id": session_id,
        "candidate_id": data.get("candidate_id"),
        "job_id": data.get("job_id"),
        "status": "in_progress",
        "current_question_index": 0,
        "total_questions_asked": 0,
        "total_responses_received": 0,
        "max_questions": data.get("max_questions", 15),
        "settings": {
            "interview_type": data.get("interview_type", "mixed"),
            "difficulty": data.get("difficulty", "medium"),
            "max_questions": data.get("max_questions", 15),
            "target_duration_minutes": data.get("target_duration_minutes", 12),
            "session_id": session_id,
            "candidate_record_id": data.get("candidate_id")
        },
        "started_at": datetime.now(timezone.utc).isoformat(),
        "initial_question": data.get("initial_question", "Tell me about yourself.")
    }
    _questions[session_id] = []
    _responses[session_id] = []
    return session_id

def get_interview_by_session(session_id: str) -> Optional[Dict]:
    """Get interview by session_id"""
    return _interviews.get(session_id)

def add_question(session_id: str, question: Dict):
    """Add question to interview"""
    if session_id not in _questions:
        _questions[session_id] = []
    _questions[session_id].append(question)

def add_response(session_id: str, response: Dict):
    """Add response to interview"""
    if session_id not in _responses:
        _responses[session_id] = []
    _responses[session_id].append(response)
    
    # Update interview progress
    if session_id in _interviews:
        _interviews[session_id]["total_responses_received"] = len(_responses[session_id])
        _interviews[session_id]["current_question_index"] = len(_responses[session_id])

def update_interview(session_id: str, updates: Dict):
    """Update interview data"""
    if session_id in _interviews:
        _interviews[session_id].update(updates)

def get_questions(session_id: str) -> List[Dict]:
    """Get all questions for interview"""
    return _questions.get(session_id, [])

def get_responses(session_id: str) -> List[Dict]:
    """Get all responses for interview"""
    return _responses.get(session_id, [])

