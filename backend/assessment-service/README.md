# Assessment Service

Simple Assessment Service for deployment testing and health monitoring.

## Features
- ✅ Simple deployment check endpoint
- ✅ Environment variable configuration
- ✅ Docker containerization
- ✅ Port configuration from .env file

## Quick Start

### Docker Deployment
```bash
# Build the image
docker build -t assessment-service .

# Run with environment file
docker run -d --name assessment-service-container -p 5008:5008 --env-file .env assessment-service

# Test the service
curl http://localhost:5008
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
  "message": "Assessment Service is running",
  "status": "deployed",
  "service": "assessment-service",
  "port": "5008"
}
```

## Environment Configuration

The service reads configuration from `.env` file:

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file to customize settings
PORT=5008
FLASK_ENV=production
```

## Docker Commands

```bash
# Stop and remove container
docker stop assessment-service-container
docker rm assessment-service-container

# Rebuild and redeploy
docker build -t assessment-service .
docker run -d --name assessment-service-container -p 5008:5008 --env-file .env assessment-service

# View logs
docker logs -f assessment-service-container
```

## Files Structure
```
assessment-service/
├── app.py              # Main Flask application (22 lines)
├── Dockerfile          # Docker configuration
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
└── README.md          # This file
```
