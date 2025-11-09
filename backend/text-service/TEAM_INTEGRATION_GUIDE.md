# SkillScreen - AI-Powered Interview Platform

## 🚀 Quick Start Guide for Team Members

### Overview
SkillScreen is an end-to-end automated interviewing platform that generates role-tailored interviews from resumes, job descriptions, or recruiter-specified skills. It features AI-powered question generation, multi-modal assessment, and comprehensive scoring.

### 🏗️ Architecture

```
├── backend/
│   └── text-service/          # Main AI logic service (NEW!)
│       ├── services/          # Core services (LLM, Code Execution, etc.)
│       ├── utils/            # Utilities (Resume Parser, Logger)
│       ├── database/         # Database models and connections
│       └── simple_fastapi_app.py  # Main FastAPI application
├── frontend/
│   └── streamlit-app/        # Streamlit frontend
└── shared/
    └── schemas/              # Shared data schemas
```

### 🔧 Integration with text-service

The `backend/text-service` is the main service your team should integrate with. It provides:

#### **Core APIs:**
- **Interview Management**: `/interviews/start`, `/interviews/{session_id}/respond`
- **Candidate Management**: `/candidates` (POST)
- **Job Management**: `/jobs` (POST)
- **Code Execution**: `/api/code/execute`, `/api/code/languages`
- **Health Check**: `/health`

#### **Key Services:**
1. **Enhanced LLM Service**: Multi-API integration (Gemini, Wolfram Alpha, SerpApi)
2. **Resume Parser**: Intelligent parsing with experience calculation
3. **Code Execution Service**: Sandboxed code execution for technical assessments
4. **Anti-cheating Service**: Response similarity detection

### 🛠️ Setup Instructions

#### Prerequisites
- Python 3.9+
- Node.js 16+ (for frontend)
- Git

#### Backend Setup (text-service)
```bash
# Clone the repository
git clone https://github.com/AIP-F25-2/SkillScreen.git
cd SkillScreen

# Switch to the integration branch
git checkout frontend/fastapi-streamlit-integration

# Install backend dependencies
cd backend/text-service
pip install -r requirements_production.txt
pip install -r requirements_test.txt

# Set up environment variables
cp env.example .env
# Edit .env with your API keys:
# GEMINI_API_KEY=your_gemini_key
# WOLFRAM_APP_ID=your_wolfram_id
# SERPAPI_KEY=your_serpapi_key

# Start the backend service
python simple_fastapi_app.py
```

#### Frontend Setup
```bash
# Install frontend dependencies
cd frontend/streamlit-app
pip install streamlit

# Start the frontend
streamlit run streamlit_frontend.py
```

### 🔑 API Integration Examples

#### Starting an Interview
```python
import requests

# Create candidate
candidate_data = {
    "name": "John Doe",
    "email": "john@example.com",
    "resume_text": "Your resume content here..."
}
candidate_response = requests.post("http://localhost:8000/candidates", json=candidate_data)

# Create job
job_data = {
    "title": "Software Engineer",
    "company": "Tech Corp",
    "description": "Job description here...",
    "required_skills": ["Python", "FastAPI", "React"]
}
job_response = requests.post("http://localhost:8000/jobs", json=job_data)

# Start interview
interview_data = {
    "candidate_id": candidate_response.json()["candidate_id"],
    "job_id": job_response.json()["job_id"]
}
interview_response = requests.post("http://localhost:8000/interviews/start", json=interview_data)
```

#### Submitting Responses
```python
# Submit response
response_data = {
    "response_text": "My answer to the question...",
    "question_number": 1
}
submit_response = requests.post(
    f"http://localhost:8000/interviews/{session_id}/respond", 
    json=response_data
)
```

### 🧪 Testing

#### Run Tests
```bash
cd backend/text-service
python -m pytest tests/ -v
```

#### Health Check
```bash
curl http://localhost:8000/health
```

### 📊 Features Available

#### ✅ Completed Features
- **AI Question Generation**: Multi-API integration for contextual questions
- **Resume Parsing**: Intelligent experience calculation and skill extraction
- **Code Execution**: Sandboxed execution for technical assessments
- **Response Analysis**: Contextual feedback generation
- **Anti-cheating**: Response similarity detection
- **Multi-modal Assessment**: Text, code, and behavioral analysis

#### 🚧 In Progress
- **Enhanced Scoring System**: Multi-dimensional assessment
- **Evidence Linking**: Connect scores to specific responses
- **STAR Method Detection**: Behavioral response analysis

### 🔍 Code Quality

This project uses **SonarQube** for code quality analysis. The analysis runs automatically on:
- Push to main branches
- Pull requests

#### SonarQube Integration
- **Project Key**: `skillscreen`
- **Organization**: `aip-f25-2`
- **Quality Gates**: Configured for maintainability, reliability, and security

### 🤝 Contributing

1. **Create Feature Branch**: `git checkout -b feature/your-feature-name`
2. **Make Changes**: Follow the existing code structure
3. **Test Your Changes**: Ensure all tests pass
4. **Commit Changes**: Use conventional commit messages
5. **Push and Create PR**: Push to your branch and create a pull request

### 📝 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 🆘 Troubleshooting

#### Common Issues
1. **Port Conflicts**: Ensure ports 8000 (backend) and 8501 (frontend) are available
2. **API Key Issues**: Check your `.env` file for correct API keys
3. **Dependencies**: Run `pip install -r requirements_production.txt`

#### Getting Help
- Check the logs in `backend/text-service/logs/`
- Review the API documentation at `/docs`
- Contact the development team

### 📈 Performance

- **Backend**: FastAPI with async support
- **Frontend**: Streamlit with optimized rendering
- **Database**: SQLite for development, PostgreSQL for production
- **Caching**: Redis for session management

### 🔒 Security

- **API Keys**: Stored in environment variables
- **Input Validation**: Pydantic models for data validation
- **Anti-cheating**: Response similarity detection
- **Code Execution**: Sandboxed environment for safety

---

**Happy Coding! 🎉**

For questions or support, reach out to the development team.
