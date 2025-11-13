# How to Run an Interview Session Test

This guide will help you test that interview data is automatically stored in the database.

## Prerequisites

1. **Install dependencies** (if not already installed):
   ```bash
   cd backend/text-service
   pip install -r requirements_production.txt
   pip install requests  # For test scripts
   ```

2. **Start the FastAPI server**:
   ```bash
   cd backend/text-service
   uvicorn fastapi_app:app --host 0.0.0.0 --port 8000 --reload
   ```

   You should see:
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8000
   INFO:     Application startup complete.
   ```

## Option 1: Quick Test (Recommended)

Run the quick test script for a fast verification:

```bash
cd backend/text-service
python test_interview_quick.py
```

This will:
- ✅ Check API health
- ✅ Create a test candidate
- ✅ Create a test job
- ✅ Start an interview
- ✅ Submit one response
- ✅ Verify data storage

## Option 2: Full Test

Run the complete test script for a comprehensive test:

```bash
cd backend/text-service
python test_interview_session.py
```

This will:
- ✅ Run through multiple questions
- ✅ Submit multiple responses
- ✅ Test the complete interview flow
- ✅ Show detailed verification steps

## Option 3: Manual API Testing

### Using curl:

1. **Health Check**:
   ```bash
   curl http://localhost:8000/api/health
   ```

2. **Create Candidate**:
   ```bash
   curl -X POST http://localhost:8000/api/candidates/ \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Test Candidate",
       "email": "test@example.com",
       "skills": ["Python", "ML"]
     }'
   ```

3. **Create Job**:
   ```bash
   curl -X POST http://localhost:8000/api/jobs/ \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Software Engineer",
       "company": "Test Co",
       "description": "Test position",
       "required_skills": ["Python"]
     }'
   ```

4. **Start Interview** (use IDs from above):
   ```bash
   curl -X POST http://localhost:8000/api/interviews/start \
     -H "Content-Type: application/json" \
     -d '{
       "candidate_id": "YOUR_CANDIDATE_ID",
       "job_id": "YOUR_JOB_ID"
     }'
   ```

5. **Submit Response** (use session_id from above):
   ```bash
   curl -X POST http://localhost:8000/api/interviews/YOUR_SESSION_ID/respond \
     -H "Content-Type: application/json" \
     -d '{
       "response_text": "I am an experienced software engineer...",
       "response_time_seconds": 30
     }'
   ```

### Using the API Docs:

1. Open your browser and go to: `http://localhost:8000/api/docs`
2. Use the interactive Swagger UI to test endpoints
3. Click "Try it out" on any endpoint to test it

## Verify Data in Database

After running the test, verify data was stored:

### 1. Check Interview Sessions

```sql
SELECT 
    id,
    interview_id,
    question_text,
    question_type,
    candidate_response,
    response_duration,
    started_at,
    completed_at,
    created_at
FROM interview_sessions
ORDER BY created_at DESC
LIMIT 10;
```

### 2. Check AI Analysis

```sql
SELECT 
    id,
    interview_id,
    session_id,
    analysis_type,
    confidence_score,
    processing_time,
    raw_results->'behavioral_analysis'->>'behavior_type' as behavior_type,
    raw_results->'quality_prediction'->>'predicted_score' as quality_score,
    created_at
FROM ai_analysis
ORDER BY created_at DESC
LIMIT 10;
```

### 3. Check Responses

```sql
SELECT 
    id,
    interview_id,
    session_id,
    response_text,
    overall_score,
    technical_accuracy_score,
    communication_score,
    created_at
FROM responses
ORDER BY created_at DESC
LIMIT 10;
```

### 4. Check Candidates

```sql
SELECT 
    id,
    full_name,
    email,
    skills,
    created_at
FROM candidates
ORDER BY created_at DESC
LIMIT 10;
```

## Expected Results

After running a test, you should see:

✅ **interview_sessions table**: 
   - At least one row with question_text and candidate_response
   - started_at and completed_at timestamps populated

✅ **ai_analysis table**:
   - At least one row with analysis_type = 'text_analysis'
   - confidence_score between 0.0 and 1.0
   - raw_results JSONB containing behavioral_analysis and quality_prediction data
   - processing_time > 0

✅ **responses table**:
   - At least one row with response_text
   - Scores populated (overall_score, technical_accuracy_score, etc.)

## Troubleshooting

### API not responding
- Check if server is running: `curl http://localhost:8000/api/health`
- Check server logs for errors
- Verify database connection in `database/database.py`

### No data in database
- Check if database connection is working
- Verify Azure PostgreSQL credentials are correct
- Check server logs for database errors
- Ensure `db.commit()` is being called (it should be automatic)

### AI analysis not stored
- Check server logs for ML service errors
- Verify behavioral_analysis_service, quality_prediction_service are working
- Check that `evaluate_and_store_response_analysis` is being called (it should be automatic)

## Next Steps

Once you've verified everything works:

1. ✅ Data is automatically stored when responses are submitted
2. ✅ AI analysis is stored in `ai_analysis` table
3. ✅ Interview sessions are stored in `interview_sessions` table
4. ✅ Responses are stored in `responses` table

You're all set! The system will automatically store all interview data going forward.

