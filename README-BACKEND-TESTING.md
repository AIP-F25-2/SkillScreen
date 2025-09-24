# SkillScreen Backend Services Testing Guide

This guide helps you test all backend services to ensure they are connected and running properly.

## 🏗️ Architecture Overview

The backend consists of 12 microservices:

| Service | Port | Description |
|---------|------|-------------|
| API Gateway | 5000 | Entry point for all requests |
| User Service | 5001 | User management and CRUD operations |
| Auth Service | 5002 | Authentication and JWT token management |
| Interview Service | 5003 | Interview management and scheduling |
| Media Service | 5004 | File upload and media management |
| Video AI Service | 5005 | Video analysis and processing |
| Audio AI Service | 5006 | Audio analysis and speech processing |
| Text AI Service | 5007 | Text analysis and NLP |
| Assessment Service | 5008 | Assessment creation and scoring |
| Coding Service | 5009 | Code execution and sandbox |
| Logger Service | 5010 | Centralized logging |
| Notification Service | 5011 | Email and SMS notifications |

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Python 3.7+ (for testing script)

### 1. Start All Services

**Windows:**
```bash
run-all.bat
```

**Linux/Mac:**
```bash
./run-all.sh
```

**Manual:**
```bash
docker-compose up --build -d
```

### 2. Test Service Connectivity

**Automated Testing:**
```bash
python test-services.py
```

**Manual Testing:**
```bash
# Test API Gateway
curl http://localhost:5000/health

# Test all services through gateway
curl http://localhost:5000/route-test
```

## 🔧 Service Endpoints

### API Gateway (Port 5000)
- `GET /health` - Health check
- `GET /info` - Service information
- `GET /route-test` - Test routing to all services
- `GET /<service>/<path>` - Route requests to services

### User Service (Port 5001)
- `GET /health` - Health check
- `GET /users` - Get all users
- `GET /users/<id>` - Get user by ID
- `POST /users` - Create new user
- `DELETE /users/<id>` - Delete user

### Auth Service (Port 5002)
- `GET /health` - Health check
- `POST /register` - Register new user
- `POST /login` - Login and get JWT token
- `POST /validate-token` - Validate JWT token
- `GET /protected` - Protected endpoint (requires JWT)

### Interview Service (Port 5003)
- `GET /health` - Health check
- `GET /interviews` - Get all interviews
- `GET /interviews/<id>` - Get interview by ID
- `POST /interviews` - Create new interview

### Media Service (Port 5004)
- `GET /health` - Health check
- `POST /upload` - Upload file
- `GET /download/<filename>` - Download file
- `GET /files` - List all files

### Video AI Service (Port 5005)
- `GET /health` - Health check
- `POST /analyze-video` - Analyze video content
- `POST /process-video` - Process video for interview

### Audio AI Service (Port 5006)
- `GET /health` - Health check
- `POST /analyze-audio` - Analyze audio content
- `POST /transcribe` - Transcribe audio to text

### Text AI Service (Port 5007)
- `GET /health` - Health check
- `POST /analyze-text` - Analyze text content
- `POST /summarize` - Summarize text

### Assessment Service (Port 5008)
- `GET /health` - Health check
- `GET /assessments` - Get all assessments
- `GET /assessments/<id>` - Get assessment by ID
- `POST /assessments` - Create new assessment
- `POST /assessments/<id>/score` - Score assessment

### Coding Service (Port 5009)
- `GET /health` - Health check
- `POST /execute-code` - Execute code
- `POST /validate-code` - Validate code syntax
- `GET /languages` - Get supported languages

### Logger Service (Port 5010)
- `GET /health` - Health check
- `POST /log` - Create log entry
- `GET /logs` - Get logs with filtering
- `GET /logs/<id>` - Get specific log
- `GET /logs/stats` - Get logging statistics

### Notification Service (Port 5011)
- `GET /health` - Health check
- `POST /send-notification` - Send notification
- `POST /send-email` - Send email
- `POST /send-sms` - Send SMS
- `GET /notifications` - Get notifications

## 🧪 Testing Examples

### 1. Test Authentication Flow
```bash
# Register a user
curl -X POST http://localhost:5002/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "testpass"}'

# Login and get token
curl -X POST http://localhost:5002/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass"}'

# Use token for protected endpoint
curl -X GET http://localhost:5002/protected \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 2. Test AI Services
```bash
# Analyze text
curl -X POST http://localhost:5007/analyze-text \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a test text for analysis"}'

