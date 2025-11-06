from repositories.interviews_repository import get_interview_by_id
from repositories.interview_templates_repository import get_template_by_id
from repositories.interview_questions_repository import (
    store_template_questions_into_sessions,
    get_questions_by_interview_id
)
from fastapi import HTTPException

def store_questions_service(interview_id: str, template_id: str):
    interview = get_interview_by_id(interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    template = get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Optional: enforce org match
    if interview["organization_id"] != template["organization_id"]:
        raise HTTPException(status_code=400, detail="Template does not belong to the same organization")

    store_template_questions_into_sessions(interview_id, template)

def get_questions_service(interview_id: str):
    return get_questions_by_interview_id(interview_id)
