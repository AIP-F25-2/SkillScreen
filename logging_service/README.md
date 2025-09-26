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
docker run -d --name logger-service-container -p 5012:5012 --env-file .env logger-service

# Test the service
curl http://localhost:5012
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
  "message": "Logger Service is running",
  "status": "deployed",
  "service": "logger-service",
  "port": "5012"
}
```

## Environment Configuration

The service reads configuration from `.env` file:

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file to customize settings
PORT=5012
FLASK_ENV=production
```

## Docker Commands

```bash
# Stop and remove container
docker stop logger-service-container
docker rm logger-service-container

# Rebuild and redeploy
docker build -t logger-service .
docker run -d --name logger-service-container -p 5012:5012 --env-file .env logger-service

# View logs
docker logs -f logger-service-container
```

## Files Structure
```
logger-service/
├── app.py              # Main Flask application (22 lines)
├── Dockerfile          # Docker configuration
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── .env                # Environment file
├── config/             # Configuration directories (preserved with .gitkeep)
│   ├── elasticsearch/
│   ├── kibana/
│   └── logstash/
├── src/                # Source directories (preserved with .gitkeep)
│   ├── controllers/
│   ├── routes/
│   ├── services/
│   └── utils/
├── tests/              # Test directories (preserved with .gitkeep)
│   ├── integration/
│   └── unit/
└── README.md          # This file
```
