from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class StoreQuestionsRequest(BaseModel):
    template_id: str

class InterviewQuestion(BaseModel):
    id: Optional[str]  # optional in case you want to generate UUID later
    interview_id: str
    question_id: Optional[str] = None
    question_text: str
    question_type: str
    created_at: datetime

class InterviewQuestionsResponse(BaseModel):
    questions: List[InterviewQuestion]
