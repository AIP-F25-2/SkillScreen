from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from utils.response import create_response
from services.code_execution_service import CodeExecutionService
from utilities.logger import init_logger

router = APIRouter()

log = init_logger("coding-service")
executor_service = CodeExecutionService()

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