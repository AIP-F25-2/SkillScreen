# Notification Service

Simple Notification Service for deployment testing and health monitoring.

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
docker build -t notification-service .

# Run with environment file
docker run -d --name notification-service-container -p 5013:5013 --env-file .env notification-service

# Test the service
curl http://localhost:5013
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
  "message": "Notification Service is running",
  "status": "deployed",
  "service": "notification-service",
  "port": "5013"
}
```

## Environment Configuration

The service reads configuration from `.env` file:

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file to customize settings
PORT=5013
FLASK_ENV=production
```

## Docker Commands

```bash
# Stop and remove container
docker stop notification-service-container
docker rm notification-service-container

# Rebuild and redeploy
docker build -t notification-service .
docker run -d --name notification-service-container -p 5013:5013 --env-file .env notification-service

# View logs
docker logs -f notification-service-container
```

## Files Structure
```
notification-service/
├── app.py              # Main Flask application (22 lines)
├── Dockerfile          # Docker configuration
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── .env                # Environment file
├── src/                # Source directories (preserved with .gitkeep)
│   ├── controllers/
│   ├── routes/
│   ├── services/
│   ├── templates/
│   │   ├── email/
│   │   └── pdf/
│   └── utils/
├── tests/              # Test directories (preserved with .gitkeep)
│   ├── integration/
│   └── unit/
└── README.md          # This file
```
