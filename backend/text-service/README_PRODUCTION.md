# SkillScreen Production System

## Overview

SkillScreen is an enterprise-grade AI-powered interview platform that provides automated candidate screening with advanced NLP analysis, anti-cheating mechanisms, and comprehensive explainability.

## Architecture

### Core Components

1. **FastAPI Backend** - RESTful API with async support
2. **PostgreSQL Database** - Persistent storage with audit trails
3. **Redis** - Caching and background task queuing
4. **NLP Service** - Advanced text analysis using Hugging Face models
5. **Anti-Cheating Service** - Behavioral analysis and duplicate detection
6. **RAG Explainability** - Evidence-based decision explanations
7. **Monitoring Stack** - Prometheus, Grafana, and health checks

### Key Features

- **Dynamic Resume Parsing** - AI-powered extraction of candidate information
- **Job Description Analysis** - Automated skill mapping and requirement extraction
- **Multi-Round Interviews** - General, Technical, and Theoretical assessment rounds
- **Advanced Scoring** - Multi-criteria evaluation with explainable results
- **Anti-Cheating Detection** - Duplicate response detection, timing analysis, behavioral patterns
- **Comprehensive Reporting** - PDF, JSON, and text export formats
- **Audit Trails** - Complete logging for compliance and transparency

## Production Deployment

### Prerequisites

- Docker and Docker Compose
- Kubernetes cluster (for K8s deployment)
- PostgreSQL 15+
- Redis 7+
- Python 3.11+

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://skillscreen:password@localhost:5432/skillscreen
POSTGRES_PASSWORD=your_secure_password

# Redis
REDIS_URL=redis://localhost:6379

# AI Services
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key

# Security
SECRET_KEY=your_secret_key
JWT_SECRET=your_jwt_secret

# Monitoring
GRAFANA_PASSWORD=your_grafana_password
```

### Docker Compose Deployment

1. **Clone and Setup**
```bash
git clone <repository>
cd SkillScreen
cp .env.example .env
# Edit .env with your configuration
```

2. **Start Services**
```bash
docker-compose up -d
```

3. **Initialize Database**
```bash
docker-compose exec api python -c "from database.database import db_manager; db_manager._initialize_database()"
```

4. **Access Services**
- API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

### Kubernetes Deployment

1. **Create Namespace**
```bash
kubectl create namespace skillscreen
```

2. **Deploy Database**
```bash
kubectl apply -f k8s/database.yaml
```

3. **Deploy Application**
```bash
kubectl apply -f k8s/deployment.yaml
```

4. **Deploy Monitoring**
```bash
kubectl apply -f k8s/monitoring.yaml
```

5. **Verify Deployment**
```bash
kubectl get pods -n skillscreen
kubectl get services -n skillscreen
```

## API Documentation

### Core Endpoints

#### Candidates
- `POST /api/candidates/` - Create candidate
- `GET /api/candidates/{id}` - Get candidate details

#### Jobs
- `POST /api/jobs/` - Create job posting
- `GET /api/jobs/{id}` - Get job details

#### Interviews
- `POST /api/interviews/start` - Start interview
- `POST /api/interviews/{session_id}/respond` - Submit response
- `GET /api/interviews/{session_id}/status` - Get interview status
- `GET /api/interviews/{session_id}/summary` - Get interview summary

#### File Operations
- `POST /api/upload/resume` - Upload resume file
- `GET /api/interviews/{session_id}/export/pdf` - Export PDF report

### Authentication

The API uses JWT tokens for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Configuration

### Database Configuration

The system supports PostgreSQL with the following features:
- Connection pooling
- Automatic migrations
- Audit logging
- Backup and recovery

### AI Model Configuration

The NLP service supports multiple AI providers:
- Google Gemini (primary)
- OpenAI GPT (fallback)
- Hugging Face Transformers (local models)

### Anti-Cheating Configuration

Configurable thresholds for:
- Duplicate response detection
- Timing analysis
- Behavioral pattern analysis
- Content analysis

## Monitoring and Observability

### Metrics

The system exposes Prometheus metrics for:
- API request rates and latency
- Database performance
- AI model usage
- Anti-cheating detection rates
- Interview completion rates

### Logging

Structured logging with:
- Request/response logging
- Error tracking
- Audit trails
- Performance metrics

### Health Checks

All services include health check endpoints:
- `/api/health` - API health status
- Database connectivity checks
- Redis connectivity checks
- AI service availability

## Security

### Data Protection
- Encryption at rest and in transit
- PII data masking
- Secure file uploads
- API rate limiting

### Compliance
- GDPR compliance features
- Audit trail retention
- Data deletion capabilities
- Privacy controls

## Performance

### Scalability
- Horizontal scaling with Kubernetes
- Database connection pooling
- Redis caching
- Async request processing

### Optimization
- Model caching
- Response compression
- CDN integration
- Database indexing

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check PostgreSQL status
   - Verify connection string
   - Check network connectivity

2. **AI Service Failures**
   - Verify API keys
   - Check rate limits
   - Monitor fallback mechanisms

3. **Performance Issues**
   - Check resource utilization
   - Monitor database performance
   - Review caching effectiveness

### Logs

Access logs through:
- Docker: `docker-compose logs -f api`
- Kubernetes: `kubectl logs -f deployment/skillscreen-api -n skillscreen`

### Debugging

Enable debug mode by setting:
```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

## Development

### Local Development

1. **Setup Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements_production.txt
```

2. **Run Database**
```bash
docker-compose up -d postgres redis
```

3. **Run Application**
```bash
uvicorn fastapi_app:app --reload --host 0.0.0.0 --port 8000
```

### Testing

Run the test suite:
```bash
pytest tests/ -v --cov=.
```

### Code Quality

Format code:
```bash
black .
flake8 .
mypy .
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

## Roadmap

### Upcoming Features
- Video interview analysis
- Audio processing with Whisper
- ATS integrations (Greenhouse, Lever, Workable)
- Advanced analytics dashboard
- Multi-language support
- Mobile applications

### Performance Improvements
- Model optimization
- Caching strategies
- Database optimization
- CDN integration
