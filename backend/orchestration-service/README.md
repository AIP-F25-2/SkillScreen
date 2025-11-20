# Interview Orchestration Service

Central orchestration service for managing complete interview workflows in the SkillScreen platform.

## Overview

The Orchestration Service coordinates all backend services to deliver seamless interview experiences:

- **Text Service**: Question generation and response evaluation
- **Audio AI Service**: Audio/video transcription and analysis
- **Video AI Service**: Video analysis and cheating detection  
- **Media Service**: File storage and management
- **Interview Service**: Interview metadata and scheduling

## Features

✅ **Interview Management**
- Create and manage interview sessions
- Track interview progress
- Handle interview completion

✅ **Question Orchestration**
- Generate contextual questions
- Manage question flow
- Track answered/pending questions

✅ **Answer Processing**
- Receive text and media answers
- Coordinate multi-service processing
- Aggregate analysis results

✅ **Background Processing**
- Async audio/video analysis
- Text evaluation
- Result aggregation

✅ **Summary Generation**
- Comprehensive interview summaries
- Multi-source data aggregation
- Final recommendations

## Architecture

```
┌─────────────────────────────────────────┐
│     Interview Orchestration Service     │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │   Interview Controller          │   │
│  │   - Create Interview            │   │
│  │   - Get Questions               │   │
│  │   - Submit Answers              │   │
│  │   - Generate Summary            │   │
│  └─────────────────────────────────┘   │
│                 │                       │
│  ┌──────────────▼──────────────────┐   │
│  │   Orchestration Service         │   │
│  │   - Workflow Coordination       │   │
│  │   - Service Integration         │   │
│  │   - Result Aggregation          │   │
│  └──────────────┬──────────────────┘   │
│                 │                       │
└─────────────────┼───────────────────────┘
                  │
        ┌─────────┴──────────┐
        │                    │
   ┌────▼─────┐      ┌──────▼─────┐
   │  Text    │      │  Audio AI  │
   │ Service  │      │  Service   │
   └──────────┘      └────────────┘
        │                    │
   ┌────▼─────┐      ┌──────▼─────┐
   │  Video   │      │   Media    │
   │ AI Svc   │      │  Service   │
   └──────────┘      └────────────┘
```

## API Endpoints

### Interview Management

#### Create Interview
```http
POST /api/orchestration/interviews
```

**Request:**
```json
{
  "candidate_id": "uuid",
  "job_position_id": "uuid",
  "interview_type": "mixed",
  "max_questions": 15
}
```

**Response:**
```json
{
  "interview_id": "uuid",
  "session_id": "uuid",
  "status": "created",
  "first_question": {
    "question_id": "uuid",
    "question_text": "Tell me about yourself...",
    "question_type": "behavioral"
  }
}
```

#### Get Interview Status
```http
GET /api/orchestration/interviews/{interview_id}/status
```

**Response:**
```json
{
  "interview_id": "uuid",
  "status": "in_progress",
  "current_question_number": 5,
  "total_questions_asked": 5,
  "max_questions": 15,
  "start_time": "2024-01-15T10:30:00Z"
}
```

### Question Management

#### Get Next Question
```http
POST /api/orchestration/interviews/{interview_id}/questions
```

**Request (optional):**
```json
{
  "context": {
    "previous_answer_quality": "good"
  }
}
```

**Response:**
```json
{
  "question_id": "uuid",
  "session_id": "uuid",
  "question_text": "Describe your experience with Python...",
  "question_number": 6,
  "question_type": "technical"
}
```

### Answer Submission

#### Submit Answer
```http
POST /api/orchestration/interviews/{interview_id}/answers
```

**Request:**
```json
{
  "session_id": "uuid",
  "question_id": "uuid",
  "text_answer": "I have 5 years of experience...",
  "media_file_id": "uuid",
  "response_time_seconds": 45.5
}
```

**Response:**
```json
{
  "interview_id": "uuid",
  "session_id": "uuid",
  "question_id": "uuid",
  "status": "accepted",
  "processing_status": "pending",
  "message": "Answer submitted. Processing in background."
}
```

### Interview Completion

#### Complete Interview
```http
POST /api/orchestration/interviews/{interview_id}/complete
```

**Response:**
```json
{
  "interview_id": "uuid",
  "status": "completed",
  "message": "Interview completed. Summary generation in progress.",
  "summary_available": false
}
```

#### Get Interview Summary
```http
GET /api/orchestration/interviews/{interview_id}/summary
```

**Response:**
```json
{
  "interview_id": "uuid",
  "candidate_name": "John Doe",
  "job_title": "Senior Python Developer",
  "overall_score": 8.5,
  "recommendation": "Strong Hire",
  "text_evaluation": { ... },
  "audio_analysis": { ... },
  "video_analysis": { ... },
  "total_questions": 15,
  "total_answers": 15,
  "duration_minutes": 25.5,
  "strengths": ["Strong technical skills", "Good communication"],
  "weaknesses": ["Limited leadership experience"],
  "next_steps": ["Schedule technical round", "Check references"]
}
```

## Workflow

### 1. Interview Creation
```
User Request → Orchestration Service
             ↓
    Create Interview Record
             ↓
    Get Candidate & Job Details
             ↓
    Call Text Service → Generate First Question
             ↓
    Create Session Record
             ↓
    Return Interview Details + First Question
```

