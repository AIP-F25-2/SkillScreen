# Auth Service

Simple Auth Service for deployment testing and health monitoring.

## Features
- ✅ Simple deployment check endpoint
- ✅ Environment variable configuration
- ✅ Docker containerization
- ✅ Port configuration from .env file

## Quick Start

### Docker Deployment
```bash
# Build the image
docker build -t auth-service .

# Run with environment file
docker run -d --name auth-service-container -p 5002:5002 --env-file .env auth-service

# Test the service
curl http://localhost:5002
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
  "message": "Auth Service is running",
  "status": "deployed",
  "service": "auth-service",
  "port": "5002"
}
```

## Environment Configuration

The service reads configuration from `.env` file:

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file to customize settings
PORT=5002
FLASK_ENV=production
```

## Docker Commands

```bash
# Stop and remove container
docker stop auth-service-container
docker rm auth-service-container

# Rebuild and redeploy
docker build -t auth-service .
docker run -d --name auth-service-container -p 5002:5002 --env-file .env auth-service

# View logs
docker logs -f auth-service-container
```

## Files Structure
```
auth-service/
├── app.py              # Main Flask application (22 lines)
├── Dockerfile          # Docker configuration
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
└── README.md          # This file
```