# Analyze video
curl -X POST http://localhost:5005/analyze-video \
  -H "Content-Type: application/json" \
  -d '{"video_url": "http://example.com/test.mp4"}'

# Analyze audio
curl -X POST http://localhost:5006/analyze-audio \
  -H "Content-Type: application/json" \
  -d '{"audio_url": "http://example.com/test.mp3"}'
```

### 3. Test Code Execution
```bash
# Execute Python code
curl -X POST http://localhost:5009/execute-code \
  -H "Content-Type: application/json" \
  -d '{"code": "print(\"Hello, World!\")", "language": "python"}'

# Execute JavaScript code
curl -X POST http://localhost:5009/execute-code \
  -H "Content-Type: application/json" \
  -d '{"code": "console.log(\"Hello, World!\");", "language": "javascript"}'
```

### 4. Test Logging
```bash
# Create a log entry
curl -X POST http://localhost:5010/log \
  -H "Content-Type: application/json" \
  -d '{"level": "INFO", "service": "test-service", "message": "Test log message"}'

# Get logs
curl http://localhost:5010/logs

# Get log statistics
curl http://localhost:5010/logs/stats
```

### 5. Test Notifications
```bash
# Send email notification
curl -X POST http://localhost:5011/send-email \
  -H "Content-Type: application/json" \
  -d '{"to": "test@example.com", "subject": "Test Email", "body": "This is a test email"}'

# Send SMS notification
curl -X POST http://localhost:5011/send-sms \
  -H "Content-Type: application/json" \
  -d '{"to": "+1234567890", "message": "Test SMS message"}'
```

## 🔍 Troubleshooting

### Common Issues

1. **Services not starting:**
   ```bash
   # Check Docker is running
   docker info
   
   # Check service logs
   docker-compose logs <service-name>
   
   # Restart specific service
   docker-compose restart <service-name>
   ```

2. **Database connection issues:**
   ```bash
   # Check PostgreSQL container
   docker-compose logs postgres
   
   # Restart database
   docker-compose restart postgres
   ```

3. **Port conflicts:**
   ```bash
   # Check if ports are in use
   netstat -an | grep :5000
   
   # Stop all services
   docker-compose down
   ```

4. **Service health checks failing:**
   ```bash
   # Check individual service
   curl http://localhost:<port>/health
   
   # Check service logs
   docker-compose logs <service-name>
   ```

### Useful Commands

```bash
# View all running containers
docker-compose ps

# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f <service-name>

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Rebuild specific service
docker-compose up --build <service-name>

# Check service health
docker-compose exec <service-name> curl localhost:<port>/health
```

## 📊 Monitoring

### Health Check URLs
- API Gateway: http://localhost:5000/health
- User Service: http://localhost:5001/health
- Auth Service: http://localhost:5002/health
- Interview Service: http://localhost:5003/health
- Media Service: http://localhost:5004/health
- Video AI Service: http://localhost:5005/health
- Audio AI Service: http://localhost:5006/health
- Text AI Service: http://localhost:5007/health
- Assessment Service: http://localhost:5008/health
- Coding Service: http://localhost:5009/health
- Logger Service: http://localhost:5010/health
- Notification Service: http://localhost:5011/health

### Service Information URLs
Replace `/health` with `/info` in the above URLs to get detailed service information.

## 🎯 Success Criteria

All services are considered healthy when:
1. ✅ All 12 services respond to health checks
2. ✅ API Gateway can route to all services
3. ✅ Authentication flow works (register → login → token validation)
4. ✅ User CRUD operations work
5. ✅ AI services respond with mock data
6. ✅ Logging service accepts and stores logs
7. ✅ Notification service can send notifications
8. ✅ Database connectivity is established

## 📝 Notes

- This is a **minimal implementation** for testing connectivity
- All AI services return **mock data** for demonstration
- Database operations are simplified for testing
- JWT tokens use a simple secret (change in production)
- File uploads are stored in Docker volumes
- All services use in-memory storage for logs and notifications

## 🆘 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review service logs: `docker-compose logs`
3. Ensure all prerequisites are met
4. Try restarting services: `docker-compose restart`

---

**Happy Testing! 🚀**
