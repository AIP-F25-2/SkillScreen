# Coding Interview Service

A separate microservice for conducting coding interviews with LLM-powered question generation.

## Features

- **LLM-Powered Question Generation**: Automatically generates coding questions based on:
  - Resume analysis (skills, experience level)
  - Job description and requirements
  - Difficulty assessment based on candidate experience
  - Inspiration from LeetCode, GeeksforGeeks, StackOverflow, Kaggle

- **LeetCode/GeeksforGeeks-Style UI**: Modern code editor interface similar to popular coding platforms

- **Automated Workflow**: Uses LLM to automate:
  - Question generation
  - Difficulty assessment
  - Test case generation
  - Solution validation
  - Code execution and testing

## Port

Runs on **port 8001** (separate from main SkillScreen service on 8000)

## API Endpoints

- `POST /api/coding-interview/start` - Start a new coding interview session
- `GET /api/coding-interview/sessions/{session_id}` - Get session details
- `POST /api/coding-interview/sessions/{session_id}/submit-code` - Submit code solution
- `GET /api/coding-interview/sessions/{session_id}/questions` - Get current question
- `POST /api/coding-interview/sessions/{session_id}/next-question` - Get next question

## Setup

```bash
cd backend/coding-interview-service
pip install -r requirements.txt
python -m uvicorn app:app --host 0.0.0.0 --port 8001 --reload
```

## Frontend

Streamlit UI available at `frontend/coding-interview-app/`

