# Audio AI Service

Simple Audio AI Service for deployment testing and health monitoring.

## Features
- ✅ Simple deployment check endpoint
- ✅ Environment variable configuration
- ✅ Docker containerization
- ✅ Port configuration from .env file

## Quick Start

### Docker Deployment
```bash
# Build the image
docker build -t audio-ai-service .

# Run with environment file
docker run -d --name audio-ai-service-container -p 5009:5009 --env-file .env audio-ai-service

# Test the service
curl http://localhost:5009
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py
```

## API Endpoints

### Root Endpoint
- `GET /` - Service status and deployment check

**Response:**
```json
{
  "message": "Audio AI Service is running",
  "status": "deployed",
  "service": "audio-ai-service",
  "port": "5009"
}
```

## Environment Configuration

The service reads configuration from `.env` file:

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file to customize settings
PORT=5009
FLASK_ENV=production
```

## Docker Commands

```bash
# Stop and remove container
docker stop audio-ai-service-container
docker rm audio-ai-service-container

# Rebuild and redeploy
docker build -t audio-ai-service .
docker run -d --name audio-ai-service-container -p 5009:5009 --env-file .env audio-ai-service

# View logs
docker logs -f audio-ai-service-container
```

## Files Structure
```
audio-ai-service/
├── app.py              # Main Flask application (22 lines)
├── Dockerfile          # Docker configuration
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
└── README.md          # This file
```