# Automatic Data Storage

## Overview

**Yes, data is automatically uploaded to the database when an interview is completed!** You don't need to run anything manually.

## What Gets Stored Automatically

When a candidate submits a response via the `/api/interviews/{session_id}/respond` endpoint, the following happens automatically:

### 1. Interview Session Data (`interview_sessions` table)
- ✅ **Automatically created** when a question is asked
- ✅ **Automatically updated** with candidate response when they submit
- Stores:
  - `question_id`, `question_text`, `question_type`
  - `candidate_response` (the actual response text)
  - `response_duration` (time taken to respond)
  - `started_at`, `completed_at` timestamps
  - `session_metadata` (optional JSON data)

### 2. AI Analysis Data (`ai_analysis` table)
- ✅ **Automatically stored** for every response
- Stores:
  - `raw_results` (JSONB) - Contains analysis data (NOT the response text):
    - Behavioral analysis (behavior type, anomaly score, engagement trends)
    - Quality prediction (predicted score, confidence, feature importance)
    - Bias detection (if applicable)
    - Metadata (question number, response length, timestamps)
  - `confidence_score` (0.0-1.0) - Final weighted score
  - `processing_time` (milliseconds)
  - Links to `interview_id` and `session_id`

### 3. Response Data (`responses` table)
- ✅ **Automatically stored** with NLP evaluation scores
- Stores scores for: relevance, technical accuracy, communication, depth, job fit

## How It Works

The automatic storage happens in the `submit_response` endpoint (`fastapi_app.py`):

```python
@app.post("/api/interviews/{session_id}/respond")
async def submit_response(...):
    # 1. Create interview session
    session = db_service.create_interview_session(...)
    
    # 2. Run evaluations (NLP, anti-cheating)
    nlp_evaluation = await nlp_service.evaluate_response(...)
    
    # 3. Complete session with response
    completed_session = db_service.complete_interview_session(...)
    
    # 4. Store response record
    db.add(db_response)
    
    # 5. AUTOMATICALLY store AI analysis
    analysis_result = await interview_service.evaluate_and_store_response_analysis(...)
    # ✅ This stores in ai_analysis table automatically!
    
    # 6. Commit everything
    db.commit()
```

## What You Need to Do

**Nothing!** The storage is completely automatic. Just:

1. **Start your FastAPI server**:
   ```bash
   cd backend/text-service
   uvicorn fastapi_app:app --host 0.0.0.0 --port 8000
   ```

2. **Use the API endpoints** - When candidates submit responses, everything is stored automatically.

## Verification

To verify data is being stored, you can:

### Check Interview Sessions
```sql
SELECT * FROM interview_sessions 
WHERE interview_id = 'your-interview-id'
ORDER BY created_at;
```

### Check AI Analysis
```sql
SELECT 
    id,
    interview_id,
    session_id,
    analysis_type,
    confidence_score,
    raw_results->'behavioral_analysis'->>'behavior_type' as behavior_type,
    raw_results->'quality_prediction'->>'predicted_score' as quality_score,
    processing_time,
    created_at
FROM ai_analysis
WHERE interview_id = 'your-interview-id'
ORDER BY created_at;
```

### Check Candidates
```sql
SELECT * FROM candidates 
WHERE organization_id = 'your-org-id'
ORDER BY created_at DESC;
```

## Error Handling

If AI analysis storage fails (e.g., ML service unavailable), the system will:
- ✅ **Still store** the interview session and response data
- ⚠️ **Log a warning** but continue processing
- ✅ **Not fail** the entire request

This ensures that even if ML services have issues, the core interview data is still saved.

## Manual Storage (If Needed)

If you need to manually trigger storage for existing data, you can use:

```python
from services.interview_service import InterviewService
from database.database import db_manager

async def manually_store_analysis():
    with db_manager.get_session() as db:
        interview_service = InterviewService()
        
        result = await interview_service.evaluate_and_store_response_analysis(
            interview_id="...",
            session_id="...",
            question_text="...",
            response_text="...",
            response_time_seconds=240,
            question_number=1,
            db=db
        )
```

But this is **not necessary** for normal operation - everything happens automatically!

## Summary

✅ **Interview sessions**: Automatically stored  
✅ **AI analysis**: Automatically stored  
✅ **Response data**: Automatically stored  
✅ **No manual steps required**: Just use the API endpoints

The database connection is configured to use Azure PostgreSQL, so all data goes directly to your production database.

