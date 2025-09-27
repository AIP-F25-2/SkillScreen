# Audio AI Service

FastAPI-based microservice for audio processing and AI analysis.

## Features
- ✅ FastAPI framework with automatic API documentation
- ✅ Standardized API response structure
- ✅ Health check endpoints
- ✅ Docker containerization
- ✅ Environment configuration

## Quick Start

### Docker Deployment
```bash
# Build the image
docker build -t audio-ai-service .

# Run with environment file
docker run -d --name audio-ai-service-container -p 8080:8080 --env-file .env audio-ai-service

# Test the service
curl http://localhost:8080
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn audio_ai:app --host 0.0.0.0 --port 8080
```

## API Endpoints

### Health Check
- `GET /` - Service status and deployment check
- `GET /health` - Detailed health information

## Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Server Configuration
PORT=8080
HOST=0.0.0.0

# Environment
ENVIRONMENT=development
DEBUG=true

# Logging
LOG_LEVEL=INFO
```

## API Response Format

All endpoints return standardized responses:

```json
{
  "success": true,
  "data": {
    // Actual response data
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00.000Z",
    "request_id": "req_abc123",
    "version": "v1"
  }
}
```

## Files Structure
```
audio-ai-service/
├── audio_ai.py            # Main FastAPI application
├── Dockerfile            # Docker configuration
├── requirements.txt      # Python dependencies
├── .env.example          # Environment template
├── controllers/          # API controllers
├── repositories/         # Data access layer
├── services/             # Business logic
├── tests/                # Test files
└── README.md            # This file
```