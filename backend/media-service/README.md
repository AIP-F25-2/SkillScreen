# Media Service

Simple Media Service for deployment testing and health monitoring.

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
docker build -t media-service .

# Run with environment file
docker run -d --name media-service-container -p 5004:5004 --env-file .env media-service

# Test the service
curl http://localhost:5004
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
  "message": "Media Service is running",
  "status": "deployed",
  "service": "media-service",
  "port": "5004"
}
```

## Environment Configuration

The service reads configuration from `.env` file:

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file to customize settings
PORT=5004
FLASK_ENV=production
```

## Docker Commands

```bash
# Stop and remove container
docker stop media-service-container
docker rm media-service-container

# Rebuild and redeploy
docker build -t media-service .
docker run -d --name media-service-container -p 5004:5004 --env-file .env media-service

# View logs
docker logs -f media-service-container
```

## Files Structure
```
media-service/
├── app.py              # Main Flask application (22 lines)
├── Dockerfile          # Docker configuration
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── .env                # Environment file
├── src/                # Source directories (preserved with .gitkeep)
│   ├── controllers/
│   ├── middleware/
│   ├── routes/
│   ├── services/
│   └── utils/
├── storage/            # Storage directories (preserved with .gitkeep)
│   ├── processed/
│   └── uploads/
├── tests/              # Test directories (preserved with .gitkeep)
│   ├── integration/
│   └── unit/
└── README.md          # This file
```