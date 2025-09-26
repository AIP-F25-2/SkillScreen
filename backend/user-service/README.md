# User Service

Simple User Service for deployment testing and health monitoring.

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
docker build -t user-service .

# Run with environment file
docker run -d --name user-service-container -p 5015:5015 --env-file .env user-service

# Test the service
curl http://localhost:5015
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
  "message": "User Service is running",
  "status": "deployed",
  "service": "user-service",
  "port": "5015"
}
```

## Environment Configuration

The service reads configuration from `.env` file:

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file to customize settings
PORT=5015
FLASK_ENV=production
```

## Docker Commands

```bash
# Stop and remove container
docker stop user-service-container
docker rm user-service-container

# Rebuild and redeploy
docker build -t user-service .
docker run -d --name user-service-container -p 5015:5015 --env-file .env user-service

# View logs
docker logs -f user-service-container
```

## Files Structure
```
user-service/
├── app.py              # Main Flask application (22 lines)
├── Dockerfile          # Docker configuration
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── .env                # Environment file
├── migrations/         # Database migration files
├── shared/             # Shared utilities
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
