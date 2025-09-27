# API Gateway Service

FastAPI-based API Gateway service with JWT authentication, RBAC, and microservice proxying.

## Features
- ✅ FastAPI-based API Gateway
- ✅ JWT Authentication & Authorization
- ✅ Role-Based Access Control (RBAC)
- ✅ Microservice Proxying
- ✅ Environment variable configuration
- ✅ Docker containerization
- ✅ Health monitoring endpoints

## Quick Start

### Docker Deployment
```bash
# Build the image
docker build -t api-gateway .

# Run with environment file
docker run -d --name api-gateway-container -p 8080:8080 --env-file .env api-gateway

# Test the service
curl http://localhost:8080
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn gateway:app --host 0.0.0.0 --port 8080 --reload
```

## API Endpoints

### Health Check
- `GET /` - Service status and deployment check

### Microservice Proxying
- `GET|POST|PUT|DELETE /{service}/{path:path}` - Proxy requests to microservices
  - `/{service}` can be: `user`, `assessment`, `coding`
  - `/{path:path}` - any path to forward to the target service

### Authentication
- JWT Bearer token required for all endpoints except `/auth/`
- Token must be included in `Authorization: Bearer <token>` header

## Environment Configuration

The service reads configuration from `.env` file:

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file to customize settings
PORT=8080
SECRET_KEY=your-secret-key
USER_SERVICE_URL=http://user_service:8001
ASSESSMENT_SERVICE_URL=http://assessment_service:8002
CODING_SERVICE_URL=http://coding_service:8003
```

## RBAC Rules

The API Gateway enforces role-based access control:

- `/user` - Only `admin` role
- `/assessment` - Both `admin` and `user` roles  
- `/coding` - Only `user` role

## Docker Commands

```bash
# Stop and remove container
docker stop api-gateway-container
docker rm api-gateway-container

# Rebuild and redeploy
docker build -t api-gateway .
docker run -d --name api-gateway-container -p 8080:8080 --env-file .env api-gateway

# View logs
docker logs -f api-gateway-container
```

## Files Structure
```
api-gateway/
├── gateway.py           # Main FastAPI application
├── Dockerfile          # Docker configuration
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
└── README.md          # This file
```
