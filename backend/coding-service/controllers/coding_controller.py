from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

from services.code_execution_service import CodeExecutionService
from services.coding_question_generator import CodingQuestionGenerator
from services.difficulty_assessor import DifficultyAssessor
from services.web_scraper_service import WebScraperService
from utilities.logger import init_logger

router = APIRouter()

log = init_logger("coding-service")
executor_service = CodeExecutionService()
question_generator = CodingQuestionGenerator()
difficulty_assessor = DifficultyAssessor()
web_scraper = WebScraperService()

def create_response(data, success: bool = True):
    return {
        "success": success,
        "data": data,
        "meta": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": f"req_{uuid.uuid4().hex[:8]}",
            "version": "v1"
        }
    }

class RunCodeRequest(BaseModel):
    languageId: int
    sourceCode: str
    stdin: Optional[str] = ""

class TestCase(BaseModel):
    id: str
    input: str
    expectedOutput: str
    weight: float = 1.0

class EvaluateCodeRequest(BaseModel):
    languageId: int
    sourceCode: str
    testCases: List[TestCase]

@router.get("/")
def root():
    return create_response({
        "message": "Coding Service is running",
        "status": "deployed",
        "service": "coding-service"
    })

@router.get("/health")
def health():
    return create_response({
        "service": "coding-service",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    })

@router.post("/run")
async def run_code(body: RunCodeRequest):
    try:
        result = await executor_service.run_code(
            language_id=body.languageId,
            source_code=body.sourceCode,
            stdin=body.stdin or ""
        )
        log.info("code_run", extra={"status": result["status"]})
        return create_response(result)
    except HTTPException:
        raise
    except Exception as e:
        log.error("code_run_error", exc_info=e)
        raise HTTPException(status_code=500, detail="Internal error running code")
    
@router.post("/evaluate")
async def evaluate_code(body: EvaluateCodeRequest):
    try:
        result = await executor_service.evaluate_code(
            language_id=body.languageId,
            source_code=body.sourceCode,
            test_cases=[tc.model_dump() for tc in body.testCases],
        )
        log.info(
            "code_evaluate",
            extra={
                "score": result["score"],
                "passedWeight": result["passedWeight"],
                "totalWeight": result["totalWeight"],
            },
        )
        return create_response(result)
    except HTTPException:
        raise
    except Exception as e:
        log.error("code_evaluate_error", exc_info=e)
        raise HTTPException(status_code=500, detail="Internal error evaluating code")


@router.post("/generate")
async def generate_question(payload: dict):
    """Generate a coding question using resume and job description.

    Body: { resume_data: {...}, job_description: {...}, difficulty: 'easy|medium|hard', question_number: int, previous_questions: [] }
    """
    try:
        resume_data = payload.get("resume_data", {})
        job_description = payload.get("job_description", {})
        difficulty = payload.get("difficulty") or "medium"
        question_number = int(payload.get("question_number", 1))
        previous_questions = payload.get("previous_questions", []) or []

        interview_id = payload.get("interview_id") or payload.get("interviewId")
        candidate_id = payload.get("candidate_id") or payload.get("candidateId")
        
        question = await question_generator.generate_question(
            resume_data=resume_data,
            job_description=job_description,
            difficulty=difficulty,
            question_number=question_number,
            previous_questions=previous_questions,
            interview_id=interview_id,
            candidate_id=candidate_id,
        )

        log.info("question_generated", extra={"title": question.get("title")})
        return create_response(question)
    except Exception as e:
        log.error("question_generate_error", exc_info=e)
        raise HTTPException(status_code=500, detail="Failed to generate question")


@router.post("/difficulty")
async def assess_difficulty(payload: dict):
    """Assess appropriate difficulty level from resume + job description."""
    try:
        resume_data = payload.get("resume_data", {})
        job_description = payload.get("job_description", {})

        difficulty = await difficulty_assessor.assess_difficulty(resume_data, job_description)
        return create_response({"difficulty": difficulty})
    except Exception as e:
        log.error("difficulty_assess_error", exc_info=e)
        raise HTTPException(status_code=500, detail="Failed to assess difficulty")


@router.post("/difficulty/assess")
async def assess_difficulty_compat(payload: dict):
    """Compatibility endpoint used by orchestration-service (payload keys may be resumeData/jobDescription)."""
    # normalize payload keys
    resume_data = payload.get("resumeData") or payload.get("resume_data") or {}
    job_description = payload.get("jobDescription") or payload.get("job_description") or {}
    return await assess_difficulty({"resume_data": resume_data, "job_description": job_description})


@router.post("/questions/generate")
async def generate_question_compat(payload: dict):
    resume_data = payload.get("resumeData") or payload.get("resume_data") or {}
    job_description = payload.get("jobDescription") or payload.get("job_description") or {}
    difficulty = payload.get("difficulty") or payload.get("level") or "medium"
    question_number = payload.get("questionNumber") or payload.get("question_number") or 1
    previous_questions = payload.get("previousQuestions") or payload.get("previous_questions") or []
    interview_id = payload.get("interviewId") or payload.get("interview_id")
    candidate_id = payload.get("candidateId") or payload.get("candidate_id")

    return await generate_question({
        "resume_data": resume_data,
        "job_description": job_description,
        "difficulty": difficulty,
        "question_number": question_number,
        "previous_questions": previous_questions,
        "interview_id": interview_id,
        "candidate_id": candidate_id,
    })


@router.get("/inspiration")
async def get_inspiration(difficulty: str = "medium", topics: str = "", skills: str = ""):
    """Get inspiration examples (scraped) for questions. `topics` and `skills` are comma-separated strings."""
    try:
        topics_list = [t.strip() for t in topics.split(",") if t.strip()]
        skills_list = [s.strip() for s in skills.split(",") if s.strip()]

        inspiration = await web_scraper.get_question_inspiration(difficulty=difficulty, topics=topics_list, skills=skills_list)
        return create_response(inspiration)
    except Exception as e:
        log.error("inspiration_error", exc_info=e)
        raise HTTPException(status_code=500, detail="Failed to fetch inspiration")