# 🚀 SkillScreen Deployment & Setup Guide

## 📋 Table of Contents
1. [Security Setup](#security-setup)
2. [Environment Configuration](#environment-configuration)
3. [Local Development Setup](#local-development-setup)
4. [Production Deployment](#production-deployment)
5. [GitHub Workflow](#github-workflow)
6. [Next Steps](#next-steps)

---

## 🔒 Security Setup

### ⚠️ **CRITICAL: API Key Security**

**Never commit API keys to GitHub!** The following files contain sensitive information:

- `backend/interview-service/.env` (contains your actual API key)
- `backend/interview-service/config.json` (API key removed, but keep secure)

### 🔧 **Step 1: Secure Your API Key**

1. **Create a local `.env` file:**
   ```bash
   cd backend/interview-service
   cp env.example .env
   ```

2. **Edit `.env` with your actual API key:**
   ```bash
   # Edit the file and replace with your actual API key
   GEMINI_API_KEY=AIzaSyAR8QK4VKXWkcWUv399pvQ5BOcIJ0qZxTw
   ```

3. **Verify `.gitignore` includes `.env`:**
   ```gitignore
   .env
   .env.local
   .env.production
   ```

---

## ⚙️ Environment Configuration

### **Step 2: Configure Environment Variables**

**Required Variables:**
```bash
# API Configuration
GEMINI_API_KEY=your_actual_api_key_here

# Application Settings
DEBUG=false
ENVIRONMENT=development
VERSION=1.0.0

# Interview Configuration
MAX_QUESTIONS=9
MIN_QUESTIONS=9
OFF_TOPIC_THRESHOLD=0.3
MAX_OFF_TOPIC_RESPONSES=3
DEFAULT_INTERVIEW_TYPE=mixed
DEFAULT_DIFFICULTY=medium

# LLM Configuration
LLM_MODEL_NAME=models/gemini-2.5-flash
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=200
LLM_TIMEOUT=30

# UI Configuration
STREAMLIT_SERVER_PORT=8502
STREAMLIT_SERVER_ADDRESS=0.0.0.0
UI_THEME=light

# Security
SECRET_KEY=your_secret_key_here
SESSION_TIMEOUT=3600
MAX_SESSIONS=100
ENABLE_ENCRYPTION=true
```

---

## 🏠 Local Development Setup

### **Step 3: Install Dependencies**

```bash
# Navigate to the project directory
cd Chat_Interview

# Install backend dependencies
cd backend/interview-service
pip install -r requirements_production.txt

# Install frontend dependencies
cd ../../frontend/streamlit-app
pip install streamlit reportlab requests
```

### **Step 4: Start the Applications**

**Terminal 1 - Start FastAPI Backend:**
```bash
cd backend/interview-service
python simple_fastapi_app.py
```
- Backend will be available at: `http://localhost:8000`
- API documentation: `http://localhost:8000/docs`

**Terminal 2 - Start Streamlit Frontend:**
```bash
cd frontend/streamlit-app
streamlit run streamlit_frontend.py --server.port 8502
```
- Frontend will be available at: `http://localhost:8502`

### **Step 5: Test the Integration**

1. **Open your browser** and go to `http://localhost:8502`
2. **Upload a resume** (PDF, DOCX, or paste text)
3. **Provide job description** details
4. **Start the interview** and complete all 9 questions
5. **Download the summary** in PDF, Text, or JSON format

---

## 🚀 Production Deployment

### **Step 6: Docker Setup (Recommended)**

**Create `docker-compose.prod.yml`:**
```yaml
version: '3.8'
services:
  backend:
    build: ./backend/interview-service
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - ENVIRONMENT=production
    volumes:
      - ./logs:/app/logs

  frontend:
    build: ./frontend/streamlit-app
    ports:
      - "8502:8502"
    depends_on:
      - backend
    environment:
      - API_BASE_URL=http://backend:8000
```

**Deploy with Docker:**
```bash
# Set environment variables
export GEMINI_API_KEY="your_api_key_here"

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps
```

### **Step 7: Cloud Deployment Options**

**Option A: AWS EC2**
```bash
# Launch EC2 instance
# Install Docker
sudo yum update -y
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker

# Clone repository
git clone https://github.com/AIP-F25-2/SkillScreen.git
cd SkillScreen

# Set environment variables
export GEMINI_API_KEY="your_api_key_here"

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

**Option B: Google Cloud Run**
```bash
# Build and push images
gcloud builds submit --tag gcr.io/PROJECT_ID/skillscreen-backend ./backend/interview-service
gcloud builds submit --tag gcr.io/PROJECT_ID/skillscreen-frontend ./frontend/streamlit-app

# Deploy to Cloud Run
gcloud run deploy skillscreen-backend --image gcr.io/PROJECT_ID/skillscreen-backend --platform managed --region us-central1 --allow-unauthenticated

gcloud run deploy skillscreen-frontend --image gcr.io/PROJECT_ID/skillscreen-frontend --platform managed --region us-central1 --allow-unauthenticated
```

---

## 🔄 GitHub Workflow

### **Step 8: Create Pull Request**

1. **Go to GitHub:** [https://github.com/AIP-F25-2/SkillScreen/pull/new/frontend/fastapi-streamlit-integration](https://github.com/AIP-F25-2/SkillScreen/pull/new/frontend/fastapi-streamlit-integration)

2. **Fill in PR details:**
   - **Title:** `feat: Add FastAPI + Streamlit integration for SkillScreen`
   - **Description:** 
     ```markdown
     ## 🎯 Overview
     This PR adds a complete FastAPI + Streamlit integration for the SkillScreen AI Interview Assistant.
     
     ## ✨ Features Added
     - 9-question interview structure (3 rounds: General, Technical, Theoretical)
     - AI-powered question generation and evaluation
     - Human-like AI summaries with downloadable reports
     - Anti-cheating mechanisms and context validation
     - Professional PDF, Text, and JSON report generation
     
     ## 🏗️ Architecture
     - **Backend:** FastAPI service in `backend/interview-service/`
     - **Frontend:** Streamlit app in `frontend/streamlit-app/`
     - **Shared:** Pydantic schemas in `shared/schemas/`
     
     ## 🧪 Testing
     - [x] Backend API endpoints tested
     - [x] Frontend integration verified
     - [x] Interview flow completed end-to-end
     - [x] Report generation working
     
     ## 📋 Next Steps
     - [ ] Code review and feedback
     - [ ] Integration with existing services
     - [ ] Production deployment
     - [ ] Performance optimization
     ```

3. **Request reviewers:** Add team members for code review

4. **Add labels:** `enhancement`, `frontend`, `backend`, `integration`

### **Step 9: Code Review Process**

**Review Checklist:**
- [ ] Code follows project conventions
- [ ] Security best practices implemented
- [ ] API endpoints are well-documented
- [ ] Error handling is comprehensive
- [ ] Tests are included (if applicable)
- [ ] Documentation is updated

**Address Feedback:**
```bash
# Make changes based on feedback
git add .
git commit -m "fix: Address code review feedback"
git push origin frontend/fastapi-streamlit-integration
```

---

## 📈 Next Steps

### **Immediate Actions (Week 1)**

1. **✅ Complete Current PR**
   - Address any code review feedback
   - Merge to main branch
   - Update documentation

2. **🔧 Production Setup**
   - Set up production environment
   - Configure monitoring and logging
   - Implement backup strategies

3. **🧪 Testing & QA**
   - Load testing for concurrent users
   - Security penetration testing
   - User acceptance testing

### **Short-term Goals (Month 1)**

4. **🗄️ Database Integration**
   - Implement PostgreSQL database
   - Add user authentication
   - Create audit trails

5. **🔗 Service Integration**
   - Connect with existing microservices
   - Implement ATS integrations
   - Add notification services

6. **📊 Analytics & Monitoring**
   - Add performance metrics
   - Implement user analytics
   - Set up alerting systems

### **Medium-term Goals (Month 2-3)**

7. **🎥 Advanced Features**
   - Video interview capabilities
   - Audio analysis and transcription
   - Real-time collaboration features

8. **🤖 AI Enhancements**
   - Advanced NLP models
   - Sentiment analysis
   - Bias detection and mitigation

9. **🌐 Scalability**
   - Kubernetes deployment
   - Auto-scaling configuration
   - CDN integration

### **Long-term Vision (Month 4+)**

10. **🏢 Enterprise Features**
    - Multi-tenant architecture
    - Advanced reporting and analytics
    - Custom branding and white-labeling

11. **🔒 Security & Compliance**
    - SOC 2 compliance
    - GDPR compliance
    - Advanced security features

12. **🌍 Global Expansion**
    - Multi-language support
    - Regional deployment
    - Local compliance requirements

---

## 🆘 Troubleshooting

### **Common Issues**

**Issue 1: API Key Not Working**
```bash
# Check if .env file exists and has correct API key
cat backend/interview-service/.env | grep GEMINI_API_KEY

# Verify API key is valid
curl -H "Authorization: Bearer YOUR_API_KEY" https://generativelanguage.googleapis.com/v1/models
```

**Issue 2: Port Already in Use**
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process
taskkill /PID <PID_NUMBER> /F

# Or use different port
python simple_fastapi_app.py --port 8001
```

**Issue 3: Dependencies Installation Failed**
```bash
# Update pip
python -m pip install --upgrade pip

# Install with verbose output
pip install -r requirements_production.txt -v

# Try alternative installation
pip install --no-cache-dir -r requirements_production.txt
```

### **Getting Help**

- **GitHub Issues:** [https://github.com/AIP-F25-2/SkillScreen/issues](https://github.com/AIP-F25-2/SkillScreen/issues)
- **Documentation:** Check the `docs/` folder for detailed guides
- **Team Communication:** Use project communication channels

---

## 📞 Support

For technical support or questions:
- **Email:** [team@skillscreen.ai](mailto:team@skillscreen.ai)
- **Slack:** #skillscreen-dev
- **GitHub:** [@AIP-F25-2](https://github.com/AIP-F25-2)

---

**🎉 Congratulations! You've successfully set up the SkillScreen FastAPI + Streamlit integration!**

*Last updated: October 2024*
