# IntervuAI Platform - Project Structure

This document outlines the folder structure for our IntervuAI Platform microservices architecture. The project is organized into platform services, business services, and frontend components.

## **📁 Repository Structure**

```
ai-interview-platform/
├── README.md
├── .gitignore
├── .dockerignore
├── docker-compose.yml
├── Makefile
│
├── .github/
│   └── workflows/
│       ├── ci-cd.yml
│       ├── deploy-staging.yml
│       └── deploy-production.yml
│
├── docs/
│   ├── api-specifications.md
│   ├── setup.md
│   ├── prompt-guidelines.md
│   └── deployment.md
│
├── shared/
│   ├── prompts/
│   │   ├── system_prompts/
│   │   ├── templates/
│   │   └── configs/
│   ├── schemas/
│   │   ├── api_schemas/
│   │   └── validation_schemas/
│   └── utils/
│       ├── ai_clients/
│       ├── prompt_management/
│       └── response_parsing/
│
├── backend/
│   ├── api-gateway/
│   │   ├── src/
│   │   │   ├── controllers/
│   │   │   ├── middleware/
│   │   │   ├── routes/
│   │   │   └── utils/
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   └── integration/
│   │   ├── Dockerfile
│   │   ├── .dockerignore
│   │   ├── requirements.txt
│   │   ├── .env.example
│   │   └── README.md
│   │
│   ├── user-service/
│   │   ├── src/
│   │   │   ├── controllers/
│   │   │   ├── models/
│   │   │   ├── services/
│   │   │   ├── routes/
│   │   │   └── utils/
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   └── integration/
│   │   ├── migrations/
│   │   ├── Dockerfile
│   │   ├── .dockerignore
│   │   ├── requirements.txt
│   │   ├── .env.example
│   │   └── README.md
│   │
│   ├── auth-service/
│   │   ├── src/
│   │   │   ├── controllers/
│   │   │   ├── models/
│   │   │   ├── services/
│   │   │   ├── routes/
│   │   │   ├── middleware/
│   │   │   └── utils/
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   └── integration/
│   │   ├── Dockerfile
│   │   ├── .dockerignore
│   │   ├── requirements.txt
│   │   ├── .env.example
│   │   └── README.md
│   │
│   ├── interview-service/
│   │   ├── src/
│   │   │   ├── controllers/
│   │   │   ├── models/
│   │   │   ├── services/
│   │   │   ├── routes/
│   │   │   ├── middleware/
│   │   │   └── utils/
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   └── integration/
│   │   ├── Dockerfile
│   │   ├── .dockerignore
│   │   ├── requirements.txt
│   │   ├── .env.example
│   │   └── README.md
│   │
│   ├── media-service/
│   │   ├── src/
│   │   │   ├── controllers/
│   │   │   ├── services/
│   │   │   ├── routes/
│   │   │   ├── middleware/
│   │   │   └── utils/
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   └── integration/
│   │   ├── storage/
│   │   │   ├── uploads/
│   │   │   └── processed/
│   │   ├── Dockerfile
│   │   ├── .dockerignore
│   │   ├── requirements.txt
│   │   ├── .env.example
│   │   └── README.md
│   │
│   ├── video-ai-service/
│   │   ├── src/
│   │   │   ├── controllers/
│   │   │   ├── services/
│   │   │   ├── models/
│   │   │   │   └── ai_models/
│   │   │   ├── prompts/
│   │   │   ├── config/
│   │   │   ├── routes/
│   │   │   └── utils/
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   ├── integration/
│   │   │   └── fixtures/
│   │   ├── Dockerfile
│   │   ├── .dockerignore
│   │   ├── requirements.txt
│   │   ├── .env.example
│   │   └── README.md
│   │
│   ├── audio-ai-service/
│   │   ├── src/
│   │   │   ├── controllers/
│   │   │   ├── services/
│   │   │   ├── models/
│   │   │   ├── prompts/
│   │   │   ├── config/
│   │   │   ├── routes/
│   │   │   └── utils/
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   ├── integration/
│   │   │   └── fixtures/
│   │   ├── Dockerfile
│   │   ├── .dockerignore
│   │   ├── requirements.txt
│   │   ├── .env.example
│   │   └── README.md
│   │
│   ├── text-ai-service/
│   │   ├── src/
│   │   │   ├── controllers/
│   │   │   ├── services/
│   │   │   ├── models/
│   │   │   ├── prompts/
│   │   │   ├── config/
│   │   │   ├── routes/
│   │   │   └── utils/
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   ├── integration/
│   │   │   └── fixtures/
│   │   │       ├── sample_resumes/
│   │   │       └── sample_responses/
│   │   ├── Dockerfile
│   │   ├── .dockerignore
│   │   ├── requirements.txt
│   │   ├── .env.example
│   │   └── README.md
│   │
│   ├── coding-service/
│   │   ├── src/
│   │   │   ├── controllers/
│   │   │   ├── services/
│   │   │   ├── models/
│   │   │   ├── routes/
│   │   │   ├── sandbox/
│   │   │   │   ├── python/
│   │   │   │   ├── javascript/
│   │   │   │   ├── java/
│   │   │   │   └── cpp/
│   │   │   ├── question_bank/
│   │   │   │   ├── algorithms/
│   │   │   │   ├── data_structures/
│   │   │   │   └── system_design/
│   │   │   ├── prompts/
│   │   │   ├── config/
│   │   │   └── utils/
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   ├── integration/
│   │   │   └── fixtures/
│   │   ├── Dockerfile
│   │   ├── .dockerignore
│   │   ├── requirements.txt
│   │   ├── .env.example
│   │   └── README.md
│   │
│   ├── assessment-service/
│   │   ├── src/
│   │   │   ├── controllers/
│   │   │   ├── services/
│   │   │   ├── models/
│   │   │   ├── routes/
│   │   │   ├── prompts/
│   │   │   ├── config/
│   │   │   └── utils/
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   ├── integration/
│   │   │   └── fixtures/
│   │   ├── Dockerfile
│   │   ├── .dockerignore
│   │   ├── requirements.txt
│   │   ├── .env.example
│   │   └── README.md
│   │
│   ├── logger-service/
│   │   ├── src/
│   │   │   ├── controllers/
│   │   │   ├── services/
│   │   │   ├── routes/
│   │   │   └── utils/
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   └── integration/
│   │   ├── config/
│   │   │   ├── elasticsearch/
│   │   │   ├── logstash/
│   │   │   └── kibana/
│   │   ├── Dockerfile
│   │   ├── .dockerignore
│   │   ├── requirements.txt
│   │   ├── .env.example
│   │   └── README.md
│   │
│   └── notification-service/
│       ├── src/
│       │   ├── controllers/
│       │   ├── services/
│       │   ├── templates/
│       │   │   ├── email/
│       │   │   └── pdf/
│       │   ├── routes/
│       │   └── utils/
│       ├── tests/
│       │   ├── unit/
│       │   └── integration/
│       ├── Dockerfile
│       ├── .dockerignore
│       ├── requirements.txt
│       ├── .env.example
│       └── README.md
│
└── frontend/
    ├── public/
    ├── src/
    │   ├── components/
    │   ├── pages/
    │   ├── hooks/
    │   ├── services/
    │   └── utils/
    ├── tests/
    ├── Dockerfile
    ├── Dockerfile.dev
    ├── .dockerignore
    ├── package.json
    ├── .env.example
    └── README.md
```

