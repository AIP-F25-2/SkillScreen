# AI Logic Service - Docker Integration

## Overview

The AI Logic Service is now fully integrated with Docker Compose and accessible through the API Gateway.

---

## Architecture

```
Frontend (localhost:3000)
    ↓
API Gateway (localhost:5000)
    ↓
AI Logic Service (container: ai-logic-service:8080)
    → Exposed as: localhost:8001
    → Gateway route: /ai-logic/*
```

---

## Files Created/Modified

### Created Files
1. **`backend/ai-logic-service/Dockerfile.dev`** - Development Dockerfile
2. **`backend/ai-logic-service/requirements_simple.txt`** - Python dependencies
3. **`DOCKER_SETUP.md`** - This file

### Modified Files
1. **`docker-compose.dev.yml`** - Added ai-logic-service
2. **`backend/api-gateway/gateway.py`** - Added /ai-logic routing
3. **`backend/ai-logic-service/simple_fastapi_app.py`** - Environment variable configuration
4. **`frontend/src/lib/api.ts`** - Updated to use API Gateway routes

---

## Docker Compose Configuration

```yaml
ai-logic-service:
  build:
    context: ./backend/ai-logic-service
    dockerfile: Dockerfile.dev
  container_name: ai-logic-service
  ports:
    - "8001:8080"
  environment:
    - PORT=8080
    - HOST=0.0.0.0
    - APP_NAME=ai-logic-service
    - ENVIRONMENT=development
    - DEBUG=True
    - LOG_LEVEL=INFO
  volumes:
    - ./backend/ai-logic-service:/app
  networks:
    - skill-screen-network
```

---

## Setup Instructions

### 1. Build and Start All Services

```bash
cd /Users/dimanthagoonewardena/Desktop/SkillScreen

# Stop any existing containers
docker-compose -f docker-compose.dev.yml down

# Build the AI logic service
docker-compose -f docker-compose.dev.yml build ai-logic-service

# Start all services
docker-compose -f docker-compose.dev.yml up -d

# Or start just the AI logic service
docker-compose -f docker-compose.dev.yml up -d ai-logic-service
```

### 2. Verify Service is Running

```bash
# Check container status
docker ps | grep ai-logic-service

# Check logs
docker logs ai-logic-service

# Test health endpoint
curl http://localhost:8001/health

# Through API Gateway
curl http://localhost:5000/ai-logic/health
```

### 3. Test the Integration

```bash
# Test through API Gateway
curl -X POST http://localhost:5000/ai-logic/candidates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "resume_text": "Experienced developer with Python and React",
    "experience_years": 5,
    "skills": ["Python", "React"]
  }'
```

---

## API Routes

### Through API Gateway (localhost:5000)

All requests go through: `http://localhost:5000/ai-logic/*`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ai-logic/health` | GET | Health check |
| `/ai-logic/resumes/parse` | POST | Parse resume PDF |
| `/ai-logic/candidates` | POST | Create candidate |
| `/ai-logic/jobs` | POST | Create job |
| `/ai-logic/interviews/start` | POST | Start interview |
| `/ai-logic/interviews/{id}` | GET | Get interview |

### Direct Access (localhost:8001)

For debugging only: `http://localhost:8001/*`

- Same endpoints without `/ai-logic` prefix
- Documentation: `http://localhost:8001/docs`

---

## Frontend Integration

### Updated API Client

All frontend requests now go through the API Gateway:

```typescript
// Before (direct to service)
const url = `http://localhost:8001/candidates`;

// After (through gateway)
const url = `${this.baseUrl}/ai-logic/candidates`;
// Resolves to: http://localhost:5000/ai-logic/candidates
```

### Testing from Frontend

1. **Upload Resume** (Recruiter Dashboard)
2. **Watch Browser Console** for:
   ```
   ✅ Parsing resume with AI service...
   ✅ AI candidate created
   ✅ AI job created
   ✅ AI interview started
   ```

---

## Development Workflow

### Making Changes

1. **Edit Code** in `backend/ai-logic-service/`
2. **Restart Container** (volume mount auto-reloads):
   ```bash
   docker-compose -f docker-compose.dev.yml restart ai-logic-service
   ```

### Viewing Logs

```bash
# Follow logs in real-time
docker logs -f ai-logic-service

# Last 100 lines
docker logs --tail 100 ai-logic-service

# With timestamps
docker logs -t ai-logic-service
```

### Debugging

```bash
# Execute commands inside container
docker exec -it ai-logic-service bash

# Check Python version
docker exec ai-logic-service python --version

# List installed packages
docker exec ai-logic-service pip list

