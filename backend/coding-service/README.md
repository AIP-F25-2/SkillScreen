# Coding Service

FastAPI-based microservice for coding challenges and solutions.

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
docker build -t coding-service .

# Run with environment file
docker run -d --name coding-service-container -p 8080:8080 --env-file .env coding-service

# Test the service
curl http://localhost:8080
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn coding:app --host 0.0.0.0 --port 8080
```

## API Endpoints

### Health Check
- `GET /` - Service status and deployment check
- `GET /health` - Detailed health information

### Coding Endpoints
- `GET /problems` - Get coding problems
- `POST /submit` - Submit coding solutions

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
coding-service/
├── coding.py             # Main FastAPI application
├── Dockerfile           # Docker configuration
├── requirements.txt     # Python dependencies
├── .env.example         # Environment template
├── controllers/         # API controllers
├── repositories/        # Data access layer
├── services/            # Business logic
├── tests/               # Test files
└── README.md           # This file
```