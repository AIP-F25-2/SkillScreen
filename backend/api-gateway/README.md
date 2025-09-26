# API Gateway Service

Simple API Gateway service for deployment testing and health monitoring.

## Features
- ✅ Simple deployment check endpoint
- ✅ Environment variable configuration
- ✅ Docker containerization
- ✅ Port configuration from .env file

## Quick Start

### Docker Deployment
```bash
# Build the image
docker build -t api-gateway .

# Run with environment file
docker run -d --name api-gateway-container -p 5000:5000 --env-file .env api-gateway

# Test the service
curl http://localhost:5000
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
  "message": "API Gateway is running",
  "status": "deployed",
  "service": "api-gateway",
  "port": "5000"
}
```

## Environment Configuration

The service reads configuration from `.env` file:

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file to customize settings
PORT=5000
FLASK_ENV=production
```

## Docker Commands

```bash
# Stop and remove container
docker stop api-gateway-container
docker rm api-gateway-container

# Rebuild and redeploy
docker build -t api-gateway .
docker run -d --name api-gateway-container -p 5000:5000 --env-file .env api-gateway

# View logs
docker logs -f api-gateway-container
```

## Files Structure
```
api-gateway/
├── app.py              # Main Flask application
├── Dockerfile          # Docker configuration
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── controllers/        # HTTP request handling
├── services/           # Business logic
├── repositories/       # Data access layer
├── tests/              # Test files (.gitkeep only)
└── README.md          # This file
```
