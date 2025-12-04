"""
Simplified FastAPI application for SkillScreen testing
This version works without PostgreSQL and complex dependencies
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import uuid
from datetime import datetime
import os
import asyncio
import aiofiles

# Import code execution service
try:
    from services.code_execution_service import code_execution_service
    CODE_EXECUTION_AVAILABLE = True
except ImportError:
    CODE_EXECUTION_AVAILABLE = False

# Import LLM service
try:
    from services.llm_service import llm_service
    LLM_SERVICE_AVAILABLE = True
except ImportError:
    LLM_SERVICE_AVAILABLE = False

# Import configuration loader
from utils.config_loader import get_config

# Set up environment variables for API keys from config
os.environ.setdefault('GEMINI_API_KEY', get_config('GEMINI_API_KEY', ''))
os.environ.setdefault('WOLFRAM_APP_ID', get_config('WOLFRAM_APP_ID', ''))
os.environ.setdefault('SERPAPI_KEY', get_config('SERPAPI_KEY', ''))

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from utils.resume_parser import resume_parser

# Simple models for testing
class CandidateCreate(BaseModel):
    name: str
    email: str
    resume_text: Optional[str] = None
    experience_years: Optional[int] = 0
    skills: Optional[List[str]] = []

class JobCreate(BaseModel):
    title: str
    company: str
    description: str
    required_skills: Optional[List[str]] = []
    experience_level: Optional[str] = "mid"

class InterviewStart(BaseModel):
    candidate_id: str
    job_id: str

class InterviewResponse(BaseModel):
    response_text: str

class InterviewSummaryResponse(BaseModel):
    session_id: str
    candidate_name: str
    job_title: str
    total_questions: int
    total_responses: int
    overall_score: float
    recommendation: str
    summary: str
    strengths: List[str]
    areas_for_improvement: List[str]
    detailed_assessment: Dict[str, Any]
    violations_analysis: Optional[Dict[str, Any]] = None

# Initialize FastAPI app
app = FastAPI(
    title="SkillScreen API",
    description="AI-powered interview platform for automated candidate screening",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for testing
candidates_db = {}
jobs_db = {}
interviews_db = {}
sessions_db = {}

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts using Jaccard similarity"""
    if not text1 or not text2:
        return 0.0
    
    # Normalize texts
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0

