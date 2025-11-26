"""
Coding Interview Service - FastAPI Application
Separate microservice for conducting coding interviews with LLM-powered question generation
Runs on port 8001
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Body, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
import os
import sys
from datetime import datetime, timezone
import uuid

# Add paths for imports - MUST be done before any imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
text_service_path = os.path.join(project_root, 'backend', 'text-service')

# Normalize paths
current_dir = os.path.normpath(os.path.abspath(current_dir))
text_service_path = os.path.normpath(os.path.abspath(text_service_path))

# Add to path - current_dir FIRST so local modules are found
# Remove any existing entries to avoid duplicates
sys.path = [p for p in sys.path if p != current_dir and p != text_service_path]
sys.path.insert(0, current_dir)
sys.path.insert(0, text_service_path)

# Change working directory to current_dir
os.chdir(current_dir)

# Verify services directory exists
services_path = os.path.join(current_dir, 'services')
if not os.path.exists(services_path):
    raise ImportError(f"Services directory not found at: {services_path}")

# Import logger first (this will set up paths for text-service)
from utils.logger import log_info, log_error, log_warning

log_info(f"Current directory: {current_dir}")
log_info(f"Services path: {services_path}")
log_info(f"Services exists: {os.path.exists(services_path)}")
log_info(f"Python path (first 3): {sys.path[:3]}")

# Import services using direct file imports to avoid path issues
import importlib.util

# Import coding_question_generator
coding_question_gen_path = os.path.join(current_dir, 'services', 'coding_question_generator.py')
spec = importlib.util.spec_from_file_location("coding_question_generator", coding_question_gen_path)
coding_question_gen_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coding_question_gen_module)
CodingQuestionGenerator = coding_question_gen_module.CodingQuestionGenerator

# Import difficulty_assessor
difficulty_assessor_path = os.path.join(current_dir, 'services', 'difficulty_assessor.py')
spec = importlib.util.spec_from_file_location("difficulty_assessor", difficulty_assessor_path)
difficulty_assessor_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(difficulty_assessor_module)
DifficultyAssessor = difficulty_assessor_module.DifficultyAssessor

# Import code_execution_service
code_execution_path = os.path.join(current_dir, 'services', 'code_execution_service.py')
spec = importlib.util.spec_from_file_location("code_execution_service", code_execution_path)
code_execution_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(code_execution_module)
CodeExecutionService = code_execution_module.CodeExecutionService

# Import schemas - handle importlib loading
try:
    from schemas.coding_interview_schemas import (
        CodingInterviewStart,
        CodingSessionResponse,
        CodeSubmission,
        SubmissionResponse
    )
except ImportError:
    # Fallback for importlib loading
    schemas_path = os.path.join(current_dir, 'schemas', 'coding_interview_schemas.py')
    if os.path.exists(schemas_path):
        spec = importlib.util.spec_from_file_location("coding_interview_schemas", schemas_path)
        schemas_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(schemas_module)
        CodingInterviewStart = schemas_module.CodingInterviewStart
        CodingSessionResponse = schemas_module.CodingSessionResponse
        CodeSubmission = schemas_module.CodeSubmission
        SubmissionResponse = schemas_module.SubmissionResponse
    else:
        raise ImportError(f"Could not find coding_interview_schemas.py at {schemas_path}")

# Initialize FastAPI app
app = FastAPI(
    title="Coding Interview Service",
    description="LLM-powered coding interview service with automated question generation",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
question_generator = CodingQuestionGenerator()
difficulty_assessor = DifficultyAssessor()
code_executor = CodeExecutionService()

# In-memory storage for sessions (can be moved to database)
coding_sessions = {}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Coding Interview Service",
        "version": "1.0.0",
        "status": "active",
        "port": 8001,
        "docs": "/api/docs"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "question_generator": "active",
            "difficulty_assessor": "active",
            "code_executor": "active"
        }
    }

@app.post("/api/coding-interview/start", response_model=CodingSessionResponse)
async def start_coding_interview(
    resume_data: Dict[str, Any] = Body(...),
    job_description: Dict[str, Any] = Body(...),
    num_questions: int = Body(5, ge=1, le=15)
):
    """
    Start a new coding interview session
    
    Args:
        resume_data: Parsed resume information (skills, experience, etc.)
        job_description: Job description and requirements
        num_questions: Number of coding questions to generate (1-15)
    
    Returns:
        CodingSessionResponse with session_id and first question
    """
    try:
        session_id = str(uuid.uuid4())
        
        log_info(f"[CODING INTERVIEW] Starting session {session_id}")
        
        # Assess difficulty based on resume and job requirements
        difficulty = await difficulty_assessor.assess_difficulty(
            resume_data=resume_data,
            job_description=job_description
        )
        
        log_info(f"[CODING INTERVIEW] Assessed base difficulty: {difficulty}")
        
        # Generate difficulty distribution FIRST, then use it for first question
        # For small numbers, distribute evenly
        import random
        
        if num_questions <= 3:
            # For 1-3 questions, distribute evenly: 1 easy, 1 medium, 1 hard (if 3)
            difficulties = ["easy", "medium", "hard"]
            difficulty_distribution = difficulties[:num_questions]
        elif num_questions <= 6:
            # For 4-6 questions: 2 easy, 2 medium, rest hard
            easy_count = 2
            medium_count = 2
            hard_count = num_questions - easy_count - medium_count
            difficulty_distribution = (["easy"] * easy_count + 
                                      ["medium"] * medium_count + 
                                      ["hard"] * hard_count)
        else:
            # For 7+ questions: 2-3 of each
            easy_count = min(3, max(2, num_questions // 3))
            medium_count = min(3, max(2, num_questions // 3))
            hard_count = num_questions - easy_count - medium_count
            
            difficulty_distribution = (["easy"] * easy_count + 
                                      ["medium"] * medium_count + 
                                      ["hard"] * hard_count)
        
        # Shuffle for variety
        random.shuffle(difficulty_distribution)
        
        log_info(f"[DIFFICULTY] Distribution for {num_questions} questions: {difficulty_distribution}")
        
        # Generate first question using first difficulty from distribution
        first_question_difficulty = difficulty_distribution[0]
        question = await question_generator.generate_question(
            resume_data=resume_data,
            job_description=job_description,
            difficulty=first_question_difficulty,
            question_number=1,
            previous_questions=[]
        )
        
        # Create session
        session = {
            "session_id": session_id,
            "resume_data": resume_data,
            "job_description": job_description,
            "base_difficulty": difficulty,  # Keep for reference
            "difficulty_distribution": difficulty_distribution,
            "num_questions": num_questions,
            "current_question": 1,
            "questions": [question],
            "submissions": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "active"
        }
        
        coding_sessions[session_id] = session
        
        log_info(f"[CODING INTERVIEW] Session {session_id} created with {num_questions} questions")
        
        return CodingSessionResponse(
            session_id=session_id,
            question=question,
            total_questions=num_questions,
            current_question=1,
            difficulty=difficulty
        )
        
    except Exception as e:
        log_error(f"Error starting coding interview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start coding interview: {str(e)}")

@app.post("/api/coding-interview/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    """Upload and parse resume file"""
    try:
        # Import resume parser from text-service
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'text-service'))
        from utils.resume_parser import ResumeParser
        
        parser = ResumeParser()
        
        # Read file content and create file-like object
        content = await file.read()
        import io
        file_obj = io.BytesIO(content)
        file_obj.name = file.filename
        file_obj.seek(0)
        
        # Parse resume
        parsed_data = parser.parse_resume_from_pdf(file_obj)
        
        log_info(f"[RESUME] Parsed resume: {parsed_data.get('name', 'Unknown')}")
        
        return {
            "success": True,
            "filename": file.filename,
            "parsed_data": parsed_data
        }
        
    except Exception as e:
        log_error(f"Error parsing resume: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to parse resume: {str(e)}")

@app.post("/api/coding-interview/upload-job-description")
async def upload_job_description(
    job_title: str = Form(...),
    company: str = Form(""),
    description: str = Form(...),
    requirements: str = Form("")
):
    """Upload job description"""
    try:
        job_data = {
            "job_title": job_title,
            "company": company,
            "description": description,
            "requirements": requirements,
            "uploaded_at": datetime.now(timezone.utc).isoformat()
        }
        
        log_info(f"[JOB] Job description uploaded: {job_title}")
        
        return {
            "success": True,
            "job_data": job_data
        }
        
    except Exception as e:
        log_error(f"Error uploading job description: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload job description: {str(e)}")

@app.get("/api/coding-interview/sessions/{session_id}")
async def get_session(session_id: str):
    """Get coding interview session details"""
    if session_id not in coding_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return coding_sessions[session_id]

@app.get("/api/coding-interview/sessions/{session_id}/questions/{question_number}")
async def get_question(session_id: str, question_number: int):
    """Get a specific question from the session"""
    if session_id not in coding_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = coding_sessions[session_id]
    
    if question_number < 1 or question_number > len(session["questions"]):
        raise HTTPException(status_code=404, detail="Question not found")
    
    return {
        "question": session["questions"][question_number - 1],
        "question_number": question_number,
        "total_questions": session["num_questions"]
    }

@app.post("/api/coding-interview/sessions/{session_id}/next-question")
async def get_next_question(session_id: str):
    """Generate and get the next question"""
    if session_id not in coding_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = coding_sessions[session_id]
    
    if session["current_question"] >= session["num_questions"]:
        return {
            "message": "All questions completed",
            "session_complete": True
        }
    
    try:
        # Generate next question
        next_question_num = session["current_question"] + 1
        
        log_info(f"[NEXT QUESTION] Generating question {next_question_num} of {session['num_questions']}")
        
        # Get difficulty for this question from distribution
        difficulty_dist = session.get("difficulty_distribution", [])
        log_info(f"[NEXT QUESTION] Difficulty distribution: {difficulty_dist}")
        
        if next_question_num <= len(difficulty_dist):
            question_difficulty = difficulty_dist[next_question_num - 1]
            log_info(f"[NEXT QUESTION] Using difficulty from distribution: {question_difficulty}")
        else:
            # Fallback to base difficulty
            question_difficulty = session.get("base_difficulty", "medium")
            log_warning(f"[NEXT QUESTION] Distribution exhausted, using fallback: {question_difficulty}")
        
        question = await question_generator.generate_question(
            resume_data=session["resume_data"],
            job_description=session["job_description"],
            difficulty=question_difficulty,
            question_number=next_question_num,
            previous_questions=[q["title"] for q in session["questions"]]
        )
        
        # Add to session
        session["questions"].append(question)
        session["current_question"] = next_question_num
        
        log_info(f"[NEXT QUESTION] Question {next_question_num} generated successfully. Total questions in session: {len(session['questions'])}")
        
        return {
            "question": question,
            "question_number": next_question_num,
            "total_questions": session["num_questions"]
        }
        
    except Exception as e:
        log_error(f"Error generating next question: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate next question: {str(e)}")

@app.post("/api/coding-interview/sessions/{session_id}/run-code")
async def run_code(
    session_id: str,
    submission: CodeSubmission
):
    """Run code without test cases (just execute and show output)"""
    if session_id not in coding_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        # For Python, add execution code if function exists but isn't called
        code_to_run = submission.code
        if submission.language == "python":
            # Check if code has a function but no execution
            has_function = "def " in code_to_run
            has_execution = any(keyword in code_to_run for keyword in ['print(', 'solution(', 'main('])
            
            if has_function and not has_execution:
                # Try to detect function name and add execution
                import re
                func_match = re.search(r'def\s+(\w+)\s*\(', code_to_run)
                if func_match:
                    func_name = func_match.group(1)
                    # Add execution with sample or just call
                    code_to_run = f"""
{code_to_run}

