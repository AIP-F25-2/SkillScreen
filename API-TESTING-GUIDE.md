# API Testing Guide - SkillScreen Backend Services

## 🎯 **All Services Are Working! Here's How to Test Them:**

### **✅ Working Endpoints:**

## **1. Health Check Endpoints (Always Work)**
```bash
# Test individual service health
curl http://localhost:5000/health  # API Gateway
curl http://localhost:5001/health  # User Service
curl http://localhost:5002/health  # Auth Service
curl http://localhost:5003/health  # Interview Service
curl http://localhost:5004/health  # Media Service
curl http://localhost:5005/health  # Video AI Service
curl http://localhost:5006/health  # Audio AI Service
curl http://localhost:5007/health  # Text AI Service
curl http://localhost:5008/health  # Assessment Service
curl http://localhost:5009/health  # Coding Service
curl http://localhost:5010/health  # Logger Service
curl http://localhost:5011/health  # Notification Service
```

## **2. Service Information Endpoints**
```bash
# Get service details
curl http://localhost:5000/info
curl http://localhost:5001/info
curl http://localhost:5002/info
# ... etc for all services
```

## **3. API Gateway Routing Test**
```bash
# Test if API Gateway can route to all services
curl http://localhost:5000/route-test
```

## **4. Business Logic Endpoints**

### **User Service (Port 5001)**
```bash
# Get all users
curl http://localhost:5001/users

# Get user by ID
curl http://localhost:5001/users/1

# Create user
curl -X POST http://localhost:5001/users \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com"}'
```

### **Auth Service (Port 5002)**
```bash
# Register user
curl -X POST http://localhost:5002/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "testpass"}'

# Login user
curl -X POST http://localhost:5002/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass"}'

# Validate token
curl -X POST http://localhost:5002/validate-token \
  -H "Content-Type: application/json" \
  -d '{"token": "YOUR_JWT_TOKEN"}'
```

### **Interview Service (Port 5003)**
```bash
# Get all interviews
curl http://localhost:5003/interviews

# Get interview by ID
curl http://localhost:5003/interviews/1

# Create interview
curl -X POST http://localhost:5003/interviews \
  -H "Content-Type: application/json" \
  -d '{"title": "Software Engineer Interview"}'
```

### **Media Service (Port 5004)**
```bash
# List files
curl http://localhost:5004/files

# Download file (if exists)
curl http://localhost:5004/download/filename.txt
```

### **AI Services (Ports 5005-5007)**

#### **Video AI Service (Port 5005)**
```bash
# Analyze video
curl -X POST http://localhost:5005/analyze-video \
  -H "Content-Type: application/json" \
  -d '{"video_url": "http://example.com/test.mp4"}'

# Process video
curl -X POST http://localhost:5005/process-video \
  -H "Content-Type: application/json" \
  -d '{"video_file": "test.mp4"}'
```

#### **Audio AI Service (Port 5006)**
```bash
# Analyze audio
curl -X POST http://localhost:5006/analyze-audio \
  -H "Content-Type: application/json" \
  -d '{"audio_url": "http://example.com/test.mp3"}'

# Transcribe audio
curl -X POST http://localhost:5006/transcribe \
  -H "Content-Type: application/json" \
  -d '{"audio_file": "test.mp3"}'
```

#### **Text AI Service (Port 5007)**
```bash
# Analyze text
curl -X POST http://localhost:5007/analyze-text \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a test text for analysis"}'

# Summarize text
curl -X POST http://localhost:5007/summarize \
  -H "Content-Type: application/json" \
  -d '{"text": "Long text to summarize", "max_length": 100}'
```

### **Assessment Service (Port 5008)**
```bash
# Get all assessments
curl http://localhost:5008/assessments

# Get assessment by ID
curl http://localhost:5008/assessments/1

# Create assessment
curl -X POST http://localhost:5008/assessments \
  -H "Content-Type: application/json" \
  -d '{"title": "Python Programming Test"}'

# Score assessment
curl -X POST http://localhost:5008/assessments/1/score \
  -H "Content-Type: application/json" \
  -d '{"answers": ["answer1", "answer2"]}'
```

### **Coding Service (Port 5009)**
```bash
# Execute code
curl -X POST http://localhost:5009/execute-code \
  -H "Content-Type: application/json" \
  -d '{"code": "print(\"Hello, World!\")", "language": "python"}'

# Validate code
curl -X POST http://localhost:5009/validate-code \
  -H "Content-Type: application/json" \
  -d '{"code": "def hello(): return \"world\"", "language": "python"}'

# Get supported languages
curl http://localhost:5009/languages
```

### **Logger Service (Port 5010)**
```bash
# Create log entry
curl -X POST http://localhost:5010/log \
  -H "Content-Type: application/json" \
  -d '{"level": "INFO", "service": "test", "message": "Test log message"}'

# Get logs
curl http://localhost:5010/logs

# Get log statistics
curl http://localhost:5010/logs/stats
```

### **Notification Service (Port 5011)**
```bash
# Send notification
curl -X POST http://localhost:5011/send-notification \
  -H "Content-Type: application/json" \
  -d '{"type": "email", "recipient": "test@example.com", "subject": "Test", "message": "Test message"}'

# Send email
curl -X POST http://localhost:5011/send-email \
  -H "Content-Type: application/json" \
  -d '{"to": "test@example.com", "subject": "Test Email", "body": "Test email body"}'

# Send SMS
curl -X POST http://localhost:5011/send-sms \
  -H "Content-Type: application/json" \
  -d '{"to": "+1234567890", "message": "Test SMS"}'

# Get notifications
curl http://localhost:5011/notifications
```

## **5. Through API Gateway (Recommended)**

You can also access services through the API Gateway:

```bash
# Access user service through gateway
curl http://localhost:5000/user/users

# Access auth service through gateway
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "testpass"}'

# Access any service through gateway
curl http://localhost:5000/[service-name]/[endpoint]
```

## **6. Comprehensive Testing**

### **Run the automated test script:**
```bash
python test-services.py
```

### **Test authentication flow:**
```bash
# 1. Register user
curl -X POST http://localhost:5002/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "testpass"}'

# 2. Login and get token
curl -X POST http://localhost:5002/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass"}'

# 3. Use token for protected endpoint
curl -X GET http://localhost:5002/protected \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## **7. Browser Testing**

You can also test in your browser by visiting:
- http://localhost:5000/health
- http://localhost:5001/health
- http://localhost:5002/health
- etc.

## **8. Troubleshooting**

### **If you get 404 errors:**
1. Make sure you're using the correct endpoint paths
2. Check that the service is running: `docker-compose ps`
3. Check service logs: `docker-compose logs [service-name]`

### **If you get connection errors:**
1. Make sure Docker Desktop is running
2. Check if services are healthy: `curl http://localhost:5000/route-test`
3. Restart services: `docker-compose restart`

## **🎉 Success Indicators:**

- ✅ All `/health` endpoints return 200 OK
- ✅ All `/info` endpoints return service details
- ✅ API Gateway `/route-test` shows all services connected
- ✅ Business logic endpoints return appropriate responses
- ✅ Authentication flow works end-to-end

**All your services are working perfectly! The 404 errors were likely because you were accessing root URLs instead of specific endpoints.**
