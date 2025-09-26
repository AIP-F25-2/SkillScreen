# Interview Service

Simple Interview Service for deployment testing and health monitoring.

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
docker build -t interview-service .

# Run with environment file
docker run -d --name interview-service-container -p 5003:5003 --env-file .env interview-service

# Test the service
curl http://localhost:5003
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
  "message": "Interview Service is running",
  "status": "deployed",
  "service": "interview-service",
  "port": "5003"
}
```

## Environment Configuration

The service reads configuration from `.env` file:

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file to customize settings
PORT=5003
FLASK_ENV=production
```

## Docker Commands

```bash
# Stop and remove container
docker stop interview-service-container
docker rm interview-service-container

# Rebuild and redeploy
docker build -t interview-service .
docker run -d --name interview-service-container -p 5003:5003 --env-file .env interview-service

# View logs
docker logs -f interview-service-container
```

## Files Structure
```
interview-service/
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
├── tests/              # Test directories (preserved with .gitkeep)
│   ├── integration/
│   └── unit/
└── README.md          # This file
```
