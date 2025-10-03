# SkillScreen - FastAPI + Streamlit Integration

This branch contains the integration of FastAPI backend with Streamlit frontend for the SkillScreen AI Interview Assistant.

## 🏗️ Architecture

### Backend Services
- **Interview Service** (`backend/interview-service/`): FastAPI-based interview orchestration service
  - `simple_fastapi_app.py`: Simplified FastAPI application for testing
  - `fastapi_app.py`: Full production FastAPI application
  - `database/`: PostgreSQL database models and connection management
  - `services/`: NLP, Anti-cheating, and RAG services
  - `utils/`: Utility functions and logging

### Frontend
- **Streamlit App** (`frontend/streamlit-app/`): User-friendly web interface
  - `streamlit_frontend.py`: Main Streamlit application connecting to FastAPI backend

### Shared Components
- **Schemas** (`shared/schemas/`): Pydantic models for API validation
- **Utils** (`shared/utils/`): Common utilities across services

## 🚀 Features

### Interview System
- **9-Question Interview Structure**: 3 rounds (General, Technical, Theoretical)
- **AI-Powered Question Generation**: Dynamic questions based on resume and job description
- **Real-time Response Evaluation**: Scoring and feedback system
- **Human-like AI Summaries**: Comprehensive interview feedback

### Download Options
- **PDF Reports**: Professional interview reports with detailed feedback
- **Text Reports**: Plain text format for easy sharing
- **JSON Data**: Structured data for integration with other systems

### Anti-Cheating Features
- **Duplicate Response Detection**: Prevents repeated answers
- **Context Validation**: Ensures responses are relevant
- **Behavioral Analysis**: Tracks response patterns

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **PostgreSQL**: Relational database
- **SQLAlchemy**: ORM for database operations
- **Google Generative AI**: LLM integration for question generation and evaluation

### Frontend
- **Streamlit**: Python-based web application framework
- **ReportLab**: PDF generation (optional)

## 📦 Installation & Setup

### Prerequisites
- Python 3.10+
- Git

### Backend Setup
```bash
cd backend/interview-service
pip install -r requirements_production.txt
python simple_fastapi_app.py
```

### Frontend Setup
```bash
cd frontend/streamlit-app
pip install streamlit reportlab
streamlit run streamlit_frontend.py --server.port 8502
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in `backend/interview-service/`:
```
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://user:password@localhost/skillscreen
```

### API Configuration
The FastAPI backend runs on `http://localhost:8000` by default.
The Streamlit frontend runs on `http://localhost:8502` by default.

## 📊 API Endpoints

### Core Interview Flow
- `POST /interviews/start`: Start new interview session
- `POST /interviews/{session_id}/respond`: Submit candidate response
- `GET /interviews/{session_id}/summary`: Get interview summary
- `GET /interviews/{session_id}/ai-summary`: Get AI-generated human-like feedback

### Data Management
- `POST /candidates`: Create candidate profile
- `POST /jobs`: Create job description
- `GET /interviews/{session_id}`: Get interview session details

## 🎯 Interview Process

1. **Setup**: Upload resume and provide job description
2. **Round 1 (Questions 1-3)**: General assessment - background and experience
3. **Round 2 (Questions 4-6)**: Technical assessment - skills and hands-on experience
4. **Round 3 (Questions 7-9)**: Theoretical assessment - concepts and best practices
5. **Summary**: AI-generated feedback with downloadable reports

## 🔒 Security Features

- **Input Validation**: Comprehensive request validation using Pydantic
- **Error Handling**: Robust error handling and logging
- **Anti-Cheating**: Multiple layers of cheating detection
- **Data Privacy**: Secure handling of candidate information

## 📈 Performance

- **FastAPI**: High-performance async API framework
- **In-Memory Storage**: For simplified testing (production uses PostgreSQL)
- **Caching**: Efficient response caching for better performance

## 🧪 Testing

### Backend Testing
```bash
cd backend/interview-service
python test_app.py
```

### Frontend Testing
Access the Streamlit app at `http://localhost:8502` and follow the interview flow.

## 📝 Development Notes

### Current Status
- ✅ FastAPI backend with interview orchestration
- ✅ Streamlit frontend with user-friendly interface
- ✅ AI-powered question generation and evaluation
- ✅ Multiple download formats (PDF, Text, JSON)
- ✅ Anti-cheating mechanisms
- ✅ Human-like AI summaries

### Future Enhancements
- [ ] PostgreSQL database integration
- [ ] Advanced NLP services
- [ ] Video/audio analysis
- [ ] ATS integrations
- [ ] Docker containerization
- [ ] Kubernetes deployment

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is part of the SkillScreen AI Interview Platform.

---

**Built with ❤️ for the SkillScreen Team**