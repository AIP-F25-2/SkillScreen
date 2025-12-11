# SkillScreen - Full Project Overview

## 🎯 Project Status

### ✅ Currently Running
- **Frontend (Next.js)**: Running on http://localhost:3000
  - Status: ✅ Active
  - Framework: Next.js 13.5.4 with React 18
  - Features: Landing page, authentication, interview interface, dashboards

### ⏳ Backend Services (Requires Docker Desktop)
All backend microservices are configured but require Docker Desktop to be running.

## 📋 Complete Project Structure

### Frontend (`/frontend`)
- **Technology**: Next.js 13.5.4, React 18, TypeScript, Tailwind CSS
- **Key Pages**:
  - `/` - Landing page with hero section
  - `/login` - Authentication
  - `/recruiter` - Recruiter dashboard
  - `/candidate` - Candidate dashboard
  - `/interview` - Interview interface
  - `/interview-setup` - Interview configuration
  - `/demo` - Demo mode
- **Components**: Modern UI with shader animations, video call interface, coding challenges
- **Port**: 3000

### Backend Services (`/backend`)

#### Core Infrastructure Services
1. **API Gateway** (`/backend/api-gateway`)
   - Port: 5001 (mapped from 8080)
   - Technology: FastAPI
   - Role: Single entry point, JWT authentication, request routing
   - Routes: Proxies to all microservices

2. **SSO Service** (`/backend/sso-service`)
   - Port: 8080 (internal)
   - Technology: Flask/Python
   - Role: Authentication, JWT token management

3. **User Service** (`/backend/user-service`)
   - Port: 8080 (internal)
   - Technology: Flask/Python
   - Role: User profiles, organization management

#### Business Services
4. **Interview Service** (`/backend/interview-service`)
   - Port: 8003 (mapped from 8080)
   - Technology: Flask/Python
   - Role: Interview scheduling, lifecycle management, resume processing

5. **Media Service** (`/backend/media-service`)
   - Port: 8080 (internal)
   - Technology: Flask/Python
   - Role: Video/audio file storage and processing

6. **Assessment Service** (`/backend/assessment-service`)
   - Port: 8005 (mapped from 8080)
   - Technology: Flask/Python
   - Role: Score orchestration, report generation

7. **Notification Service** (`/backend/notification-service`)
   - Port: 8080 (internal)
   - Technology: Flask/Python
   - Role: Email/SMS notifications, ATS integrations

#### AI Services
8. **Text Service** (`/backend/text-service`)
   - Port: 8001 (mapped from 8080)
   - Technology: FastAPI/Python
   - Role: Resume parsing, text analysis, RAG, code execution

9. **Audio AI Service** (`/backend/audio-ai-service`)
   - Port: 8000 (mapped from 8080)
   - Technology: FastAPI/Python
   - Role: Speech transcription (Whisper), sentiment analysis

10. **Video AI Service** (`/backend/video-ai-service`)
    - Port: 8080 (internal)
    - Technology: FastAPI/Python
    - Role: Face detection, emotion recognition, gaze tracking, anti-cheating

11. **Text AI Service** (`/backend/text-ai-service`)
    - Port: 8080 (internal)
    - Technology: Flask/Python
    - Role: NLP processing, question generation

12. **Coding Service** (`/backend/coding-service`)
    - Port: 8080 (internal)
    - Technology: Flask/Python
    - Role: Code execution, multi-language support, automated testing

#### Supporting Services
13. **Orchestration Service** (`/backend/orchestration-service`)
    - Port: 8080 (internal)
    - Technology: Flask/Python
    - Role: Multi-modal assessment orchestration

14. **Common Service** (`/backend/common-service`)
    - Port: 8080 (internal)
    - Technology: Flask/Python
    - Role: Shared utilities, database connections

15. **Seq** (Logging Service)
    - Port: 5341, 8081
    - Technology: Datalust Seq
    - Role: Centralized logging and monitoring

## 🗄️ Database
- **Type**: Azure PostgreSQL
- **Connection**: Configured in docker-compose.dev.yml
- **Database Name**: skillscreen_database

## 🚀 How to Start the Full Project

