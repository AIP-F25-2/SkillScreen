# Text AI Service

Simple Text AI Service for deployment testing and health monitoring.

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
docker build -t text-ai-service .

# Run with environment file
docker run -d --name text-ai-service-container -p 5014:5014 --env-file .env text-ai-service

# Test the service
curl http://localhost:5014
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
  "message": "Text AI Service is running",
  "status": "deployed",
  "service": "text-ai-service",
  "port": "5014"
}
```

## Environment Configuration

The service reads configuration from `.env` file:

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file to customize settings
PORT=5014
FLASK_ENV=production
```

## Docker Commands

```bash
# Stop and remove container
docker stop text-ai-service-container
docker rm text-ai-service-container

# Rebuild and redeploy
docker build -t text-ai-service .
docker run -d --name text-ai-service-container -p 5014:5014 --env-file .env text-ai-service

# View logs
docker logs -f text-ai-service-container
```

## Files Structure
```
text-ai-service/
├── app.py              # Main Flask application (22 lines)
├── Dockerfile          # Docker configuration
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── .env                # Environment file
├── src/                # Source directories (preserved with .gitkeep)
│   ├── config/
│   ├── controllers/
│   ├── prompts/
│   ├── routes/
│   ├── services/
│   └── utils/
├── tests/              # Test directories (preserved with .gitkeep)
│   ├── fixtures/
│   │   ├── sample_responses/
│   │   └── sample_resumes/
│   ├── integration/
│   └── unit/
└── README.md          # This file
```