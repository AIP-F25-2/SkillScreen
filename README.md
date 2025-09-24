# SkillScreen Backend Services

A comprehensive microservices-based backend system for AI-powered interview assessment platform.

## 🏗️ Architecture

This project implements a microservices architecture with 12 independent services:

| Service | Port | Description | Technology |
|---------|------|-------------|------------|
| API Gateway | 5000 | Request routing and orchestration | Flask |
| User Service | 5001 | User management and CRUD operations | Flask + PostgreSQL |
| Auth Service | 5002 | Authentication and JWT management | Flask + PostgreSQL |
| Interview Service | 5003 | Interview scheduling and management | Flask + PostgreSQL |
| Media Service | 5004 | File upload and media processing | Flask |
| Video AI Service | 5005 | Video analysis and processing | Flask |
| Audio AI Service | 5006 | Audio analysis and speech processing | Flask |
| Text AI Service | 5007 | Text analysis and NLP | Flask |
| Assessment Service | 5008 | Assessment creation and scoring | Flask + PostgreSQL |
| Coding Service | 5009 | Code execution and sandbox | Flask |
| Logger Service | 5010 | Centralized logging | Flask |
| Notification Service | 5011 | Email and SMS notifications | Flask |

## 🚀 Quick Start

### Prerequisites

- **Docker Desktop** (v20.10+)
- **Docker Compose** (v2.0+)
- **Python 3.7+** (for testing scripts)
- **Make** (optional, for advanced commands)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd SkillScreen
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start all services:**

   **Option 1: Using Make (Recommended)**
   ```bash
   make start
   ```

   **Option 2: Using PowerShell (Windows)**
   ```powershell
   .\start-services.ps1
   ```

   **Option 3: Using Docker Compose directly**
   ```bash
   docker-compose up --build -d
   ```

4. **Verify services are running:**
   ```bash
   make health
   # or
   python test-services.py
   ```

## 🔧 Development Commands

### Using Make (Cross-platform)

```bash
# Start all services
make start

# Stop all services
make stop

# Restart all services
make restart

# View logs
make logs

# Run tests
make test

# Check service health
make health

# Clean up everything
make clean

# Get help
make help
```

### Using PowerShell (Windows)

```powershell
# Start services with health checks
.\start-services.ps1

# Start with verbose output
.\start-services.ps1 -Verbose

# Start without health checks
.\start-services.ps1 -SkipHealthCheck

# Get help
.\start-services.ps1 -Help
```

### Using Docker Compose

```bash
# Start all services
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart specific service
docker-compose restart api-gateway

# Access service shell
docker-compose exec api-gateway /bin/bash
```

## 🧪 Testing

### Automated Testing

```bash
# Run comprehensive connectivity tests
python test-services.py

# Test specific service
curl http://localhost:5000/health
```

### Manual Testing Examples

```bash
# Test API Gateway routing
curl http://localhost:5000/route-test

# Test authentication flow
curl -X POST http://localhost:5002/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "testpass"}'

# Test AI services
curl -X POST http://localhost:5007/analyze-text \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a test text for analysis"}'
```

## 📊 Monitoring

### Health Checks

All services expose health check endpoints:

```bash
# Check individual service
curl http://localhost:<port>/health

# Check all services through gateway
curl http://localhost:5000/route-test
```

### Service URLs

- **API Gateway**: http://localhost:5000
- **User Service**: http://localhost:5001
- **Auth Service**: http://localhost:5002
- **Interview Service**: http://localhost:5003
- **Media Service**: http://localhost:5004
- **Video AI Service**: http://localhost:5005
- **Audio AI Service**: http://localhost:5006
- **Text AI Service**: http://localhost:5007
- **Assessment Service**: http://localhost:5008
- **Coding Service**: http://localhost:5009
- **Logger Service**: http://localhost:5010
- **Notification Service**: http://localhost:5011

## 🔒 Security

### Environment Variables

Never commit sensitive data. Use the `.env` file for configuration:

```bash
# Copy example configuration
cp .env.example .env

# Edit with your values
nano .env
```

### JWT Configuration

```bash
# Generate a strong JWT secret
JWT_SECRET=$(openssl rand -base64 32)
```

### Database Security

- Change default PostgreSQL password
- Use environment variables for credentials
- Enable SSL in production

## 🏭 Production Deployment

### Environment Setup

```bash
# Set production environment
export ENVIRONMENT=production

# Use production configuration
cp .env.production .env
```

### Docker Compose Production

```bash
# Start in production mode
make prod

# Or with Docker Compose
ENVIRONMENT=production docker-compose up --build -d
```

### Health Monitoring

```bash
# Set up monitoring
make monitor

# Check service status
make status
```

## 🐛 Troubleshooting

### Common Issues

1. **Docker not running:**
   ```bash
   # Start Docker Desktop
   # Check Docker status
   docker info
   ```

2. **Port conflicts:**
   ```bash
   # Check port usage
   netstat -an | grep :5000
   
   # Stop conflicting services
   docker-compose down
   ```

3. **Service not starting:**
   ```bash
   # Check logs
   docker-compose logs <service-name>
   
   # Restart service
   docker-compose restart <service-name>
   ```

4. **Database connection issues:**
   ```bash
   # Check PostgreSQL
   docker-compose logs postgres
   
   # Reset database
   make db-reset
   ```

### Debug Commands

```bash
# View all container logs
docker-compose logs -f

# Access service shell
make shell-service SERVICE=api-gateway

# Check resource usage
make monitor

# Database shell access
make db-shell
```

## 📁 Project Structure

```
SkillScreen/
├── backend/                 # Backend services
│   ├── api-gateway/        # API Gateway service
│   ├── auth-service/       # Authentication service
│   ├── user-service/       # User management service
│   ├── interview-service/  # Interview management
│   ├── media-service/      # File handling
│   ├── video-ai-service/   # Video AI processing
│   ├── audio-ai-service/   # Audio AI processing
│   ├── text-ai-service/    # Text AI processing
│   ├── assessment-service/ # Assessment management
│   ├── coding-service/     # Code execution
│   ├── logger-service/     # Centralized logging
│   └── notification-service/ # Notifications
├── shared/                 # Shared utilities
│   ├── database.py        # Database connection
│   ├── jwt_utils.py       # JWT utilities
│   └── requirements.txt   # Common dependencies
├── docker-compose.yml     # Service orchestration
├── Makefile              # Build automation
├── start-services.ps1    # PowerShell startup script
├── test-services.py      # Testing script
├── .env.example          # Environment template
└── README.md            # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Development Workflow

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes
# ...

# Test changes
make test

# Commit changes
git commit -m "Add new feature"

# Push branch
git push origin feature/new-feature
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check this README and inline code comments
- **Issues**: Create an issue in the repository
- **Logs**: Use `make logs` or `docker-compose logs` for debugging

## 🔄 Updates

To update the services:

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
make restart

# Verify everything works
make test
```

---

**Built with ❤️ for professional development**