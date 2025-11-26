"""
Schemas for Coding Interview Service
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

class CodingInterviewStart(BaseModel):
    """Request to start a coding interview"""
    resume_data: Dict[str, Any]
    job_description: Dict[str, Any]
    num_questions: int = Field(default=5, ge=1, le=15)

class QuestionExample(BaseModel):
    """Example input/output for a question"""
    input: Any  # Can be string, dict, list, etc.
    output: Any  # Can be string, dict, list, etc.
    explanation: Optional[str] = None

class TestCase(BaseModel):
    """Test case for a question"""
    input: Any  # Can be string, dict, list, etc.
    expected_output: Any  # Can be string, dict, list, etc.

class CodingQuestion(BaseModel):
    """Coding question structure"""
    title: str
    description: str
    difficulty: str
    examples: List[QuestionExample] = []
    constraints: List[str] = []
    test_cases: List[TestCase] = []
    expected_outputs: List[Any] = []  # Can be strings, dicts, lists, etc.
    hints: List[str] = []
    topics: List[str] = []
    time_limit_minutes: int = 30
    code_templates: Dict[str, str] = {}

class CodingSessionResponse(BaseModel):
    """Response when starting a coding interview"""
    session_id: str
    question: CodingQuestion
    total_questions: int
    current_question: int
    difficulty: str

class CodeSubmission(BaseModel):
    """Code submission for a question"""
    code: str
    language: str = "python"

class SubmissionResponse(BaseModel):
    """Response to code submission"""
    success: bool
    execution_result: Dict[str, Any]
    test_results: List[Dict[str, Any]]
    score: float