def generate_funny_analysis(violations):
    """Generate humorous analysis of interview violations"""
    if not violations:
        return {
            "title": "🎉 Clean Interview!",
            "message": "Congratulations! You provided original, authentic responses throughout the interview.",
            "emoji": "🌟",
            "fun_fact": "You're the kind of candidate who brings their own personality to interviews!"
        }
    
    duplicate_count = len([v for v in violations if v["type"] == "duplicate"])
    ai_count = len([v for v in violations if v["type"] == "ai_generated"])
    
    # Funny messages based on violation patterns
    funny_messages = {
        "duplicate_heavy": [
            "🔄 'Once a cheater, always a cheater' - but hey, at least you're consistent!",
            "📝 Copy-paste master! You could teach a class on efficiency... in the wrong field.",
            "🔄 'Variety is the spice of life' - someone forgot to tell you that!",
            "📋 You're like a broken record, but with better sound quality!",
            "🔄 'Originality is overrated' - your motto, apparently!"
        ],
        "ai_heavy": [
            "🤖 ChatGPT called, it wants its responses back!",
            "🧠 'I am not a robot' - the CAPTCHA disagrees!",
            "🤖 You're so AI-like, even robots are taking notes!",
            "🧠 'Human creativity' - that's a new concept for you!",
            "🤖 You're the reason why AI detection software exists!"
        ],
        "mixed": [
            "🎭 'Jack of all trades, master of copy-paste' - that's you!",
            "🔄🤖 The perfect storm: repetitive AND robotic!",
            "📝🤖 You're like a broken AI that only knows one response!",
            "🔄🤖 'Consistency in chaos' - your interview philosophy!",
            "📋🤖 You're the reason why interviewers have trust issues!"
        ]
    }
    
    # Determine the pattern
    if duplicate_count > ai_count and duplicate_count >= 3:
        pattern = "duplicate_heavy"
    elif ai_count > duplicate_count and ai_count >= 3:
        pattern = "ai_heavy"
    else:
        pattern = "mixed"
    
    # Use deterministic selection based on current time to avoid security warnings
    # This provides variety without using cryptographically-sensitive random functions
    import time
    current_time = int(time.time() * 1000)  # milliseconds for better distribution
    message_index = current_time % len(funny_messages[pattern])
    funny_message = funny_messages[pattern][message_index]
    
    # Generate title and emoji
    if duplicate_count >= 3 and ai_count >= 2:
        title = "🎭 The Ultimate Copy-Paste Artist"
        emoji = "🎭"
    elif duplicate_count >= 3:
        title = "🔄 The Repetition Champion"
        emoji = "🔄"
    elif ai_count >= 3:
        title = "🤖 The AI Whisperer"
        emoji = "🤖"
    else:
        title = "⚠️ The Slightly Suspicious Candidate"
        emoji = "⚠️"
    
    # Generate fun facts
    fun_facts = [
        "💡 Pro tip: Try using your own words next time!",
        "🎯 Fun fact: Interviewers can tell when you're not being yourself!",
        "📚 Did you know? Original responses score better than copied ones!",
        "🎪 You're like a magician - always pulling the same tricks!",
        "🎨 'Be yourself' - the advice you clearly ignored!",
        "🎪 You're the reason why 'authenticity' is a buzzword in HR!",
        "🎯 Fun fact: Robots have more personality than your responses!",
        "📝 You're proof that copy-paste is an art form... just not a good one!"
    ]
    
    # Use deterministic selection based on current time to avoid security warnings
    # This provides variety without using cryptographically-sensitive random functions
    current_time = int(time.time() * 1000)  # milliseconds for better distribution
    fact_index = current_time % len(fun_facts)
    fun_fact = fun_facts[fact_index]
    
    return {
        "title": title,
        "message": funny_message,
        "emoji": emoji,
        "fun_fact": fun_fact,
        "violation_summary": {
            "duplicate_responses": duplicate_count,
            "ai_generated_responses": ai_count,
            "total_violations": len(violations)
        }
    }

# Counter for IDs
candidate_counter = 0
job_counter = 0
interview_counter = 0

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "SkillScreen API is running!",
        "version": "2.0.0",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "candidates": "/candidates",
            "jobs": "/jobs", 
            "interviews": "/interviews",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "in-memory",
        "services": ["interview", "nlp", "anti-cheating", "code-execution"]
    }

