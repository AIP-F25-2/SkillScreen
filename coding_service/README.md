# Coding Service

Simple Coding Service for deployment testing and health monitoring.

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
docker build -t coding-service .

# Run with environment file
docker run -d --name coding-service-container -p 5011:5011 --env-file .env coding-service

# Test the service
curl http://localhost:5011
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
  "message": "Coding Service is running",
  "status": "deployed",
  "service": "coding-service",
  "port": "5011"
}
```

## Environment Configuration

The service reads configuration from `.env` file:

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file to customize settings
PORT=5011
FLASK_ENV=production
```

## Docker Commands

```bash
# Stop and remove container
docker stop coding-service-container
docker rm coding-service-container

# Rebuild and redeploy
docker build -t coding-service .
docker run -d --name coding-service-container -p 5011:5011 --env-file .env coding-service

# View logs
docker logs -f coding-service-container
```

## Files Structure
```
coding-service/
├── app.py              # Main Flask application (22 lines)
├── Dockerfile          # Docker configuration
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── .env                # Environment file
├── src/                # Source directories (preserved with .gitkeep)
│   ├── config/
│   ├── controllers/
│   ├── prompts/
│   ├── question_bank/
│   ├── routes/
│   ├── sandbox/
│   ├── services/
│   └── utils/
├── tests/              # Test directories (preserved with .gitkeep)
│   ├── fixtures/
│   ├── integration/
│   └── unit/
└── README.md          # This file
```