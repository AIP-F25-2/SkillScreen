# SkillScreen - AI Interview Assistant

SkillScreen is an end-to-end automated interviewing platform that generates role-tailored interviews from resumes, job descriptions, or recruiter-specified skills — delivered as chat-based interviews. It scores hard and soft skills, detects cheating risks, and produces auditable evidence (transcripts, test results) that recruiters and hiring teams can act on.

## 🎯 Features

### Core Functionalities
- **Dynamic Question Generation**: AI-powered questions that adapt based on candidate responses
- **Resume & Job Parsing**: Automatic extraction of skills, experience, and requirements
- **Sequential Interviewing**: Each question builds on previous responses
- **Real-time Evaluation**: Instant scoring of technical accuracy, communication, and relevance
- **Context Validation**: Prevents off-topic responses and maintains interview focus
- **Comprehensive Scoring**: Multi-dimensional evaluation of candidate performance
- **Interview Summaries**: Detailed feedback with strengths, improvements, and recommendations

### Technical Features
- **LLM Integration**: Google Gemini API for intelligent question generation
- **Advanced NLP**: Resume and job description parsing with skill extraction
- **Context Awareness**: Maintains conversation context throughout the interview
- **Off-topic Detection**: Identifies and handles irrelevant responses
- **Multi-dimensional Scoring**: Technical, communication, relevance, and confidence metrics
- **Real-time Feedback**: Immediate evaluation and guidance

## 🚀 Quick Start

### 1. Installation
```bash
# Clone the repository
git clone <repository-url>
cd SkillScreen

# Install dependencies
pip install -r requirements.txt

# Download required NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Download spaCy model
python -m spacy download en_core_web_sm
```

### 2. Configuration
```bash
# Run the setup script to configure SkillScreen
python setup_config.py

# Or manually set your Gemini API key
export GEMINI_API_KEY="your_gemini_api_key_here"

# Or create a .env file
cp env.example .env
# Edit .env with your API key
```

### 3. Run the Application
```bash
streamlit run app.py
```

## 📋 Usage

### Starting an Interview

1. **Navigate to "Start Interview"**
2. **Input Resume**: Paste text or upload file
3. **Input Job Description**: Paste text or upload file
4. **Configure Interview**: Choose type, difficulty, and max questions
5. **Parse Information**: Click "Parse Resume & Job Description"
6. **Start Interview**: Click "Start Interview"

### Conducting the Interview

1. **Navigate to "Active Interview"**
2. **Answer Questions**: Type your responses in the chat interface
3. **View Feedback**: See real-time scoring and feedback
4. **Continue**: Answer follow-up questions based on your responses
5. **Complete**: Interview ends automatically or manually

### Viewing Results

1. **Navigate to "Interview Results"**
2. **Review Summary**: See comprehensive evaluation
3. **Download Results**: Export as JSON
4. **Start New**: Begin another interview

## 🔧 Configuration

### Interview Types
- **Mixed**: Balanced technical and behavioral questions
- **Technical**: Focus on technical skills and problem-solving
- **Behavioral**: Focus on soft skills and experience

### Scoring Dimensions
- **Relevance**: How well the response addresses the question (0.0-1.0)
- **Technical Accuracy**: Technical correctness of the response (0.0-1.0)
- **Communication Quality**: Clarity and structure of communication (0.0-1.0)
- **Confidence Level**: Confidence demonstrated in the response (0.0-1.0)

### Context Validation
- **Off-topic Detection**: Identifies responses that don't address the question
- **Minimum Response Length**: Ensures substantial responses
- **Context Continuity**: Maintains interview flow and relevance

## 📊 Interview Process

### 1. Resume Parsing
- Extracts candidate information (name, contact, skills)
- Identifies technical and soft skills
- Analyzes work experience and education
- Categorizes skills by type and importance

### 2. Job Description Analysis
- Parses job requirements and qualifications
- Identifies required and preferred skills
- Determines experience level and difficulty
- Maps skills to interview focus areas

### 3. Dynamic Question Generation
- **Initial Question**: Based on resume and job match
- **Follow-up Questions**: Build on previous responses
- **Context Awareness**: Maintains conversation flow
- **Adaptive Difficulty**: Adjusts based on candidate performance

### 4. Real-time Evaluation
- **Immediate Scoring**: Each response is evaluated instantly
- **Multi-dimensional Analysis**: Technical, communication, relevance
- **Strengths Identification**: Highlights candidate strengths
- **Improvement Areas**: Identifies areas for development

### 5. Interview Summary
- **Comprehensive Assessment**: Overall performance evaluation
- **Detailed Feedback**: Question-by-question analysis
- **Recommendations**: Hire/no-hire decision with reasoning
- **Actionable Insights**: Specific areas for improvement

## ⚙️ Configuration & Logging

### Configuration System
SkillScreen includes a comprehensive configuration system:

- **`config.json`**: Main configuration file with all settings
- **`.env`**: Environment variables for sensitive data (API keys)
- **`config.py`**: Configuration management and validation
- **`setup_config.py`**: Automated setup and configuration script

