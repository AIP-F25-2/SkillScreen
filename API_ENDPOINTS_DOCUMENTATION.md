# SkillScreen API Endpoints Documentation

**Base URL:** `http://localhost:8000`  
**API Version:** 2.0.0  
**Documentation:** `http://localhost:8000/docs` (Swagger UI)  
**ReDoc:** `http://localhost:8000/redoc`

---

## Table of Contents

1. [Health & Status](#health--status)
2. [Candidates](#candidates)
3. [Jobs](#jobs)
4. [Interviews](#interviews)
5. [Code Execution](#code-execution)
6. [Statistics](#statistics)

---

## Health & Status

### GET `/`
**Description:** Root endpoint with API information

**Response:**
```json
{
  "message": "SkillScreen API is running!",
  "version": "2.0.0",
  "status": "healthy",
  "timestamp": "2024-12-15T10:30:00",
  "endpoints": {
    "candidates": "/candidates",
    "jobs": "/jobs",
    "interviews": "/interviews",
    "docs": "/docs"
  }
}
```

---

### GET `/health`
**Description:** Health check endpoint with service status

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-12-15T10:30:00",
  "database": "postgresql" | "in-memory" | "postgresql-error: <error>",
  "services": ["interview", "nlp", "anti-cheating", "code-execution", "database"]
}
```

**Used by Frontend:**
- Streamlit frontend checks this endpoint on startup to verify backend availability

---

## Candidates

### POST `/candidates`
**Description:** Create a new candidate

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john.doe@example.com",
  "resume_text": "Optional resume text...",
  "experience_years": 5,
  "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"]
}
```

**Response:**
```json
{
  "candidate_id": "candidate_1",
  "message": "Candidate created successfully"
}
```

**Used by Frontend:**
- Called after resume parsing in `streamlit_frontend.py` via `create_candidate()` function

---

### GET `/candidates`
**Description:** List all candidates

**Response:**
```json
{
  "candidates": [
    {
      "id": "candidate_1",
      "name": "John Doe",
      "email": "john.doe@example.com",
      "resume_text": "...",
      "experience_years": 5,
      "skills": ["Python", "FastAPI"],
      "created_at": "2024-12-15T10:30:00"
    }
  ],
  "total": 1
}
```

---

### GET `/candidates/{candidate_id}`
**Description:** Get candidate details by ID

**Path Parameters:**
- `candidate_id` (string): Candidate identifier

**Response:**
```json
{
  "id": "candidate_1",
  "name": "John Doe",
  "email": "john.doe@example.com",
  "resume_text": "...",
  "experience_years": 5,
  "skills": ["Python", "FastAPI"],
  "created_at": "2024-12-15T10:30:00"
}
```

**Error Response (404):**
```json
{
  "detail": "Candidate not found"
}
```

---

## Jobs

### POST `/jobs`
**Description:** Create a new job posting

**Request Body:**
```json
{
  "title": "Senior Software Engineer",
  "company": "Tech Corp",
  "description": "We are looking for an experienced software engineer...",
  "required_skills": ["Python", "FastAPI", "PostgreSQL"],
  "experience_level": "mid" | "senior" | "entry"
}
```

**Response:**
```json
{
  "job_id": "job_1",
  "message": "Job created successfully"
}
```

**Used by Frontend:**
- Called after job description parsing in `streamlit_frontend.py` via `create_job()` function

---

### GET `/jobs`
**Description:** List all jobs

**Response:**
```json
{
  "jobs": [
    {
      "id": "job_1",
      "title": "Senior Software Engineer",
      "company": "Tech Corp",
      "description": "...",
      "required_skills": ["Python", "FastAPI"],
      "experience_level": "mid",
      "created_at": "2024-12-15T10:30:00"
    }
  ],
  "total": 1
}
```

---

### GET `/jobs/{job_id}`
**Description:** Get job details by ID

**Path Parameters:**
- `job_id` (string): Job identifier

**Response:**
```json
{
  "id": "job_1",
  "title": "Senior Software Engineer",
  "company": "Tech Corp",
  "description": "...",
  "required_skills": ["Python", "FastAPI"],
  "experience_level": "mid",
  "created_at": "2024-12-15T10:30:00"
}
```

**Error Response (404):**
```json
{
  "detail": "Job not found"
}
```

---

## Interviews

### POST `/interviews/start`
**Description:** Start a new interview session

**Request Body:**
```json
{
  "candidate_id": "candidate_1",
  "job_id": "job_1"
}
```

**Response:**
```json
{
  "session_id": "session_1",
  "message": "Interview started for John Doe",
  "first_question": "Tell me about yourself and your experience with this role.",
  "status": "started"
}
```

**Used by Frontend:**
- Called via `start_interview()` function in `streamlit_frontend.py`
- Stores `session_id` in session state for subsequent requests

**Error Responses:**
- `404`: Candidate or Job not found

---

### GET `/interviews/{session_id}`
**Description:** Get interview session details

**Path Parameters:**
- `session_id` (string): Interview session identifier

**Response:**
```json
{
  "session_id": "session_1",
  "candidate_id": "candidate_1",
  "job_id": "job_1",
  "candidate_name": "John Doe",
  "job_title": "Senior Software Engineer",
  "status": "active" | "completed",
  "start_time": "2024-12-15T10:30:00",
  "end_time": "2024-12-15T10:45:00",
  "questions_asked": 5,
  "responses_received": 5,
  "current_question": "What technologies are you most comfortable with?",
  "question_history": ["Question 1", "Question 2", ...],
  "response_history": ["Response 1", "Response 2", ...],
  "total_score": 42.5,
  "duplicate_count": 0,
  "ai_generated_count": 0,
  "violations": []
}
```

**Used by Frontend:**
- Called in `show_interview_interface()` to get current interview status
- Used to display progress and round information

**Error Responses:**
- `404`: Interview session not found

---

### POST `/interviews/{session_id}/respond`
**Description:** Submit candidate response to current question

**Path Parameters:**
- `session_id` (string): Interview session identifier

**Request Body:**
```json
{
  "response_text": "I have 5 years of experience working with Python and FastAPI..."
}
```

**Response (Continue Interview):**
```json
{
  "status": "continue",
  "next_question": "Can you describe a challenging technical problem you solved recently?",
  "question_number": 2,
  "score": 7.5,
  "response_received": "I have 5 years of experience...",
  "warnings": null,
  "duplicate_count": 0,
  "ai_generated_count": 0,
  "candidate_name_from_intro": "John Doe"
}
```

**Response (Interview Completed):**
```json
{
  "status": "completed",
  "message": "Interview completed",
  "summary": {
    "total_questions": 9,
    "total_responses": 9,
    "average_score": 7.2,
    "recommendation": "Strong Consider" | "Do Not Hire"
  }
}
```

**Response (Warnings - Continue):**
```json
{
  "status": "continue",
  "next_question": "...",
  "warnings": [
    "⚠️ WARNING: Duplicate response detected. Please provide unique answers.",
    "⚠️ WARNING: AI-generated content detected. Please provide original responses."
  ],
  "duplicate_count": 1,
  "ai_generated_count": 0
}
```

**Used by Frontend:**
- Called via `submit_response()` function in `streamlit_frontend.py`
- Handles response submission, shows warnings, and updates chat interface

**Error Responses:**
- `404`: Interview session not found
- `400`: Interview session is not active

---

### GET `/interviews/{session_id}/summary`
**Description:** Get interview summary (only available after completion)

**Path Parameters:**
- `session_id` (string): Interview session identifier

**Response:**
```json
{
  "session_id": "session_1",
  "candidate_name": "John Doe",
  "job_title": "Senior Software Engineer",
  "total_questions": 9,
  "total_responses": 9,
  "overall_score": 7.2,
  "recommendation": "Strong Consider",
  "summary": "Interview completed for John Doe for Senior Software Engineer position. Average score: 7.20/10.",
  "strengths": [
    "Good communication",
    "Relevant experience"
  ],
  "areas_for_improvement": [
    "Could provide more specific examples"
  ],
  "detailed_assessment": {
    "technical_skills": 7.2,
    "communication": 7.7,
    "cultural_fit": 7.0
  },
  "violations_analysis": {
    "funny_analysis": {
      "title": "🎉 Clean Interview!",
      "message": "Congratulations! You provided original, authentic responses...",
      "emoji": "🌟",
      "fun_fact": "You're the kind of candidate who brings their own personality to interviews!",
      "violation_summary": {
        "duplicate_responses": 0,
        "ai_generated_responses": 0,
        "total_violations": 0
      }
    },
    "violations": [],
    "violation_count": 0,
    "duplicate_count": 0,
    "ai_generated_count": 0
  }
}
```

**Used by Frontend:**
- Called via `get_interview_summary()` function in `streamlit_frontend.py`
- Displays in `show_interview_summary()` with scores, strengths, and improvements

**Error Responses:**
- `404`: Interview session not found
- `400`: Interview is not completed yet

---

### GET `/interviews/{session_id}/ai-summary`
**Description:** Get AI-generated human-like interview summary

**Path Parameters:**
- `session_id` (string): Interview session identifier

**Response:**
```json
{
  "session_id": "session_1",
  "candidate_name": "John Doe",
  "job_title": "Senior Software Engineer",
  "ai_summary": "Dear John Doe,\n\nThank you for taking the time to interview for the Senior Software Engineer position...",
  "overall_score": 7.2,
  "recommendation": "Strong Consider"
}
```

**Used by Frontend:**
- Called via `get_ai_summary()` function in `streamlit_frontend.py`
- Displays in interview summary section as "AI Analysis"

**Error Responses:**
- `404`: Interview session not found
- `400`: Interview is not completed yet

---

### GET `/interviews`
**Description:** List all interview sessions

**Response:**
```json
{
  "interviews": [
    {
      "session_id": "session_1",
      "candidate_id": "candidate_1",
      "job_id": "job_1",
      "status": "completed",
      ...
    }
  ],
  "total": 1
}
```

---

### DELETE `/interviews/{session_id}`
**Description:** Delete interview session

**Path Parameters:**
- `session_id` (string): Interview session identifier

**Response:**
```json
{
  "message": "Interview session deleted successfully"
}
```

**Error Responses:**
- `404`: Interview session not found

---

## Code Execution

### POST `/api/code/execute`
**Description:** Execute code in sandboxed environment

**Request Body:**
```json
{
  "code": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\nprint(fibonacci(10))",
  "language": "python",
  "test_cases": [],
  "timeout": 10
}
```

**Response:**
```json
{
  "success": true,
  "output": "55",
  "error": null,
  "execution_time": 0.02,
  "memory_usage": "8MB"
}
```

**Error Response:**
```json
{
  "success": false,
  "output": "",
  "error": "SyntaxError: invalid syntax",
  "execution_time": 0.0,
  "memory_usage": "0MB"
}
```

**Used by Frontend:**
- Called in `code_editor_section()` of `streamlit_frontend.py`
- Used for technical assessments with code execution

**Error Responses:**
- `503`: Code execution service not available
- `400`: Code cannot be empty
- `500`: Code execution failed

---

### GET `/api/code/languages`
**Description:** Get list of supported programming languages

**Response:**
```json
{
  "languages": ["python", "javascript", "java", "cpp", "sql"],
  "available": true
}
```

**Error Responses:**
- `503`: Code execution service not available

---

### POST `/api/code/question`
**Description:** Create a technical coding question

**Request Body:**
```json
{
  "language": "python",
  "difficulty": "medium",
  "topic": "algorithms"
}
```

**Response:**
```json
{
  "question": "Write a function to find the maximum element in a binary tree...",
  "language": "python",
  "difficulty": "medium",
  "topic": "algorithms"
}
```

**Used by Frontend:**
- Called in `code_editor_section()` via "Get Question" button

**Error Responses:**
- `503`: Code execution service not available
- `500`: Failed to create question

---

### GET `/api/code/result/{execution_id}`
**Description:** Get execution result by ID

**Path Parameters:**
- `execution_id` (string): Code execution identifier

**Response:**
```json
{
  "execution_id": "exec_123",
  "code": "...",
  "language": "python",
  "success": true,
  "output": "55",
  "error": null,
  "execution_time": 0.02
}
```

**Error Responses:**
- `503`: Code execution service not available
- `404`: Execution result not found

---

## Statistics

### GET `/stats`
**Description:** Get system statistics

**Response:**
```json
{
  "total_candidates": 10,
  "total_jobs": 5,
  "total_interviews": 25,
  "active_interviews": 3,
  "completed_interviews": 22
}
```

---

## Frontend Integration Summary

### Streamlit Frontend (`streamlit_frontend.py`)

**Functions that call API endpoints:**

1. **`check_api_health()`** → `GET /health`
   - Checks backend availability on startup

2. **`create_candidate(resume_data)`** → `POST /candidates`
   - Creates candidate after resume parsing

3. **`create_job(job_data)`** → `POST /jobs`
   - Creates job after job description parsing

4. **`start_interview(candidate_id, job_id)`** → `POST /interviews/start`
   - Starts interview session

5. **`submit_response(session_id, response_text)`** → `POST /interviews/{session_id}/respond`
   - Submits candidate response

6. **`get_interview_summary(session_id)`** → `GET /interviews/{session_id}/summary`
   - Gets interview summary after completion

7. **`get_ai_summary(session_id)`** → `GET /interviews/{session_id}/ai-summary`
   - Gets AI-generated summary

8. **`make_api_request("GET", f"/interviews/{session_id}")`** → `GET /interviews/{session_id}`
   - Gets current interview status

9. **`make_api_request("POST", "/api/code/execute", {...})`** → `POST /api/code/execute`
   - Executes code in technical assessments

10. **`make_api_request("GET", "/api/code/question")`** → `POST /api/code/question`
    - Gets technical coding question

---

## Request/Response Formats

### Common Headers
```
Content-Type: application/json
Accept: application/json
```

### Error Response Format
```json
{
  "detail": "Error message description"
}
```

### Status Codes
- `200`: Success
- `400`: Bad Request (invalid input, session not active, etc.)
- `404`: Not Found (resource doesn't exist)
- `500`: Internal Server Error
- `503`: Service Unavailable (service not available)

---

## Authentication

**Current Status:** No authentication required (development/testing mode)

**Future:** JWT token-based authentication will be added for production:
```
Authorization: Bearer <jwt_token>
```

---

## CORS Configuration

The API is configured to accept requests from any origin (`allow_origins=["*"]`). For production, this should be restricted to specific domains.

---

## Database Integration

The API supports both:
- **In-memory storage** (default for testing)
- **PostgreSQL** (Azure PostgreSQL when available)

Database status is reported in `/health` endpoint.

---

## Rate Limiting

**Current Status:** No rate limiting implemented

**Future:** Rate limiting will be added for production to prevent abuse.

---

## Notes for Full Stack Team

1. **Base URL Configuration:**
   - Currently hardcoded in Streamlit: `API_BASE_URL = "http://localhost:8000"`
   - Consider making this configurable via environment variables

2. **Error Handling:**
   - All API calls should handle connection errors gracefully
   - Frontend shows appropriate error messages when backend is unavailable

3. **Session Management:**
   - Frontend stores `session_id` in Streamlit session state
   - Session state persists across page reruns

4. **Async Operations:**
   - Backend uses async/await for I/O operations
   - Frontend uses synchronous requests (requests library)

5. **Anti-Cheating Detection:**
   - Warnings are returned in response but don't terminate interview
   - Violations are tracked and reported in summary

6. **Interview Flow:**
   - Interview continues until 9 responses are received
   - Status changes from "active" to "completed" automatically

7. **Code Execution:**
   - Requires code execution service to be available
   - Sandboxed environment with resource limits
   - Supports multiple programming languages

---

**Last Updated:** December 2024  
**API Version:** 2.0.0  
**Contact:** [Your Team Contact Information]