### Step 1: Start Docker Desktop
1. Open Docker Desktop application on Windows
2. Wait for it to fully start (whale icon in system tray)
3. Verify it's running: `docker ps` should work without errors

### Step 2: Start Backend Services
```powershell
# Navigate to project root
cd C:\Users\sheet\Skillscreen\SkillScreen

# Start all services
docker-compose -f docker-compose.dev.yml up -d

# Check status
docker-compose -f docker-compose.dev.yml ps

# View logs
docker-compose -f docker-compose.dev.yml logs -f
```

### Step 3: Verify Services
- **Frontend**: http://localhost:3000 ✅ (Already running)
- **API Gateway**: http://localhost:5001
- **Text Service**: http://localhost:8001
- **Interview Service**: http://localhost:8003
- **Assessment Service**: http://localhost:8005
- **Audio AI Service**: http://localhost:8000
- **Seq Logging**: http://localhost:8081

## 🔧 Service Dependencies

### Required Environment Files
Some services need `.env` files (optional for development):
- `backend/audio-ai-service/.env`
- `backend/interview-service/.env`
- `backend/assessment-service/.env`

These are optional - services will use default values if not present.

### External Dependencies
- **Azure PostgreSQL**: Already configured in docker-compose
- **Judge0 API**: For coding service (optional, can use RapidAPI)
- **AI Models**: Whisper (local), various LLM APIs

## 📊 Architecture Flow

```
Frontend (Next.js)
    ↓
API Gateway (FastAPI)
    ↓
┌─────────────────────────────────────┐
│  Microservices (Flask/FastAPI)      │
│  - User Service                     │
│  - Interview Service                │
│  - Text/Audio/Video AI Services    │
│  - Assessment Service               │
│  - Coding Service                   │
└─────────────────────────────────────┘
    ↓
Azure PostgreSQL Database
```

## 🎨 Key Features

### Frontend Features
- Modern landing page with animated gradients
- Authentication system with JWT
- Recruiter dashboard for managing interviews
- Candidate dashboard for taking interviews
- Real-time interview interface
- Video call integration
- Coding challenge interface

### Backend Features
- Microservices architecture
- JWT-based authentication
- Role-based access control (RBAC)
- Multi-modal AI analysis:
  - Video: Face detection, emotions, gaze tracking
  - Audio: Speech transcription, sentiment
  - Text: Resume parsing, NLP analysis
- Code execution and testing
- Comprehensive assessment scoring

## 🛠️ Development Commands

### Frontend
```powershell
cd frontend
npm install          # Install dependencies
npm run dev         # Start dev server (already running)
npm run build       # Build for production
npm run start       # Start production server
```

### Backend (Docker)
```powershell
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# Stop all services
docker-compose -f docker-compose.dev.yml down

# View logs for specific service
docker-compose -f docker-compose.dev.yml logs -f api-gateway

# Rebuild a service
docker-compose -f docker-compose.dev.yml build api-gateway
docker-compose -f docker-compose.dev.yml up -d api-gateway
```

### Individual Service Development
```powershell
# Example: Run API Gateway locally
cd backend/api-gateway
pip install -r requirements.txt
uvicorn gateway:app --host 0.0.0.0 --port 8080 --reload
```

## 📝 Notes

1. **Docker Desktop Required**: All backend services run in Docker containers
2. **Database**: Uses Azure PostgreSQL (already configured)
3. **Ports**: Frontend uses 3000, backend services use various ports (5001, 8000, 8001, 8003, 8005)
4. **Network**: All services communicate via `skill-screen-network` Docker network
5. **Logging**: Centralized logging via Seq on port 8081

## 🔍 Troubleshooting

### Docker Desktop Not Running
- Error: `The system cannot find the file specified`
- Solution: Start Docker Desktop application

### Port Already in Use
- Check what's using the port: `netstat -ano | findstr :3000`
- Stop the conflicting service or change port in docker-compose

### Services Not Starting
- Check logs: `docker-compose -f docker-compose.dev.yml logs`
- Verify Docker Desktop is running
- Check database connectivity (Azure PostgreSQL)

### Frontend Not Connecting to Backend
- Verify API Gateway is running: http://localhost:5001
- Check CORS settings in API Gateway
- Verify frontend API configuration in `frontend/src/lib/config.ts`

