from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import os
from sqlalchemy import update
from repositories.orchestration_repository import OrchestrationRepository
from db import UnitOfWork
from utils.response import create_response
from utilities.logger import init_logger
from services.interview_orchestration_service import InterviewOrchestrationService
from uuid import UUID

from sqlalchemy import update
from repositories.orchestration_repository import interviews_table

router = APIRouter()

uow = UnitOfWork()
orchestrator_repo = OrchestrationRepository(uow)
orchestration_service = InterviewOrchestrationService()
log = init_logger("orchestrator-service")

INTERVIEW_NOT_FOUND = "Interview not found"


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
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@router.get("/interviews/start/{interview_id}")
async def start_interview(interview_id: UUID): # nosonar
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
            raise HTTPException(status_code=404, detail=INTERVIEW_NOT_FOUND)
        
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
            job_data=job_data,
            interview_id=str(interview_id)  # Pass interview_id for question variation
        )
        
        text_service_session_id = session_data.get("session_id")
        coding_question = session_data.get("coding_question")
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
                    if coding_question:
                        settings["coding_question"] = coding_question



                    stmt = (
                        update(interviews_table)
                        .where(interviews_table.c.id == interview_id)
                        .values(
                            settings=settings,
                            status="in_progress",
                            updated_at=datetime.now(timezone.utc)
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
        
        # Create interview_session record for the first question
        try:
            session_metadata = {
                "text_service_session_id": text_service_session_id,
                "coding_question": coding_question is not None
            }
            if coding_question:
                session_metadata["coding_question_id"] = coding_question.get("title", "")
            
            orchestrator_repo.create_interview_session(
                interview_id=str(interview_id),
                question_id="q1",
                question_text=first_question,
                question_type="general",
                metadata=session_metadata
            )
            log.info(f"Created interview_session record for interview {interview_id}, question q1")
        except Exception as e:
            log.warning(f"Failed to create interview_session record: {str(e)}")
            # Continue even if session record creation fails
        
        return create_response({
            "interview_id": interview_id,
            "session_id": text_service_session_id or interview_id,
            "candidate_id": candidate_id,
            "candidate_name": candidate_context["candidate_name"],
            "candidate_email": candidate_context["candidateEmail"],
            "coding_question": coding_question,
            "resume_data": {
                "name": resume_data.get("name"),
                "skills": resume_data.get("skills", []),
                "experience_years": resume_data.get("experience_years", 0),
            },
            "first_question": first_question,
            "coding_question": coding_question,
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
    """
    try:
        log.info(f"Generating next question for interview {interview_id}, question #{request.question_number}")
        
        # Get interview data
        interview = orchestrator_repo.get_interview_by_id(interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail=INTERVIEW_NOT_FOUND)
        
        # Get text-service session_id from interview settings
        settings = interview.get("settings") or {}
        text_service_session_id = settings.get("text_service_session_id")
        resume_data = settings.get("resume_data")
        
        # Use text-service session_id if available, otherwise use interview_id
        session_id = text_service_session_id or interview_id
        
        # Update previous interview_session with candidate response
        _update_previous_session(interview_id, request.previous_response)
        
        # Generate next question
        next_question = await orchestration_service.generate_next_question(
            interview_id=interview_id,
            session_id=session_id,
            previous_response=request.previous_response,
            question_number=request.question_number,
            resume_data=resume_data
        )
        
        if next_question is None:
            return _handle_interview_completion(interview_id)
        
        # Create new interview_session record for the next question
        next_question_number = request.question_number + 1
        _create_next_session_record(interview_id, next_question, next_question_number, text_service_session_id)
        
        return create_response({
            "interview_id": interview_id,
            "session_id": session_id,
            "next_question": next_question,
            "question_number": next_question_number,
            "status": "in_progress"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error generating next question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate next question: {str(e)}")


def _update_previous_session(interview_id: str, response: str):
    try:
        previous_session = orchestrator_repo.get_latest_interview_session(interview_id)
        if previous_session:
            previous_session_id = previous_session.get("id")
            if previous_session_id:
                orchestrator_repo.update_interview_session_response(
                    session_id=str(previous_session_id),
                    candidate_response=response,
                    response_duration=None
                )
                log.info("Updated interview_session %s with candidate response", previous_session_id)
    except Exception as e:
        log.warning("Failed to update previous interview_session: %s", str(e))


def _handle_interview_completion(interview_id: str):
    try:
        orchestrator_repo.update_interview_status(interview_id, "completed")
    except Exception as e:
        log.warning("Failed to update interview status: %s", str(e))
    
    return create_response({
        "status": "completed",
        "message": "Interview completed",
        "interview_id": interview_id
    })


def _create_next_session_record(interview_id: str, next_question: str, question_number: int, text_service_session_id: Optional[str]):
    try:
        if question_number <= 1:
            question_type = "general"
        elif question_number <= 4:
            question_type = "technical"
        else:
            question_type = "theoretical"
        
        orchestrator_repo.create_interview_session(
            interview_id=interview_id,
            question_id=f"q{question_number}",
            question_text=next_question,
            question_type=question_type,
            metadata={
                "previous_question_number": question_number - 1,
                "text_service_session_id": text_service_session_id
            }
        )
        log.info("Created interview_session record for interview %s, question q%d", interview_id, question_number)
    except Exception as e:
        log.warning("Failed to create interview_session record: %s", str(e))


class SubmitCodeRequest(BaseModel):
    languageId: int
    sourceCode: str


@router.post("/interviews/{interview_id}/submit-code")
async def submit_code(interview_id: str, body: SubmitCodeRequest):
    """Submit candidate code for the coding_question attached to the interview and evaluate using coding-service."""
    try:
        interview = orchestrator_repo.get_interview_by_id(interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail=INTERVIEW_NOT_FOUND)

        settings = interview.get("settings") or {}
        coding_q = settings.get("coding_question")
        if not coding_q:
            raise HTTPException(status_code=400, detail="No coding question attached to this interview")

        # Normalize test cases for coding-service evaluate endpoint
        test_cases = []
        for i, tc in enumerate(coding_q.get("test_cases", [])):
            # test cases may be {input, expected_output} or similar
            input_val = tc.get("input") or tc.get("stdin") or tc.get("input_data") or ""
            expected = tc.get("expected_output") or tc.get("expectedOutput") or tc.get("output") or ""
            test_cases.append({"id": tc.get("id") or f"tc_{i}", "input": input_val, "expectedOutput": expected, "weight": float(tc.get("weight", 1.0))})

        payload = {
            "languageId": body.languageId,
            "sourceCode": body.sourceCode,
            "testCases": test_cases
        }

        # Forward to coding-service evaluate endpoint
        resp = await orchestration_service.client.post(f"{os.getenv('CODING_SERVICE_URL','http://coding-service:8080')}/evaluate", json=payload)
        resp.raise_for_status()
        result = resp.json()

        # Persist evaluation in interview settings (append results)
        try:
            settings.setdefault("coding_attempts", [])
            settings["coding_attempts"].append({"timestamp": datetime.now(timezone.utc).isoformat(), "result": result})
            # update DB
            # update DB
            stmt = (
                update(interviews_table)
                .where(interviews_table.c.id == interview_id)
                .values(settings=settings, updated_at=datetime.now(timezone.utc))
            )
            orchestrator_repo.session.execute(stmt)
            orchestrator_repo.session.commit()
        except Exception as e:
            log.warning(f"Failed to persist coding attempt: {e}")

        return create_response(result)

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"submit_code_error: {e}")
        raise HTTPException(status_code=500, detail="Failed to evaluate submitted code")


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
            raise HTTPException(status_code=404, detail=INTERVIEW_NOT_FOUND)
        
        session_id = interview_id
        summary = await orchestration_service.get_interview_summary(session_id)
        
        return create_response(summary)
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting interview summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get interview summary: {str(e)}")


@router.post("/interviews/trigger-analyses/{interview_id}")
async def trigger_interview_analyses(interview_id: str): # nosonar
    """
    Trigger all analysis services (audio, video, text) for a completed interview
    
    This endpoint is fault-tolerant - if any service fails, it logs the error
    and continues with the other services.
    
    Flow:
    1. Get interview data and settings
    2. Get media file information (video URL, media_file_id)
    3. Get text-service session_id from interview settings
    4. Trigger audio analysis (async)
    5. Trigger video analysis (async)
    6. Get text analysis summary (may already be generated)
    7. Return results with success/failure status for each service
    
    Args:
        interview_id: Interview ID
    """
    try:
        # Ensure interview_id is a string (in case it's a UUID object from path parameter)
        interview_id_str = str(interview_id)
        log.info(f"Triggering analyses for interview {interview_id_str}")
        
        # Get interview data
        interview = orchestrator_repo.get_interview_by_id(interview_id_str)
        if not interview:
            raise HTTPException(status_code=404, detail=INTERVIEW_NOT_FOUND)
        
        # Get text-service session_id from interview settings
        settings = interview.get("settings") or {}
        text_service_session_id = settings.get("text_service_session_id") or interview_id_str
        # Ensure text_service_session_id is a string
        text_service_session_id = str(text_service_session_id) if text_service_session_id else interview_id_str
        
        candidate_id = interview.get("candidate_id")
        # Ensure candidate_id is converted to string (in case it's a UUID object)
        candidate_id_str = str(candidate_id) if candidate_id else None
        
        # Get media file information
        media_file = orchestrator_repo.get_media_file_by_interview_id(interview_id_str)
        
        media_file_id = None
        video_url = None
        storage_uri = None
        
        if media_file:
            media_file_id = str(media_file.get("id", "")) if media_file.get("id") else None
            storage_uri = media_file.get("storage_uri", "")
            
            # Construct video URL for video-ai-service
            if storage_uri:
                # storage_uri format: /user_id/filename.mp4 or full URL
                if storage_uri.startswith("http"):
                    video_url = storage_uri
                else:
                    # Construct Docker internal network URL
                    video_url = f"{os.getenv('MEDIA_SERVICE_URL', 'http://media-service:8080')}/video{storage_uri}"
                
                log.info(f"Found media file {media_file_id}, video_url: {video_url}")
            else:
                log.warning(f"Media file {media_file_id} found but storage_uri is missing")
        else:
            log.warning(f"No media file found for interview {interview_id_str} - skipping audio/video analysis")
        
        # Initialize results structure
        results = {
            "interview_id": interview_id_str,
            "session_id": text_service_session_id,
            "analyses": {},
            "summary": {
                "total_services": 3,
                "successful": 0,
                "failed": 0,
                "errors": []
            }
        }
        
        # Trigger audio analysis (fault-tolerant)
        if media_file_id:
            try:
                log.info(f"Triggering audio analysis for interview {interview_id_str}, media_file {media_file_id}")
                resp = await orchestration_service.client.post(
                    f"{os.getenv('AUDIO_AI_SERVICE_URL', 'http://audio-ai-service:8080')}/process-interview-audio",
                    json={
                        "interview_id": interview_id_str,
                        "session_id": text_service_session_id,
                        "media_file_id": media_file_id
                    },
                    timeout=60.0
                )
                resp.raise_for_status()
                result = resp.json()
                results["analyses"]["audio"] = {
                    "status": "success",
                    "service": "audio-ai",
                    "result": result
                }
                results["summary"]["successful"] += 1
                log.info(f"Audio analysis triggered successfully for interview {interview_id_str}")
            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                results["analyses"]["audio"] = {
                    "status": "error",
                    "service": "audio-ai",
                    "error": error_msg
                }
                results["summary"]["failed"] += 1
                results["summary"]["errors"].append({
                    "service": "audio-ai",
                    "error": error_msg
                })
                log.error(f"Audio analysis error for interview {interview_id_str}: {error_msg}", exc_info=True)
        else:
            results["analyses"]["audio"] = {
                "status": "skipped",
                "service": "audio-ai",
                "reason": "No media_file_id provided"
            }
            log.warning(f"Skipping audio analysis - no media_file_id provided for interview {interview_id_str}")
        
        # Trigger video analysis (fault-tolerant)
        if video_url:
            try:
                log.info(f"Triggering video analysis for interview {interview_id_str}, user_id: {candidate_id_str}, video: {video_url}")
                resp = await orchestration_service.client.post(
                    f"{os.getenv('VIDEO_AI_SERVICE_URL', 'http://video-ai-service:8080')}/analyze-url",
                    json={
                        "user_id": candidate_id_str or interview_id_str,
                        "video_url": video_url
                    },
                    timeout=300.0
                )
                resp.raise_for_status()
                result = resp.json()
                results["analyses"]["video"] = {
                    "status": "success",
                    "service": "video-ai",
                    "result": result
                }
                results["summary"]["successful"] += 1
                log.info(f"Video analysis triggered successfully for interview {interview_id_str}")
            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                results["analyses"]["video"] = {
                    "status": "error",
                    "service": "video-ai",
                    "error": error_msg
                }
                results["summary"]["failed"] += 1
                results["summary"]["errors"].append({
                    "service": "video-ai",
                    "error": error_msg
                })
                log.error(f"Video analysis error for interview {interview_id_str}: {error_msg}", exc_info=True)
        else:
            results["analyses"]["video"] = {
                "status": "skipped",
                "service": "video-ai",
                "reason": "No video_url provided"
            }
            log.warning(f"Skipping video analysis - no video_url provided for interview {interview_id_str}")
        
        # Get text analysis (fault-tolerant)
        try:
            log.info(f"Getting text analysis summary for session {text_service_session_id}")
            endpoints_to_try = [
                f"{os.getenv('TEXT_SERVICE_URL', 'http://text-service:8080')}/api/interviews/{text_service_session_id}/summary",
                f"{os.getenv('TEXT_SERVICE_URL', 'http://text-service:8080')}/interviews/{text_service_session_id}/summary",
            ]
            
            text_result = None
            for endpoint in endpoints_to_try:
                try:
                    resp = await orchestration_service.client.get(endpoint, timeout=30.0)
                    resp.raise_for_status()
                    result = resp.json()
                    text_result = {
                        "status": "success",
                        "service": "text-service",
                        "result": result
                    }
                    break
                except Exception as e:
                    if "404" in str(e) or "Not Found" in str(e):
                        continue
                    raise
            
            if text_result:
                results["analyses"]["text"] = text_result
                results["summary"]["successful"] += 1
                log.info(f"Text analysis retrieved successfully for session {text_service_session_id}")
            else:
                # Session not found - expected if text-service wasn't used
                results["analyses"]["text"] = {
                    "status": "skipped",
                    "service": "text-service",
                    "message": "Text service session not found. The interview may not have been processed through text-service.",
                    "hint": "Text analysis is only available for interviews that were processed through the text-service pipeline."
                }
                log.info(f"Text service session {text_service_session_id} not found - skipping text analysis")
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            results["analyses"]["text"] = {
                "status": "error",
                "service": "text-service",
                "error": error_msg
            }
            results["summary"]["failed"] += 1
            results["summary"]["errors"].append({
                "service": "text-service",
                "error": error_msg
            })
            log.error(f"Text analysis error for session {text_service_session_id}: {error_msg}", exc_info=True)
        
        log.info(
            f"Analysis orchestration completed for interview {interview_id_str}: "
            f"{results['summary']['successful']}/{results['summary']['total_services']} services successful"
        )
        
        return create_response(results)
        
    except HTTPException:
        raise
    except Exception as e:
        interview_id_for_error = interview_id_str if 'interview_id_str' in locals() else str(interview_id)
        log.error(f"Error triggering analyses for interview {interview_id_for_error}: {str(e)}", exc_info=True)
        # Return error but don't fail completely - allow frontend to continue
        return create_response({
            "interview_id": interview_id_for_error,
            "status": "error",
            "error": f"Failed to trigger analyses: {str(e)}",
            "analyses": {},
            "summary": {
                "total_services": 3,
                "successful": 0,
                "failed": 3,
                "errors": [{"service": "orchestration", "error": str(e)}]
            }
        })
