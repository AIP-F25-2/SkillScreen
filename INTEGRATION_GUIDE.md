# AI Logic Service Integration Guide

## Overview

This guide documents the integration of the AI Logic Service with the SkillScreen interview platform. The integration enables:

1. **AI-powered resume parsing** using OpenResume-based parser
2. **Automatic job matching** based on candidate skills
3. **Dynamic interview question generation** tailored to each candidate
4. **Question viewing** during interviews via modal interface

## Architecture

### Services Involved

1. **Frontend (Next.js/React)**
   - File upload and resume submission
   - Question modal for viewing interview questions
   - Integration with API client

2. **AI Logic Service (FastAPI - Port 8000)**
   - Resume parsing endpoint
   - Candidate/Job management
   - Interview session creation
   - Question generation

3. **Media Service (Flask - Port 8080)**
   - Resume file storage
   - Video recording and processing

4. **API Gateway (FastAPI - Port 5000)**
   - Request routing
   - Authentication (bypassed for demo)

## Key Components

### 1. API Client (`frontend/src/lib/api.ts`)

New methods added for AI service integration:

```typescript
// Parse resume using AI
async parseResumeWithAI(file: File): Promise<ApiResponse<any>>

// Create candidate in AI service
async createAICandidate(candidateData: {...}): Promise<ApiResponse<any>>

// Create job in AI service
async createAIJob(jobData: {...}): Promise<ApiResponse<any>>

// Start AI interview session
async startAIInterview(data: {...}): Promise<ApiResponse<any>>

// Get interview questions
async getInterviewQuestions(sessionId: string): Promise<ApiResponse<any>>
```

### 2. Demo Helpers (`frontend/src/lib/demoHelpers.ts`)

**Purpose**: Provide dummy data for demonstration when AI service is unavailable

**Key Functions**:

- `getDemoJobDescription(resumeSkills?: string[])`: Returns a job description tailored to candidate skills
  - Analyzes skills to determine job type (ML Engineer, DevOps, Full Stack, etc.)
  - Provides realistic job descriptions with requirements
  
- `getDemoInterviewQuestions()`: Returns 9 pre-defined interview questions
  - 3 General questions (Round 1)
  - 3 Technical questions (Round 2)
  - 3 Theoretical questions (Round 3)

**Job Types Supported**:
- Senior Machine Learning Engineer (for data science skills)
- DevOps Engineer (for cloud/infrastructure skills)
- Full Stack Developer (for frontend + backend skills)
- Frontend Developer (for UI/UX skills)
- Backend Developer (for server-side skills)
- Software Engineer (default fallback)

### 3. Question Modal (`frontend/src/components/QuestionModal.tsx`)

**Purpose**: Display interview questions in an elegant modal during the interview

**Features**:
- Animated modal with glassmorphism design
- Round indicators (General, Technical, Theoretical)
- Difficulty badges (Easy, Medium, Hard)
- Navigation between questions
- Progress bar showing interview completion
- Question counter (X/9)

**Props**:
```typescript
interface QuestionModalProps {
  isOpen: boolean;
  onClose: () => void;
  questions: Question[];
  currentQuestionIndex: number;
  onQuestionChange?: (index: number) => void;
}
```

**Question Structure**:
```typescript
interface Question {
  id: string;
  question_index: number;
  question_text: string;
  question_type: string; // 'general' | 'technical' | 'theoretical'
  difficulty: string; // 'easy' | 'medium' | 'hard'
  round_number: number; // 1, 2, or 3
}
```

### 4. Interview Screen (`frontend/src/components/ModernInterviewScreen.tsx`)

**Enhancements**:
- Loads interview questions on mount
- Question button in control bar with count badge
- FileText icon for question access
- Auto-loads demo questions for testing

**New State**:
```typescript
const [isQuestionModalOpen, setIsQuestionModalOpen] = useState(false);
const [interviewQuestions, setInterviewQuestions] = useState<any[]>([]);
const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
```

**Control Bar Addition**:
- Purple-highlighted button with question count badge
- Opens question modal on click
- Questions load automatically on component mount

### 5. File Upload (`frontend/src/components/ui/file-upload-demo.tsx`)

**Enhanced Upload Flow**:

1. **Upload to Media Service**
   - Saves PDF file for storage
   - Creates basic candidate record

2. **Parse with AI Service** (with fallback)
   - Extracts name, email, phone, skills, experience
   - Uses OpenResume-based parser
   - Falls back to basic upload if AI service unavailable

3. **Create AI Candidate**
   - Stores structured candidate data in AI service
   - Includes parsed skills and experience

4. **Generate Demo Job**
   - Analyzes candidate skills
   - Creates appropriate job description
   - Matches job type to skill set

5. **Start AI Interview**
   - Creates interview session
   - Generates personalized questions
   - Returns session ID for question retrieval

**Error Handling**:
- Graceful degradation if AI service is down
- Console warnings instead of errors
- Falls back to basic upload flow

## Data Flow

```
User Uploads Resume (PDF)
         ↓
Media Service (Store File)
         ↓
AI Service (Parse Resume)
         ↓
Extract: Name, Email, Skills, Experience
         ↓
Create Candidate in AI Service
         ↓
Generate Job Description (based on skills)
         ↓
Create Job in AI Service
         ↓
Start AI Interview Session
         ↓
Generate 9 Personalized Questions
         ↓
Store Session ID & Questions
         ↓
User Clicks "Process & Schedule"
         ↓
Creates Interview Record
         ↓
User Enters Interview
         ↓
Questions Load in Modal
         ↓
User Can View Questions Anytime
         ↓
Conducts Interview
         ↓
Ends Interview → Processing → Summary
```

