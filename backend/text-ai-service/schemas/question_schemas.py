from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class QuestionGenerationRequest(BaseModel):
    """Question generation request schema"""
    interview_id: str
    candidate_id: str
    job_position_id: str
    num_questions: Optional[int] = 5


class QuestionEvaluationRequest(BaseModel):
    """Question evaluation request schema"""
    question_id: Optional[str] = None  # Deprecated, use session_id
    session_id: Optional[str] = None
    response_text: str
    expected_answer_points: Optional[List[str]] = None


class EvaluationResponse(BaseModel):
    """Evaluation response schema"""
    evaluation_id: str
    question_id: str
    score: int
    feedback: str
    keywords_matched: List[str]
    strengths: List[str]
    areas_for_improvement: List[str]

    class Config:
        from_attributes = True


class InterviewEvaluationResponse(BaseModel):
    """Overall interview evaluation schema"""
    interview_id: str
    total_evaluations: int
    overall_score: float
    evaluations: List[Dict[str, Any]]

    class Config:
        from_attributes = True
