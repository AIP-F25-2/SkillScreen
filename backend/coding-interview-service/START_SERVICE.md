# Starting the Coding Interview Service

## Backend Service (Port 8001)

```bash
cd backend/coding-interview-service
pip install -r requirements.txt
python -m uvicorn app:app --host 0.0.0.0 --port 8001 --reload
```

Or use the app directly:
```bash
python app.py
```

## Frontend UI

```bash
cd frontend/coding-interview-app
streamlit run coding_interview_ui.py --server.port 8502 --server.address 0.0.0.0
```

## Features

1. **LLM-Powered Question Generation**
   - Uses Gemini (primary), Groq, Mistral (fallbacks)
   - Generates questions based on resume and job description
   - Automatically assesses difficulty

2. **Web Scraping Integration**
   - Fetches inspiration from LeetCode, GeeksforGeeks, StackOverflow
   - Uses real question patterns and structures

3. **LeetCode-Style UI**
   - Modern code editor interface
   - Real-time code execution
   - Test case validation
   - Progress tracking

4. **Automated Workflow**
   - Resume parsing
   - Job description analysis
   - Question generation
   - Code execution and testing

## API Endpoints

- `POST /api/coding-interview/start` - Start interview
- `POST /api/coding-interview/upload-resume` - Upload resume
- `POST /api/coding-interview/upload-job-description` - Upload job description
- `GET /api/coding-interview/sessions/{session_id}` - Get session
- `POST /api/coding-interview/sessions/{session_id}/submit-code` - Submit code
- `POST /api/coding-interview/sessions/{session_id}/next-question` - Get next question

## Testing

1. Start the backend service (port 8001)
2. Start the frontend UI (port 8502)
3. Upload resume and job description
4. Start interview
5. Solve coding questions!

