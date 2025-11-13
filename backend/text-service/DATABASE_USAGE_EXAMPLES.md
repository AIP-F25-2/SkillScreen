# Database Usage Examples

This document provides examples of how to store data in the `candidates`, `interview_sessions`, and `ai_analysis` tables.

## Database Connection

The database is configured to connect to Azure PostgreSQL:
- **Host**: `skillscreen-db.postgres.database.azure.com`
- **Port**: `5432`
- **Database**: `postgres`
- **User**: `intervuai`
- **SSL Mode**: `require`

## 1. Storing Candidate Data

### Create a Candidate

```python
from database.database import db_manager
from services.database_service import InterviewDataService

# Get database session
with db_manager.get_session() as db:
    db_service = InterviewDataService(db)
    
    # Create a new candidate
    candidate = db_service.create_candidate(
        organization_id="8a1a77f7-b3ac-49f1-9d47-d1cf0204c217",
        full_name="John Doe",
        email="john.doe@example.com",
        phone="+1-555-123-4567",
        location="Montreal, QC",
        resume_url="https://example.com/resume/john-doe.pdf",
        skills=["Python", "Machine Learning", "PostgreSQL"],
        experience={
            "years": 3,
            "companies": ["TechNova", "DataCore"]
        },
        education={
            "degree": "B.Sc. Computer Science",
            "university": "McGill University"
        },
        projects=[
            {"name": "NLP Chatbot", "description": "..."},
            {"name": "AI Interview Assistant", "description": "..."}
        ]
    )
    
    print(f"Created candidate: {candidate.id}")
```

### Get Candidate by Email

```python
candidate = db_service.get_candidate_by_email("john.doe@example.com")
if candidate:
    print(f"Found candidate: {candidate.full_name}")
```

### Update Candidate

```python
updated_candidate = db_service.update_candidate(
    candidate_id="33333333-3333-4333-8333-333333333333",
    skills=["Python", "Machine Learning", "PostgreSQL", "Docker"],
    experience={"years": 4, "companies": ["TechNova", "DataCore", "NewCompany"]}
)
```

## 2. Storing Interview Session Data

### Create Interview Session

```python
from datetime import datetime, timezone

# Create a new interview session
session = db_service.create_interview_session(
    interview_id="95b53dfd-9416-4f30-9bb8-2a235dcfe838",
    question_id="q1",
    question_text="Tell me about a complex project you built.",
    question_type="behavioral"
)
```

### Complete Interview Session with Response

```python
# Complete the session with candidate response
completed_session = db_service.complete_interview_session(
    session_id=session.id,
    candidate_response="I built a suit of armor in a cave... with a box of scraps!",
    response_duration=240  # seconds
)
```

### Get All Sessions for an Interview

```python
sessions = db_service.get_interview_sessions("95b53dfd-9416-4f30-9bb8-2a235dcfe838")
for session in sessions:
    print(f"Question: {session.question_text}")
    print(f"Response: {session.candidate_response}")
```

## 3. Storing AI Analysis Data

### Using the Comprehensive Evaluation Method

The `evaluate_and_store_response_analysis` method automatically:
- Runs behavioral analysis
- Runs quality prediction
- Runs bias detection (if applicable)
- Stores analysis results in `raw_results` (NOT the actual response text)
- Stores final confidence score in `confidence_score`

```python
from services.interview_service import InterviewService

interview_service = InterviewService()

# Evaluate and store analysis
result = await interview_service.evaluate_and_store_response_analysis(
    interview_id="95b53dfd-9416-4f30-9bb8-2a235dcfe838",
    session_id="78e57fdf-5911-4944-96ff-a55c389defa8",
    question_text="Tell me about a complex project you built.",
    response_text="I built a suit of armor in a cave... with a box of scraps!",
    response_time_seconds=240,
    question_number=1,
    candidate_context={
        "name": "Tony Stark",
        "skills": ["engineering", "robotics", "AI"]
    },
    job_context={
        "title": "Senior Engineer",
        "required_skills": ["engineering", "AI"]
    },
    db=db
)

print(f"Analysis ID: {result['analysis_id']}")
print(f"Confidence Score: {result['confidence_score']}")
print(f"Quality Score: {result['quality_score']}")
```

### Manual AI Analysis Storage