## **📋 Service Organization**

### **Backend Services** (SSO-based Architecture)
All services are organized under the `backend/` folder as part of a Single Sign-On (SSO) architecture:

#### **Platform Services**
- **`api-gateway/`** - Single entry point for all client requests, JWT authentication verification, request routing, response aggregation, rate limiting, and client-specific response formatting
- **`auth-service/`** - Role-based access control (Recruiter, Candidate, Hiring Manager, Team Lead, HR), JWT token generation and validation, session management, permission enforcement
- **`user-service/`** - User registration and authentication, profile management, organization and team management

#### **Business Services**
- **`interview-service/`** - Interview scheduling with calendar integration, session lifecycle management, question template storage, candidate onboarding workflow, interview state management
- **`media-service/`** - Media retrieval and file management, video/audio editing and trimming, highlight extraction, format conversion, thumbnail generation, multi-track synchronization, quality enhancement
- **`video-ai-service/`** - Face detection and tracking, facial expression analysis, gaze estimation, head pose analysis, body language assessment, anti-cheating detection, environment analysis, engagement scoring
- **`audio-ai-service/`** - Speech-to-text transcription, vocal pattern analysis (pitch, tone, pace), sentiment analysis, confidence detection, speaking fluency assessment, text-to-speech synthesis, communication scoring
- **`text-ai-service/`** - Resume parsing and skill extraction, interview question generation from job descriptions, text response analysis, STAR method detection, bias detection, report generation, semantic analysis
- **`coding-service/`** - Coding question management by field and difficulty, in-browser code editor, automated test execution, sandboxed code execution with security isolation, multi-language support (Python, Java, JavaScript, C++), real-time feedback
- **`assessment-service/`** - Assessment orchestration across all AI services, multi-modal score combination, final candidate assessment generation, evidence linking, workflow management, score weighting customization
- **`logger-service/`** - Centralized log aggregation, real-time log streaming and search, system metrics collection, error tracking and alerting, performance monitoring, audit trail maintenance
- **`notification-service/`** - ATS integrations (Greenhouse, Lever, Workable), email and SMS notifications, PDF report generation, webhook management, data export (CSV, JSON), third-party API orchestration

