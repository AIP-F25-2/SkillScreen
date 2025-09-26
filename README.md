# IntervuAI

> **Next-generation AI-powered interview assessment platform for comprehensive candidate evaluation**

[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.9+-green)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18+-blue)](https://reactjs.org/)

## 📖 Overview

The IntervuAI is a comprehensive microservices-based solution that revolutionizes the interview process through advanced AI analysis. Our platform provides real-time assessment of candidates across multiple dimensions including video analysis, speech patterns, coding skills, and behavioral insights.

### 🎯 Key Features

- **🎥 Advanced Video Analysis** - Face detection, emotion recognition, gaze tracking, and anti-cheating detection
- **🎙️ Speech Intelligence** - Real-time transcription, sentiment analysis, confidence detection, and communication scoring  
- **📄 Smart Text Processing** - Resume parsing, STAR method detection, bias analysis, and automated report generation
- **💻 Code Assessment** - Multi-language code execution, automated testing, and real-time feedback
- **📊 Comprehensive Analytics** - Multi-modal assessment orchestration and detailed candidate scoring
- **🔒 Enterprise Security** - Role-based access control, JWT authentication, and secure sandboxed execution
- **🔗 ATS Integration** - Seamless integration with Greenhouse, Lever, Workable, and other ATS platforms

## 🏗️ Architecture

Our platform follows a **microservices architecture** with clear separation between platform services (infrastructure) and business services (domain logic).

### Platform Services
- **API Gateway** - Single entry point, request routing, authentication verification
- **Auth Service** - JWT management, role-based access control, session management
- **User Service** - User profiles, organization management, team handling

### Business Services  
- **Interview Service** - Scheduling, lifecycle management, question templates
- **Media Service** - Video/audio processing, file storage, highlight extraction
- **Video AI Service** - Facial analysis, emotion detection, engagement scoring
- **Audio AI Service** - Speech analysis, transcription, sentiment detection
- **Text AI Service** - Resume parsing, question generation, response analysis
- **Coding Service** - Code execution, multi-language support, automated testing
- **Assessment Service** - Score orchestration, report generation, evidence linking
- **Logger Service** - Centralized logging, monitoring, audit trails
- **Notification Service** - Email/SMS notifications, ATS integrations, webhook management

> 📋 **Detailed Architecture**: See [docs/architecture.md](docs/architecture.md) for complete technical specifications



## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Git (for cloning the repository)

### Running the Platform

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd SkillScreen
   ```

2. **Start all services**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

3. **Check service status**
   ```bash
   docker-compose -f docker-compose.dev.yml ps
   ```

4. **View service logs**
   ```bash
   docker-compose -f docker-compose.dev.yml logs -f
   ```

5. **Stop all services**
   ```bash
   docker-compose -f docker-compose.dev.yml down
   ```

### Access Points
- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:5000
- **Individual Services**: http://localhost:5001-5011

### Service Ports
| Service | Port | Description |
|---------|------|-------------|
| API Gateway | 5000 | Main entry point |
| User Service | 5001 | User management |
| Auth Service | 5002 | Authentication |
| Interview Service | 5003 | Interview management |
| Media Service | 5004 | Media processing |
| Assessment Service | 5005 | Score orchestration |
| Notification Service | 5006 | Notifications |
| Logger Service | 5007 | Centralized logging |
| Text AI Service | 5008 | Text processing |
| Audio AI Service | 5009 | Speech analysis |
| Video AI Service | 5010 | Video analysis |
| Coding Service | 5011 | Code execution |

## 📁 Project Structure

```
ai-interview-platform/
├── frontend/                 # React web application
├── backend/                  # All backend services
│   ├── api-gateway/         # Request routing & authentication
│   ├── auth-service/        # JWT & role-based access control
│   ├── user-service/        # User & organization management
│   ├── interview-service/   # Interview lifecycle management
│   ├── media-service/       # Video/audio processing
│   ├── video-ai-service/    # Video analysis & emotion detection
│   ├── audio-ai-service/    # Speech analysis & transcription
│   ├── text-ai-service/     # Text processing & NLP
│   ├── coding-service/      # Code execution & assessment
│   ├── assessment-service/  # Score orchestration
│   ├── logger-service/      # Centralized logging
│   └── notification-service/ # Notifications & integrations
├── shared/                   # Common utilities & schemas
├── docs/                    # Technical documentation
└── .github/                 # CI/CD workflows
```

## 🛠️ Technology Stack

### Backend Services
- **Framework**: Flask (Python)
- **Authentication**: JWT, Role-based Access Control
- **Databases**: PostgreSQL, Redis
- **Message Queue**: Redis/RabbitMQ
- **Container**: Docker, Kubernetes

### AI & ML Services
- **Computer Vision**: OpenCV, MediaPipe
- **Speech Processing**: OpenAI Whisper, Azure Speech
- **NLP**: OpenAI GPT, Claude, Hugging Face
- **Text-to-Speech**: ElevenLabs, Azure TTS
- **Video Processing**: FFmpeg

### Frontend
- **Framework**: React 18+
- **Styling**: Tailwind CSS
- **State Management**: Redux Toolkit
- **Testing**: Jest, React Testing Library

### DevOps & Infrastructure
- **Containerization**: Docker, Docker Compose
- **Orchestration**: Kubernetes
- **Monitoring**: Grafana, Prometheus, ELK Stack
- **CI/CD**: GitHub Actions
- **Cloud**: AWS/Azure/GCP ready



## 🔌 API Documentation

Each service will provide comprehensive API documentation with standardized response formats and versioned endpoints following REST conventions.

## 🧪 Testing

The platform will maintain high test coverage across all services with unit tests, integration tests, and end-to-end testing for comprehensive quality assurance.

## 🚀 Deployment

The platform is designed for containerized deployment with support for development, staging, and production environments using Docker and Kubernetes orchestration.

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes in the appropriate service folder
4. Run tests to ensure quality
5. Commit your changes with descriptive messages
6. Push to your branch
7. Open a Pull Request

### Service Development Guidelines
- Each service should be independently deployable
- Follow the established folder structure within services
- Include comprehensive tests (unit + integration)
- Update documentation for API changes
- Use the shared utilities for common functionality

## 📊 Monitoring & Observability

- **Metrics**: Prometheus + Grafana dashboards
- **Logging**: Centralized logging via logger-service  
- **Tracing**: Distributed tracing across microservices
- **Health Checks**: Individual service health endpoints
- **Alerting**: Configurable alerts for system metrics

## 🔒 Security

- **Authentication**: JWT-based with refresh tokens
- **Authorization**: Fine-grained role-based access control
- **Code Execution**: Sandboxed environments with security isolation
- **Data Protection**: Encryption at rest and in transit
- **API Security**: Rate limiting, input validation, CORS protection
- **Anti-Cheating**: Multi-modal detection systems

<div align="center">

**Built with ❤️ by the IntervuAI Team**

[⭐ Star us on GitHub](https://github.com/your-org/ai-interview-platform) | [🐛 Report Bug](https://github.com/your-org/ai-interview-platform/issues) | [💡 Request Feature](https://github.com/your-org/ai-interview-platform/issues)

</div>