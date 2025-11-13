# from fastapi import APIRouter, HTTPException
# from schemas.interview_questions import StoreQuestionsRequest
# from utils.response import create_response
# from services.interview_questions_service import store_questions_service, get_questions_service

# router = APIRouter()

# @router.post("/{id}/questions")
# def store_questions(id: str, req: StoreQuestionsRequest):
#     try:
#         store_questions_service(id, req.template_id)
#         return create_response({"message": "Questions stored"})
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/{id}/questions")
# def get_questions(id: str):
#     try:
#         result = get_questions_service(id)
#         return create_response(result)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, HTTPException
from utils.response import create_response
from services.interview_questions_service import (
    store_questions_service,
    get_questions_service,
)

router = APIRouter()

# -----------------------------
# POST /interviews/{id}/questions
# -----------------------------
@router.post("/{id}/questions")
def store_questions(id: str):
    """
    Generate interview_sessions entries for this interview
    using the interview's own template_id (no request body needed).
    """
    try:
        store_questions_service(id)
        return create_response({"message": "Questions stored successfully"})
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# GET /interviews/{id}/questions
# -----------------------------
@router.get("/{id}/questions")
def get_questions(id: str):
    try:
        result = get_questions_service(id)
        return create_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