# Test endpoints from inside container
docker exec ai-logic-service curl http://localhost:8080/health
```

---

## Troubleshooting

### Service Won't Start

**Check logs:**
```bash
docker logs ai-logic-service
```

**Common issues:**
- Port 8080 already in use inside container
- Missing dependencies in requirements_simple.txt
- Syntax errors in simple_fastapi_app.py

**Solution:**
```bash
# Rebuild from scratch
docker-compose -f docker-compose.dev.yml build --no-cache ai-logic-service
docker-compose -f docker-compose.dev.yml up -d ai-logic-service
```

### Can't Connect from Frontend

**Issue:** 404 errors on `/ai-logic/*` routes

**Check:**
1. API Gateway is running: `docker ps | grep api-gateway`
2. Service map includes ai-logic: `docker exec api-gateway cat gateway.py | grep ai-logic`
3. RBAC rules allow access

**Solution:**
```bash
# Restart API Gateway
docker-compose -f docker-compose.dev.yml restart api-gateway

# Check gateway logs
docker logs api-gateway
```

### Resume Parsing Fails

**Issue:** PDF parsing errors

**Check:**
1. PDF is text-based (not scanned image)
2. pdfplumber and PyPDF2 are installed
3. File upload size limits

**Debug:**
```bash
# Check if libraries are installed
docker exec ai-logic-service pip show pdfplumber PyPDF2

# Test parsing directly
docker exec -it ai-logic-service python
>>> from utils.resume_parser import resume_parser
>>> # Test parsing
```

### Volume Mount Issues

**Issue:** Code changes not reflected

**Check:**
```bash
# Verify volume mount
docker inspect ai-logic-service | grep -A 10 Mounts

# Check file exists in container
docker exec ai-logic-service ls -la /app/simple_fastapi_app.py
```

**Solution:**
```bash
# Restart with fresh mount
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up -d ai-logic-service
```

---

## Production Deployment

### Differences from Development

**Development (current):**
- ✅ Volume mounts for live code reload
- ✅ In-memory database
- ✅ Debug mode enabled
- ✅ Exposed port 8001 for direct access

**Production (recommended):**
- ⚠️ No volume mounts (baked-in code)
- ⚠️ PostgreSQL database connection
- ⚠️ Debug mode disabled
- ⚠️ Only accessible through API Gateway
- ⚠️ Multiple workers (uvicorn --workers 4)
- ⚠️ Proper error handling and monitoring

### Production Dockerfile

Use the existing `Dockerfile` (not `Dockerfile.dev`):

```yaml
ai-logic-service:
  build:
    context: ./backend/ai-logic-service
    dockerfile: Dockerfile  # Production version
  # ... rest of config
```

---

## Environment Variables

### Service-Level

Set in `docker-compose.dev.yml`:

```yaml
environment:
  - PORT=8080              # Internal container port
  - HOST=0.0.0.0          # Bind to all interfaces
  - APP_NAME=ai-logic-service
  - ENVIRONMENT=development
  - DEBUG=True
  - LOG_LEVEL=INFO
```

### Gateway-Level

API Gateway configuration (already set):

```python
"ai-logic": os.getenv("AI_LOGIC_SERVICE_URL", "http://ai-logic-service:8080")
```

---

## Testing Checklist

- [ ] Build service: `docker-compose build ai-logic-service`
- [ ] Start service: `docker-compose up -d ai-logic-service`
- [ ] Check status: `docker ps | grep ai-logic`
- [ ] Test health: `curl http://localhost:8001/health`
- [ ] Test through gateway: `curl http://localhost:5000/ai-logic/health`
- [ ] Check logs: `docker logs ai-logic-service`
- [ ] Upload resume from frontend
- [ ] Check browser console for AI service logs
- [ ] Verify question modal shows questions
- [ ] Complete an interview
- [ ] Check video recording works

---

## Quick Commands Reference

```bash
# Start everything
docker-compose -f docker-compose.dev.yml up -d

# Start just AI logic service
docker-compose -f docker-compose.dev.yml up -d ai-logic-service

# Stop everything
docker-compose -f docker-compose.dev.yml down

# Restart AI logic service
docker-compose -f docker-compose.dev.yml restart ai-logic-service

# Rebuild AI logic service
docker-compose -f docker-compose.dev.yml build ai-logic-service

# View logs
docker logs -f ai-logic-service

# Execute shell in container
docker exec -it ai-logic-service bash

# Check health
curl http://localhost:8001/health
curl http://localhost:5000/ai-logic/health

# Test resume parsing
curl -X POST http://localhost:5000/ai-logic/candidates \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@test.com","skills":[],"experience_years":0}'
```

---

## Summary

### ✅ What's Done
1. Dockerfile.dev created for AI logic service
2. Added to docker-compose.dev.yml
3. API Gateway routing configured
4. Frontend API client updated
5. Environment variables configured
6. Volume mounts for live reload

### ✅ How to Use
1. Run `docker-compose up -d`
2. Access through API Gateway: `http://localhost:5000/ai-logic/*`
3. Direct access (debug): `http://localhost:8001/*`
4. Frontend automatically uses gateway routes

### ✅ Benefits
1. Consistent with other services
2. Centralized routing through gateway
3. Easy deployment and scaling
4. Live code reload during development
5. Proper service isolation

---

**Last Updated:** October 16, 2025  
**Status:** Ready for Testing 🚀