## API Endpoints Used

### AI Logic Service (Port 8000)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/resumes/parse` | POST | Parse resume PDF |
| `/api/candidates/` | POST | Create candidate |
| `/api/jobs/` | POST | Create job |
| `/api/interviews/start` | POST | Start interview session |
| `/api/interviews/{sessionId}/questions` | GET | Get questions |

### Media Service (Port 8080)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/resumes/upload` | POST | Upload resume file |
| `/api/candidates/{id}/schedule` | POST | Schedule interview |
| `/upload_chunk` | POST | Upload video chunk |
| `/finalize_upload` | POST | Finalize video |
| `/reset_chunks` | POST | Reset video chunks |

## Demo Mode

**When AI Service is NOT Available**:
- Resume parsing uses basic text extraction
- Demo questions are loaded from `demoHelpers.ts`
- Job description is generic "Software Engineer"
- No AI-generated personalization

**When AI Service IS Available**:
- Full resume parsing with OpenResume
- Personalized job descriptions
- AI-generated questions (future feature)
- Skills-based job matching

## Testing the Integration

### Prerequisites

1. **Start AI Logic Service**:
   ```bash
   cd backend/ai-logic-service
   python fastapi_app.py
   # Should run on http://localhost:8000
   ```

2. **Start Other Services**:
   ```bash
   # From project root
   docker-compose -f docker-compose.dev.yml up
   ```

3. **Start Frontend**:
   ```bash
   cd frontend
   npm run dev
   # Should run on http://localhost:3000
   ```

### Test Flow

1. **Login as Recruiter**:
   - Username: `recruiter`
   - Password: `password123`

2. **Upload Resume**:
   - Go to Recruiter Dashboard
   - Click "Upload Resume"
   - Select a PDF resume
   - Enter candidate name (optional)
   - Click "Upload Resume"
   - Watch console for AI service integration logs

3. **Schedule Interview**:
   - Click "Process & Schedule Interview"
   - Check that interview is created
   - Note the session ID

4. **Start Interview** (as Candidate):
   - Login as candidate: `ashish` / `password123`
   - Go to Candidate Dashboard
   - Click on scheduled interview
   - Interview page loads

5. **View Questions**:
   - Look for purple FileText button in control bar
   - Badge shows "9" questions
   - Click to open question modal
   - Navigate through questions
   - See round indicators and difficulty levels

6. **Conduct Interview**:
   - Recording auto-starts
   - Answer questions (reference modal as needed)
   - Click "End Interview"
   - Wait for processing
   - View summary with transcription

### Console Logs to Check

```
✅ Uploading resume to media service...
✅ Resume uploaded to media service
✅ Parsing resume with AI service...
✅ AI parse response: { name: "...", skills: [...], ... }
✅ Creating AI candidate with data: { ... }
✅ AI candidate created: { candidate_id: "..." }
✅ Creating demo job: { title: "...", ... }
✅ AI job created: { job_id: "..." }
✅ AI interview started: { session_id: "..." }
✅ Resume upload and AI processing completed successfully!
✅ Demo interview questions loaded: 9
```

## Troubleshooting

### AI Service Connection Issues

**Symptom**: Console shows "AI service not available, using basic upload"

**Solutions**:
1. Check AI service is running on port 8000
2. Check CORS is enabled in AI service
3. Verify `/api/resumes/parse` endpoint exists
4. Check browser console for CORS errors

### Questions Not Loading

**Symptom**: Question modal shows "0 questions" or is empty

**Solutions**:
1. Check `getDemoInterviewQuestions()` is imported
2. Verify `useEffect` is running on component mount
3. Check console for question loading logs
4. Ensure `interviewQuestions` state is set correctly

### Resume Parsing Fails

**Symptom**: Skills not detected or name extraction fails

**Solutions**:
1. Check PDF is text-based (not scanned image)
2. Verify resume has clear formatting
3. Check OpenResume parser dependencies
4. Fall back to manual name entry

## Future Enhancements

1. **Real-time Question Generation**:
   - Questions generated based on resume parsing
   - Adaptive difficulty based on responses
   - Follow-up questions

2. **Question Answering Tracking**:
   - Mark questions as answered
   - Time spent on each question
   - Answer quality indicators

3. **Multi-language Support**:
   - Translate questions
   - Support non-English resumes
   - Localized job descriptions

4. **Question Categories**:
   - Filter by type
   - Jump to specific sections
   - Bookmark important questions

5. **Interviewer Notes**:
   - Add notes to specific questions
   - Rate responses in real-time
   - Share notes with team

## Files Modified/Created

### Created:
- `frontend/src/components/QuestionModal.tsx` - Question display modal
- `frontend/src/lib/demoHelpers.ts` - Demo data generators
- `INTEGRATION_GUIDE.md` - This documentation

### Modified:
- `frontend/src/lib/api.ts` - Added AI service endpoints
- `frontend/src/components/ModernInterviewScreen.tsx` - Added question modal integration
- `frontend/src/components/ui/file-upload-demo.tsx` - Enhanced with AI parsing flow

## Support

For issues or questions:
1. Check console logs for detailed error messages
2. Verify all services are running on correct ports
3. Check network tab for failed API calls
4. Review this guide for troubleshooting steps
5. Check AI service logs for backend errors

## Conclusion

This integration provides a foundation for AI-powered interview experiences. The modular design allows for:
- Graceful degradation when services are unavailable
- Easy extension with new features
- Clean separation of concerns
- Comprehensive error handling

The demo mode ensures the system works even without the AI service, making it ideal for development and testing.

