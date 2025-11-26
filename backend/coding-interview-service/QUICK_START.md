# Quick Start Guide - Coding Interview Service

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
cd backend/coding-interview-service
pip install -r requirements.txt
```

### 2. Start Backend Service (Port 8001)
```bash
python app.py
```
Or:
```bash
python -m uvicorn app:app --host 0.0.0.0 --port 8001 --reload
```

### 3. Start Frontend UI (Port 8502)
```bash
cd ../../frontend/coding-interview-app
streamlit run coding_interview_ui.py --server.port 8502
```

## 📋 Usage

1. **Open UI**: Navigate to `http://localhost:8502`
2. **Upload Resume**: Upload your PDF resume in the sidebar
3. **Set Job Description**: Enter job title, company, description, and requirements
4. **Start Interview**: Click "Start Interview" button
5. **Solve Questions**: Code your solutions in the editor
6. **Submit & Test**: Run code and submit for evaluation

## 🎯 Features

- ✅ LLM-powered question generation (Gemini, Groq, Mistral)
- ✅ Automatic difficulty assessment
- ✅ Web scraping from LeetCode, GeeksforGeeks, StackOverflow
- ✅ LeetCode-style UI
- ✅ Real-time code execution
- ✅ Test case validation
- ✅ Multi-language support (Python, Java, JavaScript)

## 🔧 Configuration

Make sure you have API keys in `backend/text-service/.config`:
- `GEMINI_API_KEY`
- `GROQ_API_KEY`
- `MISTRAL_API_KEY`

## 📝 API Endpoints

- `POST /api/coding-interview/start` - Start interview
- `POST /api/coding-interview/upload-resume` - Upload resume
- `POST /api/coding-interview/upload-job-description` - Upload job
- `GET /api/coding-interview/sessions/{session_id}` - Get session
- `POST /api/coding-interview/sessions/{session_id}/submit-code` - Submit code
- `POST /api/coding-interview/sessions/{session_id}/next-question` - Next question

## 🐛 Troubleshooting

**Backend not starting?**
- Check if port 8001 is available
- Verify dependencies are installed
- Check API keys in `.config`

**Frontend not connecting?**
- Ensure backend is running on port 8001
- Check browser console for errors

**Questions not generating?**
- Verify LLM API keys are configured
- Check backend logs for errors