### Configuration Options
```bash
# View current configuration
python setup_config.py show

# Setup configuration
python setup_config.py
```

### Logging System
- **Structured Logging**: JSON-formatted logs with context
- **Multiple Log Files**: Application, audit, and error logs
- **Log Rotation**: Automatic log file rotation and cleanup
- **Performance Tracking**: Function execution time monitoring

### Log Files
- `logs/skillscreen.log`: Main application logs
- `logs/audit.log`: Interview audit trail
- `logs/errors.log`: Error tracking and debugging

## 🎯 Key Features

### Dynamic Question Generation
- Questions adapt based on candidate responses
- Maintains conversation context
- Prevents repetitive questioning
- Ensures comprehensive coverage

### Context Validation
- Detects off-topic responses
- Maintains interview focus
- Prevents interview derailment
- Ensures quality responses

### Multi-dimensional Scoring
- **Technical Accuracy**: Evaluates technical knowledge
- **Communication Quality**: Assesses clarity and structure
- **Relevance**: Measures response appropriateness
- **Confidence**: Gauges candidate confidence level

### Comprehensive Feedback
- **Real-time Evaluation**: Immediate feedback on responses
- **Strengths Identification**: Highlights positive aspects
- **Improvement Areas**: Identifies development opportunities
- **Actionable Recommendations**: Specific guidance for improvement

## 🔍 Interview Flow

```
1. Resume & Job Parsing
   ↓
2. Initial Question Generation
   ↓
3. Candidate Response
   ↓
4. Response Evaluation
   ↓
5. Follow-up Question Generation
   ↓
6. Repeat (3-5) until completion
   ↓
7. Comprehensive Summary
```

## 📈 Scoring System

### Response Evaluation
- **Relevance Score**: 0.0-1.0 (how well it addresses the question)
- **Technical Accuracy**: 0.0-1.0 (technical correctness)
- **Communication Quality**: 0.0-1.0 (clarity and structure)
- **Confidence Level**: 0.0-1.0 (demonstrated confidence)

### Overall Assessment
- **Overall Score**: Average of all dimensions
- **Recommendation**: Hire/No-hire/Maybe
- **Key Strengths**: Identified positive aspects
- **Areas for Improvement**: Development opportunities

## 🛠️ Technical Implementation

### Core Components
- **Resume Parser**: Extracts skills and experience from resumes
- **Job Parser**: Analyzes job descriptions and requirements
- **LLM Integration**: Google Gemini API for question generation
- **Interview Engine**: Orchestrates the interview process
- **UI Interface**: Streamlit-based chat interface

### Key Technologies
- **Python 3.9+**: Core programming language
- **Streamlit**: Web interface framework
- **Google Gemini API**: LLM integration
- **spaCy**: Natural language processing
- **NLTK**: Text processing and analysis
- **Pandas**: Data manipulation and analysis

## 🔧 Configuration Options

### Interview Settings
- **Maximum Questions**: 5-20 questions per interview
- **Off-topic Threshold**: 0.1-1.0 for off-topic detection
- **Max Off-topic Responses**: 1-10 before ending interview
- **Default Interview Type**: Mixed, technical, or behavioral

### API Configuration
- **Gemini API Key**: Required for question generation
- **Model Selection**: Gemini Pro for optimal performance
- **Rate Limiting**: Built-in API rate limiting
- **Error Handling**: Graceful error handling and recovery

## 📊 Analytics and Reporting

### Interview Analytics
- **Session Tracking**: Monitor active interviews
- **Performance Metrics**: Track interview effectiveness
- **Success Rates**: Measure interview completion rates
- **Quality Metrics**: Assess interview quality

### Export Options
- **JSON Export**: Complete interview data
- **Summary Reports**: High-level assessments
- **Detailed Analysis**: Question-by-question breakdown
- **Recommendation Reports**: Hiring decisions and reasoning

## 🚀 Deployment

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GEMINI_API_KEY="your_key_here"

# Run application
streamlit run app.py
```

### Production Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run with production settings
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

## 🔒 Security and Privacy

### Data Protection
- **Local Processing**: All data processed locally
- **No Data Storage**: No permanent storage of interview data
- **API Keys**: Secure handling of API credentials
- **Session Management**: Secure session handling

### Privacy Considerations
- **Data Minimization**: Only necessary data is processed
- **Temporary Storage**: Data exists only during interview
- **Secure Transmission**: HTTPS for all communications
- **Access Control**: Session-based access control

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the code examples

## 🔮 Future Enhancements

### Planned Features
- **Audio/Video Support**: Multi-modal interview capabilities
- **Advanced Analytics**: Deeper insights and reporting
- **Integration APIs**: ATS and HR system integration
- **Custom Question Banks**: Industry-specific question sets
- **Team Collaboration**: Multi-interviewer support
- **Advanced Scoring**: Machine learning-based evaluation

### Roadmap
- **Q1 2024**: Audio interview support
- **Q2 2024**: Video interview capabilities
- **Q3 2024**: ATS integration
- **Q4 2024**: Advanced analytics dashboard

---

**SkillScreen** - Revolutionizing the interview process with AI-powered insights and comprehensive candidate evaluation.