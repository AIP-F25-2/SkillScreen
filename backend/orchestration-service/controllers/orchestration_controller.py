from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import update
from repositories.orchestration_repository import OrchestrationRepository
from db import UnitOfWork
from utils.response import create_response
from utilities.logger import init_logger
from services.interview_orchestration_service import InterviewOrchestrationService
from uuid import UUID

router = APIRouter()

uow = UnitOfWork()
orchestrator_repo = OrchestrationRepository(uow)
orchestration_service = InterviewOrchestrationService()
log = init_logger("orchestrator-service")


# Request/Response Models
class NextQuestionRequest(BaseModel):
    previous_response: str
    question_number: int


@router.get("/")
def health_check():
    return create_response({
        "message": "Orchestration Service is running",
        "status": "deployed",
        "service": "orchestration-service"
    })


@router.get("/health")
def health():
    return create_response({
        "service": "orchestration-service",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    })

@router.get("/interviews/start/{interview_id}")
async def start_interview(interview_id: UUID):
    """
    Start interview flow based on interview ID
    
    Flow:
    1. Get interview data from database
    2. Get candidate data from database
    3. Download and parse resume from Azure Blob Storage
    4. Generate initial question based on resume
    5. Return interview data and first question
    
    Args:
        interview_id: Interview ID
    """
    try:
        log.info(f"Starting interview flow for interview_id: {interview_id}")
        
        # Step 1: Get interview data
        interview = orchestrator_repo.get_interview_by_id(str(interview_id))
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        candidate_id = interview.get("candidate_id")
        if not candidate_id:
            raise HTTPException(status_code=400, detail="Interview is missing candidate ID")
        
        # Step 2: Get candidate data from database
        candidate = orchestrator_repo.get_candidate_by_id(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        resume_url = candidate.get("resume_url")
        if not resume_url:
            raise HTTPException(status_code=400, detail="Candidate resume not found")
        
        # Step 3: Download and parse resume
        log.info(f"Downloading and parsing resume for candidate {candidate_id}")
        resume_data = await orchestration_service.download_and_parse_resume(resume_url)
        
        # Step 4: Get job/interview-related data if needed
        job_data = None
        if interview.get("job_position_id"):
            # TODO: Fetch job position data if needed
            # For now, we'll rely on resume_data
            pass
        
        # Step 5: Create interview session in text-service and get first question
        candidate_context = {
            "candidateId": candidate_id,
            "candidate_name": candidate.get("full_name") or resume_data.get("name"),
            "candidateEmail": candidate.get("email"),
        }
        
        session_data = await orchestration_service.create_interview_session(
            candidate_data=candidate_context,
            resume_data=resume_data,
            job_data=job_data
        )
        
        text_service_session_id = session_data.get("session_id")
        first_question = session_data.get("first_question", "Tell me about yourself and your experience with this role.")
        
        # Store text-service session_id in interview settings for later use
        try:
            # Re-fetch to avoid stale object issues
            interview = orchestrator_repo.get_interview_by_id(interview_id)
            if interview:
                settings = interview.get("settings") or {}
                if isinstance(settings, dict):
                    settings["text_service_session_id"] = text_service_session_id
                    settings["resume_data"] = resume_data  # Store for follow-up questions

                    from sqlalchemy import update
                    from repositories.orchestration_repository import interviews_table

                    stmt = (
                        update(interviews_table)
                        .where(interviews_table.c.id == interview_id)
                        .values(
                            settings=settings,
                            status="in_progress",
                            updated_at=datetime.utcnow()
                        )
                    )
                    orchestrator_repo.session.execute(stmt)
                    orchestrator_repo.session.commit()
                else:
                    orchestrator_repo.update_interview_status(interview_id, "in_progress")
            else:
                orchestrator_repo.update_interview_status(interview_id, "in_progress")
        except Exception as e:
            log.warning(f"Failed to update interview with session data: {str(e)}")
            try:
                orchestrator_repo.update_interview_status(interview_id, "in_progress")
            except:
                pass
        
        log.info(
            f"Interview started successfully: {interview_id}, "
            f"text-service session: {text_service_session_id}"
        )
        
        return create_response({
            "interview_id": interview_id,
            "session_id": text_service_session_id or interview_id,
            "candidate_id": candidate_id,
            "candidate_name": candidate_context["candidate_name"],
            "candidate_email": candidate_context["candidateEmail"],
            "resume_data": {
                "name": resume_data.get("name"),
                "skills": resume_data.get("skills", []),
                "experience_years": resume_data.get("experience_years", 0),
            },
            "first_question": first_question,
            "question_number": 1,
            "status": "in_progress"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error starting interview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {str(e)}")


@router.post("/interviews/{interview_id}/next-question")
async def get_next_question(interview_id: str, request: NextQuestionRequest):
    """
    Generate next interview question based on candidate's previous response
    
    Flow:
    1. Get interview session data
    2. Submit previous response to text-service
    3. Get next question from text-service
    4. Return next question or completion status
    
    Args:
        interview_id: Interview ID
        request: Previous response and question number
    """
    try:
        log.info(f"Generating next question for interview {interview_id}, question #{request.question_number}")
        
        # Get interview data
        interview = orchestrator_repo.get_interview_by_id(interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        # Get text-service session_id from interview settings
        settings = interview.get("settings") or {}
        text_service_session_id = settings.get("text_service_session_id")
        resume_data = settings.get("resume_data")
        
        # Use text-service session_id if available, otherwise use interview_id
        session_id = text_service_session_id or interview_id
        
        # Generate next question
        next_question = await orchestration_service.generate_next_question(
            interview_id=interview_id,
            session_id=session_id,
            previous_response=request.previous_response,
            question_number=request.question_number,
            resume_data=resume_data
        )
        
        if next_question is None:
            # Interview completed
            try:
                orchestrator_repo.update_interview_status(interview_id, "completed")
            except Exception as e:
                log.warning(f"Failed to update interview status: {str(e)}")
            
            return create_response({
                "status": "completed",
                "message": "Interview completed",
                "interview_id": interview_id
            })
        
        return create_response({
            "interview_id": interview_id,
            "session_id": session_id,
            "next_question": next_question,
            "question_number": request.question_number + 1,
            "status": "in_progress"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error generating next question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate next question: {str(e)}")


@router.get("/interviews/{interview_id}/summary")
async def get_interview_summary(interview_id: str):
    """
    Get interview summary after completion
    
    Args:
        interview_id: Interview ID
    """
    try:
        interview = orchestrator_repo.get_interview_by_id(interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        session_id = interview_id
        summary = await orchestration_service.get_interview_summary(session_id)
        
        return create_response(summary)
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting interview summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get interview summary: {str(e)}")