### **Shared Resources**
- **`shared/`** - Common AI client utilities, prompt templates and management, response parsing utilities, API schemas and validation
- **`docs/`** - Technical documentation, API specifications, prompt engineering guidelines
- **`frontend/`** - React/Next.js web application for interview management and candidate interaction

## **🔧 Technical Standards**

Each service follows consistent patterns:
- **Flask application** with application factory pattern
- **Docker containerization** (Dockerfile, Dockerfile.dev)
- **Comprehensive testing** (unit, integration)
- **Environment configuration** (.env.example, requirements.txt)
- **AI services** include dedicated prompt management and configuration

## **🔌 Key Service Dependencies**

### **External APIs & Libraries**
- **Video Processing**: FFmpeg, OpenCV, MediaPipe
- **AI/ML Services**: OpenAI, Claude, Azure TTS, ElevenLabs, Google TTS
- **Calendar Integration**: Google Calendar, Outlook APIs
- **Email Services**: SendGrid, AWS SES
- **ATS Providers**: Greenhouse, Lever, Workable
- **Container Orchestration**: Docker Swarm (for secure code execution)
- **Monitoring**: Grafana, Elasticsearch, Logstash, Kibana

### **Inter-Service Communication**
- **interview-service** → user-service, AI services, calendar APIs
- **media-service** → cloud storage, video processing libraries
- **AI services** → GenAI APIs, media-service (for data input)
- **assessment-service** → all AI services, interview-service
- **coding-service** → text-ai-service, assessment-service, logger-service
- **notification-service** → ATS APIs, email services, AI services (for reports)

## **📊 Standard API Response Format**

All services follow consistent response patterns:
```json
{
  "success": true,
  "data": { /* actual response data */ },
  "meta": {
    "timestamp": "2024-01-15T10:30:00.000Z",
    "request_id": "req_abc123",
    "version": "v1"
  }
}
```

## **⚠️ Development Guidelines**

**Feel free to modify the folder structures within individual services according to your team's specific needs and preferences. However, please try to maintain the current overall organization structure for consistency across the project.**

- Keep the separation between `/backend/` and `/frontend/`
- All backend services are organized under `/backend/` for SSO-based architecture
- Maintain consistent Docker and testing patterns
- Use the `/shared/` directory for common utilities
- Follow the established naming conventions for new services

Each service should remain independently deployable and maintainable while being part of the unified backend architecture.