### 2. Question-Answer Cycle
```
Get Next Question Request → Orchestration Service
                          ↓
               Check Interview Status
                          ↓
              Get Previous Q&A Context
                          ↓
     Call Text Service → Generate Next Question
                          ↓
              Create New Session Record
                          ↓
                Return Question
                          
Submit Answer Request → Orchestration Service
                      ↓
         Store Text Answer + Media Reference
                      ↓
         Return Immediate Acknowledgment
                      ↓
      [Background] Process Media Files
                      ↓
      Audio AI Service → Transcription & Analysis
                      ↓
      Video AI Service → Behavior Analysis
                      ↓
      Text Service → Response Evaluation
                      ↓
              Store All Results
```

### 3. Interview Completion
```
Complete Request → Orchestration Service
                 ↓
         Mark Interview Complete
                 ↓
    [Background] Generate Summary
                 ↓
    Collect All Analysis Results:
    - Text Evaluations
    - Audio Analyses
    - Video Reports
                 ↓
    Call Text Service → Generate Summary
                 ↓
         Store Summary
```

## Configuration

### Environment Variables

```bash
# Application
APP_NAME=orchestration-service
ENVIRONMENT=development
DEBUG=True
HOST=0.0.0.0
PORT=8080

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/skillscreen

# Service URLs (Docker network)
TEXT_SERVICE_URL=http://text-service:8080
AUDIO_AI_SERVICE_URL=http://audio-ai-service:8080
VIDEO_AI_SERVICE_URL=http://video-ai-service:8080
MEDIA_SERVICE_URL=http://media-service:8080
INTERVIEW_SERVICE_URL=http://interview-service:8080

# Timeouts
SERVICE_TIMEOUT=300
PROCESSING_TIMEOUT=600

# Interview Configuration
MAX_QUESTIONS_PER_INTERVIEW=15
DEFAULT_INTERVIEW_DURATION_MINUTES=30
```

## Local Development

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Run locally
python orchestration.py
```

### Docker Deployment

```bash
# Build image
docker build -t orchestration-service .

# Run container
docker run -d \
  --name orchestration-service \
  -p 8080:8080 \
  --env-file .env \
  orchestration-service
```

## Database Schema

The orchestration service uses existing tables:

### interviews
- id (UUID, PK)
- candidate_id (UUID, FK)
- job_position_id (UUID, FK)
- interview_type (VARCHAR)
- status (VARCHAR)
- max_questions (INT)
- current_question_number (INT)
- total_questions_asked (INT)
- start_time (TIMESTAMP)
- end_time (TIMESTAMP)
- duration_minutes (FLOAT)

### interview_sessions
- id (UUID, PK)
- interview_id (UUID, FK)
- question_id (UUID)
- question_number (INT)
- question_text (TEXT)
- text_answer (TEXT)
- media_file_id (UUID)
- response_time_seconds (FLOAT)
- status (VARCHAR)
- processing_status (VARCHAR)
- answered_at (TIMESTAMP)

### interview_summaries
- interview_id (UUID, PK)
- overall_score (FLOAT)
- recommendation (VARCHAR)
- text_evaluation (JSONB)
- audio_summary (JSONB)
- video_summary (JSONB)
- strengths (JSONB)
- weaknesses (JSONB)
- red_flags (JSONB)
- next_steps (JSONB)
- generated_at (TIMESTAMP)

## Service Integration

### Text Service Integration
```python
# Generate question
question = await text_client.generate_question(
    interview_id=interview_id,
    candidate_id=candidate_id,
    job_position_id=job_position_id,
    question_number=1,
    interview_type="mixed"
)

# Evaluate response
evaluation = await text_client.evaluate_response(
    question_text="...",
    response_text="...",
    candidate_id=candidate_id,
    job_position_id=job_position_id
)

# Generate summary
summary = await text_client.generate_interview_summary(
    interview_id=interview_id,
    sessions=sessions,
    audio_analyses=audio_analyses
)
```

### Audio AI Service Integration
```python
# Trigger audio processing
result = await audio_client.process_interview_audio(
    interview_id=interview_id,
    session_id=session_id,
    media_file_id=media_file_id
)

# Check status
status = await audio_client.get_audio_status(media_file_id)

# Get analysis results
analysis = await audio_client.get_audio_analysis(
    interview_id=interview_id,
    session_id=session_id
)
```

### Video AI Service Integration
```python
# Analyze video
result = await video_client.analyze_video(
    user_id=candidate_id,
    video_url=video_url
)

# Get report
report = await video_client.get_video_report(
    user_id=candidate_id,
    timestamp=timestamp
)
```

## Error Handling

The service implements comprehensive error handling:

- **Service Unavailable**: Graceful degradation when services are down
- **Timeouts**: Configurable timeouts for long-running operations
- **Retries**: Automatic retries for transient failures
- **Logging**: Detailed logging for debugging

## Monitoring

### Health Endpoints

```http
GET /health              # Basic health check
GET /health/ready        # Readiness probe
GET /health/live         # Liveness probe
```

### Metrics

- Interview creation rate
- Question generation latency
- Processing success rate
- Service response times

## Best Practices

1. **Async Processing**: Heavy operations (audio/video) run in background
2. **Immediate Acknowledgment**: Quick response to client, process later
3. **Idempotency**: Safe to retry operations
4. **Transaction Management**: Proper rollback on failures
5. **Service Isolation**: Each service has single responsibility

## Troubleshooting

### Common Issues

**Interview creation fails**
- Check candidate and job position exist
- Verify text-service is accessible
- Check database connectivity

**Answer processing slow**
- Monitor audio-ai-service queue
- Check media file upload completion
- Verify sufficient resources

**Summary not generated**
- Ensure interview is marked complete
- Check all sessions have answers
- Verify text-service connectivity

## Contributing

When adding new features:
1. Update API endpoints
2. Add service client methods
3. Update orchestration logic
4. Add tests
5. Update documentation

## License

MIT License - SkillScreen Platform

