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
        "services": ["interview", "nlp", "anti-cheating"]
    }

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
        "total_score": 0.0
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
    session["response_history"].append({
        "response": response.response_text,
        "timestamp": datetime.now().isoformat(),
        "question_number": session["questions_asked"]
    })
    session["responses_received"] += 1
    
    # Simple scoring logic (mock)
    score = min(8.0, max(3.0, len(response.response_text) / 20.0))
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
                "recommendation": "Strong Consider" if avg_score >= 7.0 else "Consider" if avg_score >= 5.0 else "Do Not Hire"
            }
        }
    else:
        # Generate next question based on interview round
        # Round 1: General Questions (1-3)
        # Round 2: Technical Questions (4-6) 
        # Round 3: Theoretical Questions (7-9)
        
        question_round = min(3, (session["responses_received"] // 3) + 1)
        
        if question_round == 1:  # General Questions
            questions = [
                "Tell me about yourself and your experience with this role.",
                "What are your key strengths for this position?",
                "Why are you interested in this role and our company?"
            ]
        elif question_round == 2:  # Technical Questions
            questions = [
                "Describe a challenging technical project you worked on.",
                "How do you approach debugging and problem-solving?",
                "What technologies and tools are you most comfortable with?"
            ]
        else:  # Theoretical Questions
            questions = [
                "Explain your approach to system design and architecture.",
                "How do you ensure code quality and maintainability?",
                "What industry trends do you think will shape this field?"
            ]
        
        # Get question based on position within the round
        round_position = session["responses_received"] % 3
        next_question = questions[round_position] if round_position < len(questions) else "Thank you for your time. The interview is complete."
        session["current_question"] = next_question
        session["questions_asked"] += 1
        session["question_history"].append(next_question)
        
        return {
            "status": "continue",
            "next_question": next_question,
            "question_number": session["questions_asked"],
            "score": round(score, 2),
            "response_received": response.response_text
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
    
    return InterviewSummaryResponse(
        session_id=session_id,
        candidate_name=session["candidate_name"],
        job_title=session["job_title"],
        total_questions=session["questions_asked"],
        total_responses=session["responses_received"],
        overall_score=round(avg_score, 2),
        recommendation="Strong Consider" if avg_score >= 7.0 else "Consider" if avg_score >= 5.0 else "Do Not Hire",
        summary=f"Interview completed for {session['candidate_name']} for {session['job_title']} position. Average score: {avg_score:.2f}/10.",
        strengths=["Good communication", "Relevant experience"] if avg_score >= 6.0 else ["Participated in interview"],
        areas_for_improvement=["Could provide more specific examples"] if avg_score < 7.0 else ["Continue professional development"],
        detailed_assessment={
            "technical_skills": round(avg_score, 2),
            "communication": round(avg_score + 0.5, 2),
            "cultural_fit": round(avg_score - 0.2, 2)
        }
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
        "candidate_name": session["candidate_name"],
        "job_title": session["job_title"],
        "ai_summary": ai_summary,
        "overall_score": round(avg_score, 2),
        "recommendation": "Strong Consider" if avg_score >= 7.0 else "Consider" if avg_score >= 5.0 else "Do Not Hire"
    }

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
    
    # Generate contextual feedback
    strengths = []
    weaknesses = []
    suggestions = []
    
    if avg_score >= 7.0:
        strengths = [
            "demonstrated strong communication skills throughout the interview",
            "showed good technical knowledge and problem-solving approach",
            "provided relevant examples from past experience",
            "displayed enthusiasm for the role and company"
        ]
        weaknesses = [
            "could benefit from more specific technical examples",
            "may need to elaborate more on complex problem-solving scenarios"
        ]
        suggestions = [
            "Continue developing expertise in current technologies",
            "Practice articulating technical concepts more clearly",
            "Prepare more detailed examples for future interviews"
        ]
    elif avg_score >= 5.0:
        strengths = [
            "showed basic competency in required skills",
            "demonstrated willingness to learn and grow",
            "provided some relevant experience examples"
        ]
        weaknesses = [
            "lacked depth in technical explanations",
            "could improve communication clarity",
            "needed more specific examples and details"
        ]
        suggestions = [
            "Focus on strengthening technical fundamentals",
            "Practice explaining complex concepts simply",
            "Prepare more detailed project examples",
            "Consider additional training in key technologies"
        ]
    else:
        strengths = [
            "participated actively in the interview process"
        ]
        weaknesses = [
            "demonstrated insufficient technical knowledge",
            "struggled with clear communication",
            "lacked relevant experience examples",
            "showed limited understanding of role requirements"
        ]
        suggestions = [
            "Invest in comprehensive technical training",
            "Practice interview skills and communication",
            "Gain more hands-on experience in relevant technologies",
            "Consider entry-level positions to build experience"
        ]
    
    # Generate the human-like summary
    summary = f"""
Dear {session['candidate_name']},

Thank you for taking the time to interview for the {session['job_title']} position. I wanted to share some feedback from our conversation to help you in your professional development.

**Overall Assessment:**
Your interview performance was {tone}, with an average score of {avg_score:.1f}/10 across {session['responses_received']} questions. Based on your responses, I would {recommendation} for this position.

**What Went Well:**
"""
    
    for strength in strengths:
        summary += f"• You {strength}\n"
    
    summary += f"""
**Areas for Improvement:**
"""
    
    for weakness in weaknesses:
        summary += f"• You {weakness}\n"
    
    summary += f"""
**Recommendations for Growth:**
"""
    
    for suggestion in suggestions:
        summary += f"• {suggestion}\n"
    
    summary += f"""
**Next Steps:**
Based on your performance, I would suggest focusing on the areas mentioned above. If you're interested in this role, I'd recommend reaching out to discuss how we can support your development in these areas.

Thank you again for your interest in joining our team. I wish you the best in your career journey.

Best regards,
Interview Assessment Team

---
*This feedback was generated based on your responses to {session['questions_asked']} interview questions covering general, technical, and theoretical aspects of the role.*
"""
    
    return summary.strip()

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
