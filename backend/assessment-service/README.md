# Assessment Orchestration Service

The Assessment Orchestration Service aggregates AI analysis results from multiple services (audio, video, text, coding) and generates comprehensive candidate assessments with LLM-based recommendations.

## Features

- **Intelligent Scheduled Checks**: Runs every 10 minutes to detect completed interviews
- **Multi-Service Score Aggregation**: Combines audio, video, text, and coding analysis
- **LLM-Based Weight Determination**: Uses Claude API to determine optimal scoring weights from job descriptions
- **LLM-Based Recommendations**: Generates hire/no-hire recommendations with reasoning
- **Evidence Linking**: Aggregates evidence across all modalities
- **Flexible Scoring**: Supports custom weight overrides via API

## Architecture

```
Scheduled Job (10 min) → Check Completed Interviews
                       ↓
                 Verify All AI Services Complete
                       ↓
                 Aggregate Scores (Audio + Video + Text + Coding)
                       ↓
                 LLM Determines Weights (from Job Description)
                       ↓
                 LLM Generates Recommendation + Summary
                       ↓
                 Insert into assessments Table
```

## API Endpoints

### Assessment Operations
- `POST /v1/assessment/start/{interview_id}` - Manually trigger assessment
- `GET /v1/assessment/status/{interview_id}` - Check assessment progress  
- `GET /v1/assessment/results/{interview_id}` - Get final assessment
- `POST /v1/assessment/regenerate/{interview_id}` - Regenerate with new weights
- `GET /v1/assessment/scores/{interview_id}` - Get detailed score breakdown
- `POST /v1/assessment/customize-weights` - Set custom scoring weights

### Health & Monitoring
- `GET /health` - Service health check
- `GET /v1/scheduler/status` - Check scheduler status

## Environment Variables

See `.env.example` for configuration options.

Key variables:
- `DATABASE_URL` - PostgreSQL connection string
- `ANTHROPIC_API_KEY` - Claude API key for LLM features
- `ASSESSMENT_CHECK_INTERVAL_MINUTES` - Scheduler interval (default: 10)
- `DEFAULT_WEIGHT_*` - Default scoring weights

## Default Scoring Weights

**With Coding:**
- Coding: 40%
- Text: 20%
- Audio: 20%
- Video: 20%

**Without Coding:**
- Text: 34%
- Audio: 33%
- Video: 33%

## Database Tables

**Reads from:**
- `interviews` - Interview status and metadata
- `interview_sessions` - Questions/sessions per interview
- `ai_analysis` - Raw results from AI services
- `job_positions` - Job descriptions for LLM weight determination

**Writes to:**
- `assessments` - Final aggregated assessments

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the service
uvicorn assessment:app --host 0.0.0.0 --port 8005 --reload
```

## Running with Docker

```bash
# Build image
docker build -t assessment-service .

# Run container
docker run -p 8005:8005 --env-file .env assessment-service
```

## Scheduled Check Logic

The service runs a background job every 10 minutes that:

1. Finds interviews with `status='completed'` that don't have assessments yet
2. Verifies all required AI services have completed for ALL sessions
3. Aggregates scores from `ai_analysis` table
4. Calls Claude API for weight determination and final recommendation
5. Inserts results into `assessments` table

## Development

```bash
# Run tests
pytest

# Format code
black .

# Lint
flake8 .
```

## Team

**Owner**: Assessment AI Team  
**Project**: SkillScreen  
**Tech Stack**: FastAPI, PostgreSQL, Claude API, APScheduler