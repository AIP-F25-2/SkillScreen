# Video AI Service

Simple Video AI Service for deployment testing and health monitoring.

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
docker build -t video-ai-service .

# Run with environment file
docker run -d --name video-ai-service-container -p 5016:5016 --env-file .env video-ai-service

# Test the service
curl http://localhost:5016
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
  "message": "Video AI Service is running",
  "status": "deployed",
  "service": "video-ai-service",
  "port": "5016"
}
```

## Environment Configuration

The service reads configuration from `.env` file:

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file to customize settings
PORT=5016
FLASK_ENV=production
```

## Docker Commands

```bash
# Stop and remove container
docker stop video-ai-service-container
docker rm video-ai-service-container

# Rebuild and redeploy
docker build -t video-ai-service .
docker run -d --name video-ai-service-container -p 5016:5016 --env-file .env video-ai-service

# View logs
docker logs -f video-ai-service-container
```

## Files Structure
```
video-ai-service/
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
│   ├── integration/
│   └── unit/
└── README.md          # This file
```
