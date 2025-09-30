# Logger Service

Simple Logger Service for deployment testing and health monitoring.

## Features
- ✅ Simple deployment check endpoint
- ✅ Environment variable configuration
- ✅ Docker containerization
- ✅ Port configuration from .env file
- ✅ Preserved directory structure with .gitkeep files

## Quick Start

### Docker Deployment
```bash
# Build the image
docker build -t logger-service .

# Run with environment file
docker run -d --name logger-service-container -p 8080:8080 --env-file .env logger-service

# Test the service
curl http://localhost:8080
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn logger_service:app --host 0.0.0.0 --port 8080
```

## API Endpoints

### Root Endpoint
- `GET /` - Service status and deployment check

**Response:**
```json
{
  "message": "Logger Service is running",
  "status": "deployed",
  "service": "logger-service",
  "port": "8080"
}
```

## Environment Configuration

The service reads configuration from `.env` file:

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file to customize settings
PORT=8080
ENVIRONMENT=development
```

## Docker Commands

```bash
# Stop and remove container
docker stop logger-service-container
docker rm logger-service-container

# Rebuild and redeploy
docker build -t logger-service .
docker run -d --name logger-service-container -p 8080:8080 --env-file .env logger-service

# View logs
docker logs -f logger-service-container
```

## Files Structure
```
logger-service/
├── logger_service.py   # Main FastAPI application
├── Dockerfile          # Docker configuration
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── controllers/        # API controllers
├── repositories/       # Data access layer
├── services/           # Business logic
├── tests/              # Test files
└── README.md          # This file
```
