# Team Setup Guide - Code Editor & Coding Interview Services

This guide will help your team members set up and run the **Text Service** and **Coding Interview Service** on their local machines.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Repository Setup](#repository-setup)
3. [Environment Configuration](#environment-configuration)
4. [Running Text Service](#running-text-service)
5. [Running Coding Interview Service](#running-coding-interview-service)
6. [API Endpoints](#api-endpoints)
7. [Troubleshooting](#troubleshooting)

---

## 🔧 Prerequisites

Before starting, ensure you have the following installed:

- **Python 3.8+** (recommended: Python 3.10 or 3.11)
- **Git** (for cloning the repository)
- **pip** (Python package manager)
- **Virtual environment tool** (venv or conda)

### Optional (for specific languages):
- **Node.js** (for JavaScript execution)
- **Java JDK** (for Java execution)
- **GCC/G++** (for C++ execution)
- **.NET SDK** or **Mono** (for C# execution)

---

## 📥 Repository Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/AIP-F25-2/SkillScreen.git
cd SkillScreen
```

### Step 2: Checkout the Correct Branch

```bash
git checkout frontend/fastapi-streamlit-integration-v2
```

### Step 3: Pull Latest Changes

```bash
git pull origin frontend/fastapi-streamlit-integration-v2
```

---

## ⚙️ Environment Configuration

### Step 1: Create Virtual Environment

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install Dependencies

#### For Text Service:
```bash
cd backend/text-service
pip install -r requirements.txt
```

#### For Coding Interview Service:
```bash
cd backend/coding-interview-service
pip install -r requirements.txt
```

#### For Frontend:
```bash
cd frontend/coding-interview-app
pip install streamlit
```

---

## 🔑 API Keys Configuration

### Step 1: Create Configuration File

Navigate to `backend/text-service/` and create a `.config` file:

```bash
cd backend/text-service
```

### Step 2: Add API Keys

Create `.config` file with the following content:

```ini
# LLM API Keys
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
MISTRAL_API_KEY=your_mistral_api_key_here

# Database (if using)
DATABASE_URL=your_database_url_here

# Other configurations
GEMINI_MODEL=gemini-1.5-pro
```

**⚠️ Important:** 
- Never commit the `.config` file to Git (it's in `.gitignore`)
- Ask your team lead for the API keys
- Keep your API keys secure and private

### Step 3: Verify Configuration

Check that `.config` file exists:
```bash
# Windows
dir .config

# Linux/Mac
ls -la .config
```

---

## 🚀 Running Text Service

### Step 1: Navigate to Text Service Directory

```bash
cd backend/text-service
```

### Step 2: Start the Service

**Option A: Using Python directly**
```bash
python fastapi_app.py
```

**Option B: Using uvicorn**
```bash
uvicorn fastapi_app:app --host 0.0.0.0 --port 8000 --reload
```

### Step 3: Verify Service is Running

Open your browser and navigate to:
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/

The service should be running on **port 8000**.

---

## 💻 Running Coding Interview Service

### Step 1: Navigate to Coding Interview Service Directory

```bash
cd backend/coding-interview-service
```

### Step 2: Start the Service

**Using the startup script (Recommended):**
```bash
python start_service.py
```

**Or using uvicorn directly:**
```bash
uvicorn app:app --host 0.0.0.0 --port 8001 --reload
```

### Step 3: Verify Service is Running

The service should be running on **port 8001**.

Test with:
```bash
curl http://localhost:8001/
```

---

## 🖥️ Running Frontend (Coding Interview UI)

### Step 1: Navigate to Frontend Directory

```bash
cd frontend/coding-interview-app
```

### Step 2: Start Streamlit

```bash
streamlit run coding_interview_ui.py --server.port 8502
```

### Step 3: Access the UI

Open your browser and navigate to:
- **Coding Interview UI:** http://localhost:8502

---

## 📡 API Endpoints

### Text Service (Port 8000)

#### Interview Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/interview/start` | Start a new interview session |
| POST | `/api/interview/{session_id}/submit-response` | Submit interview response |
| GET | `/api/interview/{session_id}` | Get interview session details |
| POST | `/api/interview/{session_id}/end` | End interview session |

#### Code Editor Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/code-editor/sessions` | Create a new code editor session |
| PUT | `/api/code-editor/sessions/{session_id}/code` | Update code in session |
| POST | `/api/code-editor/sessions/{session_id}/execute` | Execute code |
| POST | `/api/code-editor/sessions/{session_id}/run-tests` | Run test cases |
| GET | `/api/code-editor/sessions/{session_id}` | Get session status |
| GET | `/api/code-editor/languages` | Get supported languages |

#### Resume & Job Description

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/resume/upload` | Upload and parse resume (PDF) |
| POST | `/api/job-description` | Set job description and requirements |

### Coding Interview Service (Port 8001)

#### Session Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/coding-interview/start` | Start a new coding interview |
| GET | `/api/coding-interview/sessions/{session_id}` | Get session details |
| POST | `/api/coding-interview/sessions/{session_id}/next-question` | Get next question |

#### Code Submission

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/coding-interview/sessions/{session_id}/submit-code` | Submit code with test cases |
| POST | `/api/coding-interview/sessions/{session_id}/run-code` | Run code without test cases |

#### Resume & Job Description

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/coding-interview/resume/upload` | Upload resume (PDF) |
| POST | `/api/coding-interview/job-description` | Set job description |

---

## 🔍 Example API Calls

### Start Coding Interview

```bash
curl -X POST "http://localhost:8001/api/coding-interview/start" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_data": {
      "skills": ["Python", "Java"],
      "experience_years": 3
    },
    "job_description": {
      "job_title": "Software Engineer",
      "company": "Tech Corp",
      "description": "We are looking for...",
      "required_skills": ["Python", "Java"]
    },
    "num_questions": 5
  }'
```

### Submit Code

```bash
curl -X POST "http://localhost:8001/api/coding-interview/sessions/{session_id}/submit-code" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def solution(arr):\n    return sum(arr)",
    "language": "python"
  }'
```

### Run Code (without test cases)

```bash
curl -X POST "http://localhost:8001/api/coding-interview/sessions/{session_id}/run-code" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def solution():\n    print(\"Hello World\")",
    "language": "python"
  }'
```

---

## 🛠️ Supported Programming Languages

Both services support the following languages:

1. **Python** (`.py`) - Default
2. **Java** (`.java`) - Requires JDK
3. **JavaScript** (`.js`) - Requires Node.js
4. **C++** (`.cpp`) - Requires GCC/G++
5. **C#** (`.cs`) - Requires .NET SDK or Mono

---

## 🐛 Troubleshooting

### Issue: Port Already in Use

**Error:** `Address already in use` or `Port 8000/8001/8502 is already in use`

**Solution:**
```bash
# Find process using the port
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000

# Kill the process (replace PID with actual process ID)
# Windows
taskkill /PID <PID> /F

# Linux/Mac
kill -9 <PID>
```

### Issue: Module Not Found

**Error:** `ModuleNotFoundError: No module named 'xxx'`

**Solution:**
```bash
# Make sure virtual environment is activated
# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: API Keys Not Working

**Error:** `Invalid API key` or `Authentication failed`

**Solution:**
1. Check `.config` file exists in `backend/text-service/`
2. Verify API keys are correct (no extra spaces)
3. Ensure API keys are active and have credits/quota

### Issue: Services Can't Connect

**Error:** `Connection refused` or `Failed to connect`

**Solution:**
1. Verify both services are running
2. Check firewall settings
3. Ensure correct ports (8000 for text-service, 8001 for coding-interview-service)
4. Check CORS settings if accessing from different origin

### Issue: Code Execution Fails

**Error:** `Execution error` or `Compilation failed`

**Solution:**
1. Verify language runtime is installed (Java, Node.js, etc.)
2. Check code syntax
3. Review error messages in service logs
4. Ensure test cases are properly formatted

---

## 📝 Quick Start Checklist

- [ ] Clone repository and checkout branch
- [ ] Create and activate virtual environment
- [ ] Install dependencies for both services
- [ ] Create `.config` file with API keys
- [ ] Start Text Service (port 8000)
- [ ] Start Coding Interview Service (port 8001)
- [ ] Start Frontend UI (port 8502)
- [ ] Test API endpoints
- [ ] Verify code execution works

---

## 📞 Getting Help

If you encounter issues:

1. Check the **Troubleshooting** section above
2. Review service logs for error messages
3. Verify all prerequisites are installed
4. Contact the team lead for API keys or configuration issues
5. Check GitHub issues for known problems

---

## 🔄 Updating Your Local Copy

To get the latest changes:

```bash
git pull origin frontend/fastapi-streamlit-integration-v2
pip install -r requirements.txt  # Update dependencies if needed
```

---

## 📚 Additional Resources

- **Text Service Documentation:** `backend/text-service/README.md`
- **Coding Interview Service:** `backend/coding-interview-service/README.md`
- **API Documentation:** http://localhost:8000/docs (when service is running)
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Streamlit Docs:** https://docs.streamlit.io/

---

## ✅ Verification

After setup, verify everything works:

1. **Text Service:** http://localhost:8000/docs should show API documentation
2. **Coding Interview Service:** http://localhost:8001/ should return a response
3. **Frontend:** http://localhost:8502 should show the coding interview UI
4. **Test Code Execution:** Try submitting a simple Python function

---

**Last Updated:** November 2025  
**Branch:** `frontend/fastapi-streamlit-integration-v2`  
**Maintainer:** Development Team