# Code execution endpoints
@app.post("/api/code/execute")
async def execute_code(request: Dict[str, Any]):
    """Execute code in sandboxed environment"""
    if not CODE_EXECUTION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Code execution service not available")
    
    try:
        code = request.get("code", "")
        language = request.get("language", "python")
        test_cases = request.get("test_cases", [])
        timeout = request.get("timeout", 10)
        
        if not code.strip():
            raise HTTPException(status_code=400, detail="Code cannot be empty")
        
        result = await code_execution_service.execute_code(
            code=code,
            language=language,
            test_cases=test_cases,
            timeout=timeout
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code execution failed: {str(e)}")

@app.get("/api/code/languages")
async def get_supported_languages():
    """Get list of supported programming languages"""
    if not CODE_EXECUTION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Code execution service not available")
    
    return {
        "languages": code_execution_service.get_supported_languages(),
        "available": CODE_EXECUTION_AVAILABLE
    }

@app.post("/api/code/question")
async def create_technical_question(request: Dict[str, Any]):
    """Create a technical coding question"""
    if not CODE_EXECUTION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Code execution service not available")
    
    try:
        language = request.get("language", "python")
        difficulty = request.get("difficulty", "medium")
        topic = request.get("topic", "general")
        
        question = code_execution_service.create_technical_question(
            language=language,
            difficulty=difficulty,
            topic=topic
        )
        
        return question
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create question: {str(e)}")

@app.get("/api/code/result/{execution_id}")
async def get_execution_result(execution_id: str):
    """Get execution result by ID"""
    if not CODE_EXECUTION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Code execution service not available")
    
    result = code_execution_service.get_execution_result(execution_id)
    if not result:
        raise HTTPException(status_code=404, detail="Execution result not found")
    
    return result

# Candidate endpoints
@app.post("/candidates", response_model=Dict[str, str])
async def create_candidate(candidate: CandidateCreate):
    """Create a new candidate"""
    global candidate_counter
    candidate_counter += 1
    candidate_id = f"candidate_{candidate_counter}"
    
    candidates_db[candidate_id] = {
        "id": candidate_id,
        "name": candidate.name,
        "email": candidate.email,
        "resume_text": candidate.resume_text,
        "experience_years": candidate.experience_years,
        "skills": candidate.skills,
        "created_at": datetime.now().isoformat()
    }
    
    return {"candidate_id": candidate_id, "message": "Candidate created successfully"}

@app.get("/candidates")
async def list_candidates():
    """List all candidates"""
    return {"candidates": list(candidates_db.values()), "total": len(candidates_db)}

@app.get("/candidates/{candidate_id}")
async def get_candidate(candidate_id: str):
    """Get candidate by ID"""
    if candidate_id not in candidates_db:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidates_db[candidate_id]

# Job endpoints
@app.post("/jobs", response_model=Dict[str, str])
async def create_job(job: JobCreate):
    """Create a new job"""
    global job_counter
    job_counter += 1
    job_id = f"job_{job_counter}"
    
    jobs_db[job_id] = {
        "id": job_id,
        "title": job.title,
        "company": job.company,
        "description": job.description,
        "required_skills": job.required_skills,
        "experience_level": job.experience_level,
        "created_at": datetime.now().isoformat()
    }
    
    return {"job_id": job_id, "message": "Job created successfully"}

@app.get("/jobs")
async def list_jobs():
    """List all jobs"""
    return {"jobs": list(jobs_db.values()), "total": len(jobs_db)}

@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """Get job by ID"""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs_db[job_id]

# Interview endpoints
@app.post("/interviews/start", response_model=Dict[str, Any])
async def start_interview(request: InterviewStart):
    """Start a new interview session"""
    global interview_counter
    interview_counter += 1
    session_id = f"session_{interview_counter}"
    
    # Validate candidate and job exist
    if request.candidate_id not in candidates_db:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if request.job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    candidate = candidates_db[request.candidate_id]
    job = jobs_db[request.job_id]
    
    # Create interview session
    sessions_db[session_id] = {
        "session_id": session_id,
        "candidate_id": request.candidate_id,
        "job_id": request.job_id,
        "candidate_name": candidate["name"],
        "job_title": job["title"],
        "status": "active",
        "start_time": datetime.now().isoformat(),
        "questions_asked": 0,
        "responses_received": 0,
        "current_question": "Tell me about yourself and your experience with this role.",
        "question_history": [],
        "response_history": [],
        "total_score": 0.0,
        "candidate_name_from_intro": None  # Will be extracted from first response
    }
    
    return {
        "session_id": session_id,
        "message": f"Interview started for {candidate['name']}",
        "first_question": "Tell me about yourself and your experience with this role.",
        "status": "started"
    }

@app.get("/interviews/{session_id}")
async def get_interview(session_id: str):
    """Get interview session details"""
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Interview session not found")
    return sessions_db[session_id]

@app.post("/interviews/{session_id}/respond")
async def submit_response(session_id: str, response: InterviewResponse):
    """Submit candidate response"""
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    session = sessions_db[session_id]
    
    if session["status"] != "active":
        raise HTTPException(status_code=400, detail="Interview session is not active")
    
    # Add response to history
    session["response_history"].append(response.response_text)
    session["responses_received"] += 1
    
    # Extract candidate name from first response (introduction)
    if session["responses_received"] == 1 and not session.get("candidate_name_from_intro"):
        intro_text = response.response_text.lower()
        # Look for common introduction patterns
        name_patterns = [
            r"i am ([a-zA-Z\s]+)",
            r"my name is ([a-zA-Z\s]+)",
            r"i'm ([a-zA-Z\s]+)",
            r"this is ([a-zA-Z\s]+)"
        ]
        
        for pattern in name_patterns:
            import re
            match = re.search(pattern, intro_text)
            if match:
                extracted_name = match.group(1).strip().title()
                # Clean up the name (remove extra words)
                if len(extracted_name.split()) <= 3 and not any(word in extracted_name.lower() for word in ['an', 'a', 'the', 'and', 'with']):
                    session["candidate_name_from_intro"] = extracted_name
                    break
    
    # Enhanced scoring with anti-cheating detection
    response_text = response.response_text
    
    # Basic scoring logic
    base_score = min(8.0, max(3.0, len(response_text) / 20.0))
    
    # Anti-cheating analysis (simplified version)
    is_duplicate = False
    is_ai_generated = False
    warnings = []
    
    # Check for duplicate responses (improved logic)
    similarity = 0.0  # Initialize similarity variable
    if session["responses_received"] > 0:
        previous_responses = session.get("response_history", [])
        similarity_count = 0
        
        for prev_response in previous_responses:
            # Ensure prev_response is a string, not a dict
            if isinstance(prev_response, dict):
                prev_text = prev_response.get("response_text", "")
            else:
                prev_text = str(prev_response)
            
            similarity = calculate_similarity(response_text, prev_text)
            if similarity > 0.8:  # 80% similarity threshold
                similarity_count += 1
        
        # Only flag as duplicate if similar to 2 or more previous responses
        # This prevents false positives when responses are naturally similar
        if similarity_count >= 2:
            is_duplicate = True
    
    # Check for AI-generated content (enhanced detection)
    ai_indicators = [
        'in conclusion', 'furthermore', 'moreover', 'additionally',
        'it is important to note', 'it should be noted', 'it is worth mentioning',
        'as previously mentioned', 'as stated earlier', 'to summarize',
        'in summary', 'it is crucial to', 'it is essential to',
        'utilize', 'facilitate', 'implement', 'optimize', 'leverage',
        'i\'m currently pursuing', 'my key strengths are', 'i\'m drawn to this role',
        'one of the most challenging', 'my approach is', 'i\'m most comfortable',
        'i start by', 'i ensure', 'the biggest trends', 'i stay adaptable',
        'which helps me perform well', 'i\'m also good at', 'i\'m passionate about',
        'this aligns perfectly', 'i believe that', 'i\'m excited about',
        'i would approach this', 'i have experience with', 'i\'m proficient in',
        'i can contribute to', 'i\'m looking forward to', 'i\'m committed to',
        'i have a strong foundation', 'i\'m confident that', 'i bring to the table'
    ]
    
    response_lower = response_text.lower()
    ai_count = sum(1 for indicator in ai_indicators if indicator in response_lower)
    
    # Also check for perfect structure (bullet points, numbered lists)
    has_perfect_structure = (
        response_text.count('**') >= 4 or  # Multiple bold formatting
        response_text.count('•') >= 3 or   # Multiple bullet points
        response_text.count('1.') >= 2 or  # Numbered lists
        (len(response_text.split('\n')) >= 3 and response_text.count(':') >= 2)  # Structured format
    )
    
    # Flag as AI-generated if any indicators OR perfect structure (more sensitive)
    if ai_count >= 1 or has_perfect_structure:
        is_ai_generated = True
    
    # Apply penalties
    if is_duplicate:
        base_score *= 0.3  # 70% penalty for duplicates
        warnings.append("⚠️ WARNING: Duplicate response detected. Please provide unique answers.")
    
    if is_ai_generated:
        base_score *= 0.2  # 80% penalty for AI-generated content
        warnings.append("⚠️ WARNING: AI-generated content detected. Please provide original responses.")
    
    # Check for termination conditions
    duplicate_count = session.get("duplicate_count", 0)
    ai_count = session.get("ai_generated_count", 0)
    
    if is_duplicate:
        duplicate_count += 1
        session["duplicate_count"] = duplicate_count
    
    if is_ai_generated:
        ai_count += 1
        session["ai_generated_count"] = ai_count
    
    # Track violations for end-of-interview analysis (no termination)
    violations = session.get("violations", [])
    
    if is_duplicate:
        violations.append({
            "type": "duplicate",
            "question": session.get("questions_asked", 0),
            "response": response_text[:100] + "..." if len(response_text) > 100 else response_text,
            "similarity": similarity if 'similarity' in locals() else 0.0
        })
        session["violations"] = violations
    
    if is_ai_generated:
        violations.append({
            "type": "ai_generated",
            "question": session.get("questions_asked", 0),
            "response": response_text[:100] + "..." if len(response_text) > 100 else response_text,
            "confidence": ai_count / len(ai_indicators) if ai_indicators else 0.0
        })
        session["violations"] = violations
    
    # Response history already stored above
    
    # Store warnings
    if warnings:
        session["warnings"] = session.get("warnings", []) + warnings
    
    score = base_score
    session["total_score"] += score
    
    # Check if interview should continue (10-12 minutes = 8-10 questions)
    if session["responses_received"] >= 9:  # 9 questions for 10-12 minutes
        session["status"] = "completed"
        session["end_time"] = datetime.now().isoformat()
        avg_score = session["total_score"] / session["responses_received"]
        
        return {
            "status": "completed",
            "message": "Interview completed",
            "summary": {
                "total_questions": session["questions_asked"],
                "total_responses": session["responses_received"],
                "average_score": round(avg_score, 2),
                "recommendation": "Strong Consider" if avg_score >= 7.0 else "Do Not Hire"
            }
        }
    else:
        # Generate next question based on resume and job description
        candidate = candidates_db.get(session["candidate_id"], {})
        job = jobs_db.get(session["job_id"], {})
        
        # Get resume data
        resume_text = candidate.get("resume_text", "")
        job_description = job.get("description", "")
        required_skills = job.get("required_skills", [])
        
        # Generate contextual questions based on data
        next_question = await generate_contextual_question(
            session["responses_received"], 
            candidate, 
            job, 
            resume_text, 
            job_description, 
            required_skills
        )
        
        session["current_question"] = next_question
        session["questions_asked"] += 1
        session["question_history"].append(next_question)
        
        return {
            "status": "continue",
            "next_question": next_question,
            "question_number": session["questions_asked"],
            "score": round(score, 2),
            "response_received": response_text,
            "warnings": warnings if warnings else None,
            "duplicate_count": session.get("duplicate_count", 0),
            "ai_generated_count": session.get("ai_generated_count", 0),
            "candidate_name_from_intro": session.get("candidate_name_from_intro")
        }

@app.get("/interviews/{session_id}/summary")
async def get_interview_summary(session_id: str):
    """Get interview summary"""
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    session = sessions_db[session_id]
    
    if session["status"] != "completed":
        raise HTTPException(status_code=400, detail="Interview is not completed yet")
    
    avg_score = session["total_score"] / session["responses_received"] if session["responses_received"] > 0 else 0.0
    
    # Generate funny analysis of violations
    violations = session.get("violations", [])
    funny_analysis = generate_funny_analysis(violations)
    
    violations_analysis = {
        "funny_analysis": funny_analysis,
        "violations": violations,
        "violation_count": len(violations),
        "duplicate_count": len([v for v in violations if v["type"] == "duplicate"]),
        "ai_generated_count": len([v for v in violations if v["type"] == "ai_generated"])
    }
    
    return InterviewSummaryResponse(
        session_id=session_id,
        candidate_name=session.get("candidate_name_from_intro") or session["candidate_name"],
        job_title=session["job_title"],
        total_questions=session["questions_asked"],
        total_responses=session["responses_received"],
        overall_score=round(avg_score, 2),
        recommendation="Strong Consider" if avg_score >= 7.0 else "Do Not Hire",
        summary=f"Interview completed for {session['candidate_name']} for {session['job_title']} position. Average score: {avg_score:.2f}/10.",
        strengths=["Good communication", "Relevant experience"] if avg_score >= 6.0 else ["Participated in interview"],
        areas_for_improvement=["Could provide more specific examples"] if avg_score < 7.0 else ["Continue professional development"],
        detailed_assessment={
            "technical_skills": round(avg_score, 2),
            "communication": round(avg_score + 0.5, 2),
            "cultural_fit": round(avg_score - 0.2, 2)
        },
        violations_analysis=violations_analysis
    )

@app.get("/interviews")
async def list_interviews():
    """List all interview sessions"""
    return {"interviews": list(sessions_db.values()), "total": len(sessions_db)}

@app.delete("/interviews/{session_id}")
async def delete_interview(session_id: str):
    """Delete interview session"""
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    del sessions_db[session_id]
    return {"message": "Interview session deleted successfully"}

@app.get("/interviews/{session_id}/ai-summary")
async def get_ai_generated_summary(session_id: str):
    """Get AI-generated human-like interview summary"""
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    session = sessions_db[session_id]
    
    if session["status"] != "completed":
        raise HTTPException(status_code=400, detail="Interview is not completed yet")
    
    # Get candidate and job info
    candidate = candidates_db.get(session["candidate_id"], {})
    job = jobs_db.get(session["job_id"], {})
    
    avg_score = session["total_score"] / session["responses_received"] if session["responses_received"] > 0 else 0.0
    
    # Generate human-like AI summary
    ai_summary = generate_human_like_summary(session, candidate, job, avg_score)
    
    return {
        "session_id": session_id,
        "candidate_name": session.get("candidate_name_from_intro") or session["candidate_name"],
        "job_title": session["job_title"],
        "ai_summary": ai_summary,
        "overall_score": round(avg_score, 2),
        "recommendation": "Strong Consider" if avg_score >= 7.0 else "Do Not Hire"
    }

def analyze_responses(responses: List[Dict]) -> Dict[str, int]:
    """Analyze responses to provide more specific feedback"""
    analysis = {
        'technical_depth': 0,
        'experience_relevance': 0,
        'communication': 0,
        'effort': 0
    }
    
    technical_keywords = ['algorithm', 'database', 'api', 'framework', 'architecture', 'optimization', 'scalability', 'testing', 'deployment']
    experience_keywords = ['project', 'team', 'company', 'worked', 'developed', 'implemented', 'managed', 'led']
    
    for response in responses:
        response_text = response.get('response_text', '').lower()
        
        # Check technical depth
        if any(keyword in response_text for keyword in technical_keywords):
            analysis['technical_depth'] += 1
            
        # Check experience relevance
        if any(keyword in response_text for keyword in experience_keywords):
            analysis['experience_relevance'] += 1
            
        # Check communication quality (length and structure)
        if len(response_text.split()) > 20:  # Substantial response
            analysis['communication'] += 1
            
        # Check effort (any response shows effort)
        if len(response_text.strip()) > 0:
            analysis['effort'] += 1
    
    return analysis

async def generate_contextual_question(question_number, candidate, job, resume_text, job_description, required_skills):
    """Generate contextual questions using LLM service with fallback to template-based approach"""
    
    # Try to use LLM service for advanced question generation
    if LLM_SERVICE_AVAILABLE and llm_service.is_initialized:
        try:
            # Prepare candidate context
            candidate_context = {
                'name': candidate.get('name', 'Candidate'),
                'skills': candidate.get('skills', []),
                'experience_years': candidate.get('experience_years', 0),
                'resume_text': resume_text or ''
            }
            
            # Prepare job context
            job_context = {
                'title': job.get('title', 'Position'),
                'company': job.get('company', 'Company'),
                'description': job_description or '',
                'required_skills': required_skills or [],
                'experience_level': job.get('experience_level', 'mid')
            }
            
            # Determine question type based on question number
            if question_number < 3:
                question_type = 'general'
            elif question_number < 6:
                question_type = 'technical'
            else:
                question_type = 'behavioral'
            
            # Generate question using LLM service
            question = await llm_service.generate_interview_question(
                question_type=question_type,
                candidate_context=candidate_context,
                job_context=job_context,
                previous_questions=[],  # Could be enhanced to track previous questions
                question_number=question_number + 1
            )
            
            if question and len(question.strip()) > 10:
                return question.strip()
                
        except Exception as e:
            print(f"LLM question generation failed: {e}")
    
    # Fallback to template-based approach
    return generate_template_question(question_number, candidate, job, resume_text, job_description, required_skills)

def generate_template_question(question_number, candidate, job, resume_text, job_description, required_skills):
    """Fallback template-based question generation"""
    
    # Question 1: Always introduction
    if question_number == 0:
        return "Tell me about yourself and your experience with this role."
    
    # Question 2: Based on resume experience
    if question_number == 1:
        if resume_text and any(word in resume_text.lower() for word in ['project', 'developed', 'built', 'created']):
            return "I see you've worked on several projects. Can you tell me about a specific project you're most proud of and what challenges you faced?"
        else:
            return "What are your key strengths for this position?"
    
    # Question 3: Based on job requirements (avoid mentioning skills not in job description)
    if question_number == 2:
        if required_skills:
            # Only mention skills that are actually in the job description
            job_skills = []
            for skill in required_skills:
                if skill.lower() in job_description.lower():
                    job_skills.append(skill)
            
            if job_skills:
                skills_str = ", ".join(job_skills[:3])
                return f"This role requires expertise in {skills_str}. How do your current skills align with these requirements?"
            else:
                return "Why are you interested in this role and our company?"
        else:
            return "Why are you interested in this role and our company?"
    
    # Question 4: Technical depth based on resume
    if question_number == 3:
        if resume_text and any(word in resume_text.lower() for word in ['python', 'java', 'javascript', 'sql', 'machine learning', 'data']):
            return "Describe a challenging technical problem you solved recently. What approach did you take and what was the outcome?"
        else:
            return "How do you approach debugging and problem-solving in your work?"
    
    # Question 5: Industry/domain specific
    if question_number == 4:
        if job_description:
            if 'data' in job_description.lower():
                return "How do you ensure data quality and accuracy in your work?"
            elif 'software' in job_description.lower():
                return "What development methodologies do you follow, and how do you ensure code quality?"
            elif 'analysis' in job_description.lower():
                return "Can you walk me through your analytical process when approaching a new problem?"
            else:
                return "What technologies and tools are you most comfortable with?"
        else:
            return "What technologies and tools are you most comfortable with?"
    
    # Question 6: Experience-based
    if question_number == 5:
        if resume_text and any(word in resume_text.lower() for word in ['team', 'collaborate', 'lead', 'manage']):
            return "Tell me about a time when you had to work with a difficult team member or stakeholder. How did you handle the situation?"
        else:
            return "How do you stay updated with the latest trends and technologies in your field?"
    
    # Question 7: Problem-solving approach
    if question_number == 6:
        if required_skills and len(required_skills) > 0:
            # Only mention skills that are in the job description
            job_skills = [skill for skill in required_skills if skill.lower() in job_description.lower()]
            if job_skills:
                return f"Given that this role involves working with {job_skills[0]}, how would you approach learning a new technology or skill that you haven't used before?"
            else:
                return "How would you approach learning a new technology or skill that you haven't used before?"
        else:
            return "Explain your approach to system design and architecture."
    
    # Question 8: Future and growth
    if question_number == 7:
        return "Where do you see yourself in 3-5 years, and how does this role align with your career goals?"
    
    # Question 9: Final behavioral question instead of asking if they have questions
    if question_number == 8:
        if resume_text and any(word in resume_text.lower() for word in ['project', 'team', 'developed']):
            return "Tell me about a time when you had to overcome a significant challenge or setback in your work. What did you learn from that experience?"
        else:
            return "What motivates you most in your professional life, and how does this role align with those motivations?"
    
    # Fallback
    return "Thank you for your time and for sharing your experiences with us today."

def generate_human_like_summary(session, candidate, job, avg_score):
    """Generate a human-like interview summary"""
    
    # Determine recommendation tone
    if avg_score >= 8.0:
        tone = "very positive"
        recommendation = "strong hire"
    elif avg_score >= 7.0:
        tone = "positive"
        recommendation = "recommend for hire"
    elif avg_score >= 5.0:
        tone = "mixed"
        recommendation = "consider with reservations"
    else:
        tone = "negative"
        recommendation = "not recommend for hire"
    
    # Generate contextual feedback based on actual responses
    strengths = []
    weaknesses = []
    suggestions = []
    
    # Analyze responses for more specific feedback
    response_analysis = analyze_responses(session['responses'])
    
    if avg_score >= 7.0:
        strengths = [
            "demonstrated strong communication skills with clear, structured responses",
            "showed solid technical knowledge and provided relevant examples",
            "displayed good problem-solving approach and analytical thinking",
            "exhibited enthusiasm and cultural fit for the role"
        ]
        if response_analysis.get('technical_depth', 0) > 0:
            strengths.append("provided detailed technical explanations and examples")
        if response_analysis.get('experience_relevance', 0) > 0:
            strengths.append("shared relevant past experience that aligns with role requirements")
            
        weaknesses = [
            "could benefit from more specific technical implementation details",
            "may need to elaborate more on complex problem-solving methodologies"
        ]
        suggestions = [
            "Continue developing expertise in current technologies",
            "Practice articulating technical concepts with more precision",
            "Prepare detailed case studies for future interviews"
        ]
    elif avg_score >= 5.0:
        strengths = [
            "showed basic competency in core required skills",
            "demonstrated willingness to learn and adapt",
            "provided some relevant experience examples"
        ]
        if response_analysis.get('communication', 0) > 0:
            strengths.append("maintained clear communication throughout the interview")
            
        weaknesses = [
            "lacked depth in technical explanations and implementation details",
            "could improve clarity in expressing complex ideas",
            "needed more specific examples with measurable outcomes"
        ]
        suggestions = [
            "Focus on strengthening technical fundamentals through hands-on practice",
            "Practice explaining complex concepts using simple, clear language",
            "Prepare detailed project examples with specific metrics and outcomes",
            "Consider additional training in key technologies mentioned in the role"
        ]
    else:
        strengths = [
            "participated actively in the interview process"
        ]
        if response_analysis.get('effort', 0) > 0:
            strengths.append("showed genuine interest and effort in responding to questions")
            
        weaknesses = [
            "demonstrated insufficient technical knowledge for the role requirements",
            "struggled with clear communication and structured responses",
            "lacked relevant experience examples and specific details",
            "showed limited understanding of key role responsibilities"
        ]
        suggestions = [
            "Invest in comprehensive technical training in core technologies",
            "Practice interview skills and structured communication techniques",
            "Gain hands-on experience through projects or internships",
            "Consider entry-level positions to build foundational experience"
        ]
    
    # Use extracted name if available, otherwise fallback to stored name
    display_name = session.get("candidate_name_from_intro") or session['candidate_name']
    
    # Generate the human-like summary with better formatting
    summary = f"""Dear {display_name},

Thank you for taking the time to interview for the {session['job_title']} position. I wanted to share some feedback from our conversation to help you in your professional development.

OVERALL ASSESSMENT
Your interview performance was {tone}, with an average score of {avg_score:.1f}/10 across {session['responses_received']} questions. Based on your responses, I would {recommendation} for this position.

WHAT WENT WELL
"""
    
    for strength in strengths:
        summary += f"• You {strength}\n"
    
    summary += f"""
AREAS FOR IMPROVEMENT
"""
    
    for weakness in weaknesses:
        summary += f"• You {weakness}\n"
    
    summary += f"""
RECOMMENDATIONS FOR GROWTH
"""
    
    for suggestion in suggestions:
        summary += f"• {suggestion}\n"
    
    summary += f"""
NEXT STEPS
Based on your performance, I would suggest focusing on the areas mentioned above. If you're interested in this role, I'd recommend reaching out to discuss how we can support your development in these areas.

Thank you again for your interest in joining our team. I wish you the best in your career journey.

Best regards,
Interview Assessment Team

---
*This feedback was generated based on your responses to {session['questions_asked']} interview questions covering general, technical, and theoretical aspects of the role.*
"""
    
    return summary.strip()

@app.post("/resumes/parse")
async def parse_resume(file: UploadFile = File(...)):
    """Parse resume file and extract candidate information"""
    try:
        # Parse resume using resume_parser
        parsed_data = resume_parser.parse_resume_from_pdf(file.file)
        
        return {
            "success": True,
            "data": parsed_data,
            "message": "Resume parsed successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing resume: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    return {
        "total_candidates": len(candidates_db),
        "total_jobs": len(jobs_db),
        "total_interviews": len(sessions_db),
        "active_interviews": len([s for s in sessions_db.values() if s["status"] == "active"]),
        "completed_interviews": len([s for s in sessions_db.values() if s["status"] == "completed"])
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting SkillScreen Simplified API...")
    print("API will be available at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")
    print("Interactive API testing at: http://localhost:8000/redoc")
    uvicorn.run(app, host="0.0.0.0", port=8000)