```python
# Store AI analysis manually
analysis = db_service.create_ai_analysis(
    interview_id="95b53dfd-9416-4f30-9bb8-2a235dcfe838",
    session_id="78e57fdf-5911-4944-96ff-a55c389defa8",
    analysis_type="text_analysis",
    service_name="text-service",
    raw_results={
        "behavioral_analysis": {
            "behavior_type": "engaged",
            "anomaly_score": 0.2,
            "engagement_trend": "improving",
            "consistency_score": 0.85,
            "behavioral_flags": [],
            "engagement_score": 0.9
        },
        "quality_prediction": {
            "predicted_score": 8.5,
            "confidence": 0.88,
            "feature_importance": {"response_length": 0.3, "complexity": 0.4},
            "model_used": "ensemble"
        },
        "bias_detection": None,
        "metadata": {
            "question_number": 1,
            "response_length": 150,
            "response_time_seconds": 240,
            "timestamp": "2025-11-12T20:28:16.457652+00:00"
        }
    },
    confidence_score=0.82,  # Final score (0.0-1.0)
    processing_time=84,  # milliseconds
    version="v1.0"
)
```

### Retrieve AI Analysis

```python
# Get all analyses for an interview
analyses = db_service.get_ai_analysis_by_interview("95b53dfd-9416-4f30-9bb8-2a235dcfe838")
for analysis in analyses:
    print(f"Analysis Type: {analysis.analysis_type}")
    print(f"Confidence Score: {analysis.confidence_score}")
    print(f"Raw Results: {analysis.raw_results}")

# Get all analyses for a session
session_analyses = db_service.get_ai_analysis_by_session("78e57fdf-5911-4944-96ff-a55c389defa8")
```

## Complete Workflow Example

```python
from database.database import db_manager
from services.database_service import InterviewDataService
from services.interview_service import InterviewService
import asyncio

async def complete_interview_workflow():
    with db_manager.get_session() as db:
        db_service = InterviewDataService(db)
        interview_service = InterviewService()
        
        # 1. Create or get candidate
        candidate = db_service.get_candidate_by_email("tony.stark@stark.io")
        if not candidate:
            candidate = db_service.create_candidate(
                organization_id="d22e21b7-e936-4495-a78f-4c28bfc9222a",
                full_name="Tony Stark",
                email="tony.stark@stark.io",
                skills=["engineering", "robotics", "AI", "problem-solving"]
            )
        
        # 2. Create interview session
        session = db_service.create_interview_session(
            interview_id="95b53dfd-9416-4f30-9bb8-2a235dcfe838",
            question_id="q1",
            question_text="Tell me about a complex project you built.",
            question_type="behavioral"
        )
        
        # 3. Candidate responds
        response_text = "I built a suit of armor in a cave... with a box of scraps!"
        response_time = 240  # seconds
        
        # 4. Complete the session
        completed_session = db_service.complete_interview_session(
            session_id=str(session.id),
            candidate_response=response_text,
            response_duration=response_time
        )
        
        # 5. Evaluate and store AI analysis
        analysis_result = await interview_service.evaluate_and_store_response_analysis(
            interview_id="95b53dfd-9416-4f30-9bb8-2a235dcfe838",
            session_id=str(session.id),
            question_text=session.question_text,
            response_text=response_text,
            response_time_seconds=response_time,
            question_number=1,
            candidate_context={
                "name": candidate.full_name,
                "skills": candidate.skills or []
            },
            job_context={
                "title": "Senior Engineer",
                "required_skills": ["engineering", "AI"]
            },
            db=db
        )
        
        print(f"✅ Analysis stored with confidence score: {analysis_result['confidence_score']}")
        print(f"✅ Analysis ID: {analysis_result['analysis_id']}")

# Run the workflow
asyncio.run(complete_interview_workflow())
```

## Important Notes

1. **AI Analysis `raw_results`**: This column stores the **analysis data** (behavioral patterns, quality metrics, bias detection results), NOT the actual candidate response text. The response text is stored in `interview_sessions.candidate_response`.

2. **Confidence Score**: The `confidence_score` in `ai_analysis` is a normalized value between 0.0 and 1.0, calculated as a weighted average of:
   - Quality prediction score (60% weight)
   - Behavioral consistency (25% weight)
   - Behavioral engagement (15% weight)

3. **Database Connection**: The connection string is automatically configured. You can override it using environment variables:
   - `DATABASE_URL`: Full connection string
   - `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`

4. **Session Management**: Always use the context manager (`with db_manager.get_session()`) or ensure you close sessions properly to avoid connection leaks.