# Execute function
import json
try:
    if '{func_name}' in globals():
        import inspect
        sig = inspect.signature({func_name})
        param_count = len(sig.parameters)
        
        if param_count == 0:
            result = {func_name}()
            if result is not None:
                if isinstance(result, (dict, list)):
                    print(json.dumps(result, sort_keys=True))
                else:
                    print(result)
            else:
                print("Function executed successfully (returned None)")
        else:
            print(f"Function '{func_name}' requires {{param_count}} parameter(s).")
            print("Use the Submit button to test with actual test cases.")
    else:
        print("No function found. Make sure your function is defined correctly.")
except Exception as e:
    print(f"Error: {{e}}")
    import traceback
    traceback.print_exc()
"""
        
        # Execute code without test cases
        execution_result = await code_executor.execute_code(
            code=code_to_run,
            language=submission.language,
            test_cases=None  # No test cases for run
        )
        
        return {
            "success": True,
            "execution_result": execution_result
        }
        
    except Exception as e:
        log_error(f"Error running code: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to run code: {str(e)}")

@app.post("/api/coding-interview/sessions/{session_id}/submit-code")
async def submit_code(
    session_id: str,
    submission: CodeSubmission
):
    """Submit code solution for current question"""
    if session_id not in coding_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = coding_sessions[session_id]
    current_question = session["questions"][session["current_question"] - 1]
    
    try:
        # Parse test cases - convert JSON strings to proper format
        test_cases = current_question.get("test_cases", [])
        processed_test_cases = []
        
        for tc in test_cases:
            if isinstance(tc, dict):
                # If input/output are JSON strings, parse them
                input_val = tc.get("input", "")
                expected_output = tc.get("expected_output", "")
                
                # Try to parse if they're JSON strings
                try:
                    if isinstance(input_val, str) and (input_val.startswith('{') or input_val.startswith('[')):
                        input_val = json.loads(input_val)
                except:
                    pass
                
                try:
                    if isinstance(expected_output, str) and (expected_output.startswith('{') or expected_output.startswith('[')):
                        expected_output = json.loads(expected_output)
                except:
                    pass
                
                processed_test_cases.append({
                    "input": input_val,
                    "expected_output": expected_output
                })
            else:
                processed_test_cases.append(tc)
        
        # Execute code with test cases
        execution_result = await code_executor.execute_code(
            code=submission.code,
            language=submission.language,
            test_cases=processed_test_cases
        )
        
        # Store submission
        submission_record = {
            "question_number": session["current_question"],
            "code": submission.code,
            "language": submission.language,
            "execution_result": execution_result,
            "submitted_at": datetime.now(timezone.utc).isoformat()
        }
        
        session["submissions"].append(submission_record)
        
        return {
            "success": True,
            "execution_result": execution_result,
            "submission": submission_record
        }
        
    except Exception as e:
        log_error(f"Error submitting code: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit code: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )

