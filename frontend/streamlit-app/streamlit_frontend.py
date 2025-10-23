"""
Streamlit Frontend for SkillScreen FastAPI Backend
This frontend connects to the FastAPI backend to provide a user-friendly interface
"""

import streamlit as st
import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import time
import base64
from io import BytesIO
import sys
import os

# Add the backend utils to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'text-service', 'utils'))
from resume_parser import resume_parser

# Try to import reportlab for PDF generation
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="SkillScreen - AI Interview Assistant",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# UTILITY FUNCTIONS - Common patterns to reduce duplication
# ============================================================================

def show_message(message_type: str, message: str, icon: str = ""):
    """Unified function for displaying messages"""
    if message_type == "success":
        st.success(f"{icon} {message}")
    elif message_type == "error":
        st.error(f"{icon} {message}")
    elif message_type == "warning":
        st.warning(f"{icon} {message}")
    elif message_type == "info":
        st.info(f"{icon} {message}")

def show_api_error(error_msg: str = "API Error"):
    """Show standardized API error message"""
    show_message("error", error_msg, "❌")

def show_success(message: str):
    """Show standardized success message"""
    show_message("success", message, "✅")

def show_warning(message: str):
    """Show standardized warning message"""
    show_message("warning", message, "⚠️")

def show_info(message: str):
    """Show standardized info message"""
    show_message("info", message, "💡")

def handle_api_response(response_data: Optional[Dict], success_msg: str = "", error_msg: str = "Failed to process request") -> bool:
    """Handle API response and show appropriate message"""
    if response_data:
        if success_msg:
            show_success(success_msg)
        return True
    else:
        show_api_error(error_msg)
        return False

def make_api_request(method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
    """Make API request to FastAPI backend"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        
        if method.upper() == "GET":
            response = requests.get(url)
        elif method.upper() == "POST":
            response = requests.post(url, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url)
        else:
            show_api_error(f"Unsupported HTTP method: {method}")
            return None
        
        if response.status_code == 200:
            return response.json()
        else:
            show_api_error(f"API Error {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        show_api_error("Cannot connect to FastAPI backend. Please ensure it's running on http://localhost:8000")
        return None
    except Exception as e:
        show_api_error(f"Error making API request: {str(e)}")
        return None

def check_api_health():
    """Check if the API is running"""
    health_data = make_api_request("GET", "/health")
    return health_data is not None

def show_welcome_message():
    """Display welcome message and app explanation"""
    st.markdown("""
    ## Welcome to SkillScreen! 👋
    
    **Your AI-Powered Interview Assistant**
    
    ### How it works:
    1. **📄 Upload your resume** (PDF, DOCX, or paste text)
    2. **💼 Provide the job description** you're applying for
    3. **🤖 Start your personalized interview** (5 questions)
    4. **📊 Get detailed feedback** and downloadable reports
    
    ### What to expect:
    - **General questions** to understand your background
    - **Technical questions** based on the job requirements
    - **Real-time evaluation** with detailed feedback
    - **Comprehensive summary** with improvement tips
    
    ### Ready to begin? Let's get started! 🚀
    """)

def create_candidate(resume_data: Dict) -> Optional[str]:
    """Create candidate in the backend"""
    candidate_data = {
        "name": resume_data["name"],
        "email": resume_data["email"],
        "skills": resume_data["skills"],
        "experience_years": resume_data["experience_years"],
        "education": resume_data["education"],
        "work_experience": resume_data["work_experience"]
    }
    
    result = make_api_request("POST", "/candidates/", candidate_data)
    return result["candidate_id"] if result else None

def create_job(job_data: Dict) -> Optional[str]:
    """Create job in the backend"""
    result = make_api_request("POST", "/jobs/", job_data)
    return result["job_id"] if result else None

def start_interview(candidate_id: str, job_id: str) -> Optional[Dict]:
    """Start interview session"""
    return make_api_request("POST", "/interviews/start", {
        "candidate_id": candidate_id,
        "job_id": job_id
    })

def submit_response(session_id: str, response_text: str) -> Optional[Dict]:
    """Submit interview response"""
    return make_api_request("POST", f"/interviews/{session_id}/respond", {
        "response_text": response_text
    })

def get_interview_summary(session_id: str) -> Optional[Dict]:
    """Get interview summary"""
    return make_api_request("GET", f"/interviews/{session_id}/summary")

def get_ai_summary(session_id: str) -> Optional[Dict]:
    """Get AI-generated summary"""
    return make_api_request("GET", f"/interviews/{session_id}/ai-summary")

def _create_resume_data_dict(parsed_data: Dict) -> Dict:
    """Create standardized resume data dictionary"""
    return {
        "name": parsed_data['name'],
        "email": parsed_data['email'],
        "experience_years": parsed_data['experience_years'],
        "skills": parsed_data['skills'] if parsed_data['skills'] else ["General"],
        "education": parsed_data['education'],
        "work_experience": parsed_data['work_experience'],
        "parsing_method": "OpenResume-based parser (Tang, 2024)"
    }

def parse_resume_file(resume_file, resume_text: str) -> Optional[Dict]:
    """Parse resume file or text with error handling"""
    try:
        if resume_file is not None:
            # Use OpenResume-based PDF parser
            parsed_data = resume_parser.parse_resume_from_pdf(resume_file)
            resume_text = parsed_data['raw_text']
            show_success("PDF parsed using OpenResume-based parser")
        else:
            resume_text = resume_text or ""
        
        # Use OpenResume-based parser
        parsed_data = resume_parser.parse_resume(resume_text)
        return _create_resume_data_dict(parsed_data)
        
    except Exception as e:
        show_warning(f"OpenResume parser failed: {str(e)}")
        # Fallback to basic extraction
        try:
            if resume_file is not None:
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(resume_file)
                resume_text = ""
                for page in pdf_reader.pages:
                    resume_text += page.extract_text() + "\n"
                show_success("PDF parsed using basic text extraction")
            else:
                resume_text = resume_text or ""
            
            # Use OpenResume-based parser
            parsed_data = resume_parser.parse_resume(resume_text)
            return _create_resume_data_dict(parsed_data)
            
        except Exception as e:
            show_api_error(f"Error reading PDF file: {str(e)}")
            show_info("**Tip**: Try copying and pasting the text content instead of uploading the PDF file.")
            return None

def parse_job_description(job_title: str, company_name: str, job_description: str) -> Optional[Dict]:
    """Parse job description with skill extraction"""
    import re
    
    # Extract skills from job description
    job_lower = job_description.lower()
    
    # Common tech skills to look for (using regex for word boundaries)
    tech_skills = [
        'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue',
        'node.js', 'express', 'django', 'flask', 'fastapi', 'spring', 'laravel',
        'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform',
        'git', 'github', 'gitlab', 'jenkins', 'ci/cd', 'devops',
        'machine learning', 'ai', 'tensorflow', 'pytorch', 'scikit-learn',
        'data science', 'data analysis', 'tableau', 'power bi', 'excel',
        'agile', 'scrum', 'kanban', 'project management'
    ]
    
    required_skills = []
    for skill in tech_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', job_lower):
            required_skills.append(skill.title())
    
    # Extract experience level
    exp_patterns = [
        (r'\b(\d+)\+?\s*years?\s*(?:of\s*)?experience\b', 'years'),
        (r'\b(entry|junior|mid|senior|lead|principal)\b', 'level'),
        (r'\b(0-2|2-5|5-10|10\+)\s*years?\b', 'range')
    ]
    
    exp_level = "Mid-level"
    for pattern, pattern_type in exp_patterns:
        match = re.search(pattern, job_lower)
        if match:
            if pattern_type == 'years':
                years = int(match.group(1))
                if years <= 2:
                    exp_level = "Entry-level"
                elif years <= 5:
                    exp_level = "Mid-level"
                else:
                    exp_level = "Senior-level"
            elif pattern_type == 'level':
                exp_level = match.group(1).title() + "-level"
            elif pattern_type == 'range':
                exp_level = f"{match.group(1)} years experience"
            break
    
    return {
        "title": job_title,
        "company": company_name,
        "description": job_description,
        "required_skills": required_skills if required_skills else ["General"],
        "experience_level": exp_level
    }

def initialize_session_state():
    """Initialize all session state variables"""
    session_vars = {
        'candidate_id': None,
        'job_id': None,
        'current_session_id': None,
        'interview_messages': [],
        'interview_completed': False,
        'interview_terminated': False,
        'parsed_resume': None,
        'parsed_job': None,
        'first_question_added': False
    }
    
    for key, default_value in session_vars.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def reset_interview_state():
    """Reset interview-related session state"""
    st.session_state.current_session_id = None
    st.session_state.interview_messages = []
    st.session_state.interview_completed = False
    st.session_state.interview_terminated = False
    st.session_state.first_question_added = False

def show_status_indicators():
    """Show current status indicators"""
    if st.session_state.candidate_id:
        show_success("Candidate ready")
    if st.session_state.job_id:
        show_success("Job ready")
    if st.session_state.current_session_id:
        show_success("Interview active")

def handle_interview_start():
    """Handle interview start process"""
    try:
        with st.spinner("Starting interview..."):
            result = start_interview(st.session_state.candidate_id, st.session_state.job_id)
            
            if result:
                st.session_state.current_session_id = result["session_id"]
                st.session_state.interview_messages = []
                st.session_state.interview_completed = False
                
                # Add initial question
                st.session_state.interview_messages.append({
                    "role": "assistant",
                    "content": result["first_question"]
                })
                # Mark that we've added the first question
                st.session_state.first_question_added = True
                
                show_success("Interview started successfully!")
                st.rerun()
            else:
                show_api_error("Failed to start interview")
                
    except Exception as e:
        show_api_error(f"Error starting interview: {str(e)}")

def handle_response_submission(session_id: str, response_text: str):
    """Handle response submission process"""
    try:
        with st.spinner("Submitting response..."):
            result = submit_response(session_id, response_text)
            
            if result:
                if result["status"] == "continue":
                    # Show warnings if any
                    if result.get("warnings"):
                        for warning in result["warnings"]:
                            show_warning(warning)
                    
                    # Show anti-cheating counters
                    if result.get("duplicate_count", 0) > 0:
                        show_info(f"Duplicate responses detected: {result['duplicate_count']}")
                    
                    if result.get("ai_generated_count", 0) > 0:
                        show_info(f"AI-generated content detected: {result['ai_generated_count']}")
                    
                    # Add next question only if it's different from current question
                    current_question = st.session_state.interview_messages[-1]["content"] if st.session_state.interview_messages else ""
                    if result["next_question"] != current_question:
                        st.session_state.interview_messages.append({
                            "role": "assistant",
                            "content": result["next_question"]
                        })
                        st.rerun()
                elif result["status"] == "completed":
                    # Interview completed
                    st.session_state.interview_completed = True
                    st.rerun()
                elif result["status"] == "terminated":
                    # Interview terminated due to anti-cheating
                    show_api_error(result.get("message", "Interview terminated due to policy violations"))
                    st.session_state.interview_completed = True
                    st.session_state.interview_terminated = True
                    st.rerun()
            else:
                show_api_error("Failed to submit response")
                
    except Exception as e:
        show_api_error(f"Error submitting response: {str(e)}")

def generate_pdf_report(summary_data, ai_summary_data):
    """Generate PDF report"""
    if not REPORTLAB_AVAILABLE:
        return None
    
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        # Build PDF content
        story = []
        
        # Title
        story.append(Paragraph("SkillScreen Interview Report", title_style))
        story.append(Spacer(1, 20))
        
        # Candidate Information
        story.append(Paragraph("Candidate Information", heading_style))
        story.append(Paragraph(f"<b>Name:</b> {summary_data.get('candidate_name', 'N/A')}", styles['Normal']))
        story.append(Paragraph(f"<b>Email:</b> {summary_data.get('candidate_email', 'N/A')}", styles['Normal']))
        story.append(Paragraph(f"<b>Experience:</b> {summary_data.get('candidate_experience', 'N/A')} years", styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Job Information
        story.append(Paragraph("Job Information", heading_style))
        story.append(Paragraph(f"<b>Position:</b> {summary_data.get('job_title', 'N/A')}", styles['Normal']))
        story.append(Paragraph(f"<b>Company:</b> {summary_data.get('job_company', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Interview Results
        story.append(Paragraph("Interview Results", heading_style))
        story.append(Paragraph(f"<b>Overall Score:</b> {summary_data.get('overall_score', 'N/A')}/100", styles['Normal']))
        story.append(Paragraph(f"<b>Questions Answered:</b> {summary_data.get('questions_answered', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Strengths
        if summary_data.get('strengths'):
            story.append(Paragraph("Strengths", heading_style))
            for strength in summary_data['strengths']:
                story.append(Paragraph(f"• {strength}", styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Areas for Improvement
        if summary_data.get('areas_for_improvement'):
            story.append(Paragraph("Areas for Improvement", heading_style))
            for area in summary_data['areas_for_improvement']:
                story.append(Paragraph(f"• {area}", styles['Normal']))
            story.append(Spacer(1, 12))
        
        # AI Summary
        if ai_summary_data and ai_summary_data.get('summary'):
            story.append(Paragraph("AI Analysis", heading_style))
            story.append(Paragraph(ai_summary_data['summary'], styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return buffer.getvalue()
        
    except Exception as e:
        show_api_error(f"Error generating PDF: {str(e)}")
        return None

def generate_text_report(summary_data, ai_summary_data):
    """Generate text report"""
    report = f"""
INTERVIEW REPORT
================

Candidate Information:
- Name: {summary_data.get('candidate_name', 'N/A')}
- Email: {summary_data.get('candidate_email', 'N/A')}
- Experience: {summary_data.get('candidate_experience', 'N/A')} years

Job Information:
- Position: {summary_data.get('job_title', 'N/A')}
- Company: {summary_data.get('job_company', 'N/A')}

Interview Results:
- Overall Score: {summary_data.get('overall_score', 'N/A')}/100
- Questions Answered: {summary_data.get('questions_answered', 'N/A')}

Strengths:
"""
    
    if summary_data.get('strengths'):
        for strength in summary_data['strengths']:
            report += f"- {strength}\n"
    else:
        report += "- No specific strengths identified\n"
    
    report += "\nAreas for Improvement:\n"
    if summary_data.get('areas_for_improvement'):
        for area in summary_data['areas_for_improvement']:
            report += f"- {area}\n"
    else:
        report += "- No specific areas identified\n"
    
    if ai_summary_data and ai_summary_data.get('summary'):
        report += f"\nAI Analysis:\n{ai_summary_data['summary']}\n"
    
    report += f"\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    return report

def code_editor_section():
    """Code editor section for technical assessments"""
    st.header("💻 Technical Assessment")
    
    # Code editor
    st.subheader("Code Editor")
    language = st.selectbox("Select Language", ["python", "javascript", "java", "cpp", "sql"])
    
    code = st.text_area("Write your code here:", height=300, placeholder=f"# Write your {language} code here...")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("▶️ Run Code", type="primary"):
            if code.strip():
                with st.spinner("Executing code..."):
                    result = make_api_request("POST", "/api/code/execute", {
                        "code": code,
                        "language": language
                    })
                    
                    if result:
                        if result.get("success"):
                            show_success("Code executed successfully!")
                            st.code(result.get("output", ""))
                        else:
                            show_api_error("Code execution failed")
                            st.code(result.get("error", ""))
                    else:
                        show_api_error("Failed to execute code")
            else:
                show_warning("Please enter some code to execute")
    
    with col2:
        if st.button("📝 Get Question"):
            question_result = make_api_request("GET", "/api/code/question")
            if question_result:
                show_info("**Technical Question:**")
                st.write(question_result.get("question", "No question available"))

# ============================================================================
# MAIN APPLICATION FUNCTIONS
# ============================================================================

def main():
    """Main Streamlit application"""
    st.title("🎯 SkillScreen - AI Interview Assistant")
    
    # Check API health
    if not check_api_health():
        st.error("""
        ## ⚠️ Backend Not Available
        
        The FastAPI backend is not running. Please:
        
        1. **Start the FastAPI backend** by running:
           ```bash
           cd backend/text-service
           python simple_fastapi_app.py
           ```
        
        2. **Ensure it's running on** http://localhost:8000
        
        3. **Refresh this page** once the backend is running
        """)
        return
    
    # Initialize session state
    initialize_session_state()
    
    # Sidebar for input
    with st.sidebar:
        st.header("📋 Setup")
        
        # Resume input
        st.subheader("📄 Resume")
        resume_option = st.radio("Choose input method:", ["Upload PDF", "Paste Text"])
        
        resume_file = None
        resume_text = ""
        
        if resume_option == "Upload PDF":
            resume_file = st.file_uploader("Upload Resume (PDF)", type=['pdf'])
        else:
            resume_text = st.text_area("Paste Resume Text", height=150)
        
        # Job description input
        st.subheader("💼 Job Description")
        job_title = st.text_input("Job Title")
        company_name = st.text_input("Company Name")
        job_description = st.text_area("Job Description", height=150)
        
        # Parse buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 Parse Resume", use_container_width=True):
                if resume_file or resume_text:
                    parsed_resume = parse_resume_file(resume_file, resume_text)
                    if parsed_resume:
                        candidate_id = create_candidate(parsed_resume)
                        if handle_api_response(candidate_id, "Resume parsed and candidate created!", "Failed to create candidate"):
                            st.session_state.candidate_id = candidate_id
                            st.session_state.parsed_resume = parsed_resume
                else:
                    show_api_error("Please upload a resume or paste text")
        
        with col2:
            if st.button("💼 Parse Job", use_container_width=True):
                if job_title and company_name and job_description:
                    job_data = parse_job_description(job_title, company_name, job_description)
                    if job_data:
                        job_id = create_job(job_data)
                        if handle_api_response(job_id, "Job created successfully!", "Failed to create job"):
                            st.session_state.job_id = job_id
                            st.session_state.parsed_job = job_data
                else:
                    show_api_error("Please fill in job title, company, and description")
        
        # Start interview button
        if st.session_state.candidate_id and st.session_state.job_id:
            if st.button("🚀 Start Interview", type="primary", use_container_width=True):
                handle_interview_start()
        
        # Show current status
        show_status_indicators()
    
    st.markdown("---")
    
    # Display parsed data in main frame
    if 'parsed_resume' in st.session_state or 'parsed_job' in st.session_state:
        st.subheader("🔍 Parsed Data Review")
        show_info("📋 Review the extracted information before starting the interview")
        
        col1, col2 = st.columns(2)
        
        if st.session_state.parsed_resume:
            with col1:
                st.markdown("### 👤 Candidate Information")
                resume_data = st.session_state.parsed_resume
                st.write(f"**Name:** {resume_data['name']}")
                st.write(f"**Email:** {resume_data['email']}")
                st.write(f"**Experience:** {resume_data['experience_years']} years")
                st.write(f"**Skills:** {', '.join(resume_data['skills'][:10])}")  # Show first 10 skills
                if len(resume_data['skills']) > 10:
                    st.write(f"... and {len(resume_data['skills']) - 10} more skills")
        
        if st.session_state.parsed_job:
            with col2:
                st.markdown("### 💼 Job Information")
                job_data = st.session_state.parsed_job
                st.write(f"**Title:** {job_data['title']}")
                st.write(f"**Company:** {job_data['company']}")
                st.write(f"**Level:** {job_data['experience_level']}")
                st.write(f"**Required Skills:** {', '.join(job_data['required_skills'][:10])}")  # Show first 10 skills
                if len(job_data['required_skills']) > 10:
                    st.write(f"... and {len(job_data['required_skills']) - 10} more skills")
    
    # Main content area
    if st.session_state.current_session_id and not st.session_state.interview_completed:
        show_interview_interface()
    elif st.session_state.interview_completed:
        if st.session_state.interview_terminated:
            show_termination_summary()
        else:
            show_interview_summary()
    else:
        show_info("👈 Please set up your resume and job description in the sidebar to start the interview.")

def show_interview_interface():
    """Show the main interview interface"""
    session_id = st.session_state.current_session_id
    
    # Get current interview status
    interview_data = make_api_request("GET", f"/interviews/{session_id}")
    if not interview_data:
        show_api_error("Failed to get interview data")
        return
    
    # Show interview progress with round information
    question_num = interview_data["responses_received"] + 1
    if question_num <= 3:
        round_info = "🔵 Round 1: General Assessment"
        round_desc = "Background, experience, and soft skills"
    elif question_num <= 6:
        round_info = "🔧 Round 2: Technical Assessment"
        round_desc = "Technical skills and hands-on experience"
    else:
        round_info = "🎯 Round 3: Final Assessment"
        round_desc = "Final evaluation and fit assessment"
    
    # Progress bar
    progress = min(question_num / 5, 1.0)  # Assuming 5 questions total
    st.progress(progress)
    
    # Round information
    st.markdown(f"### {round_info}")
    st.markdown(f"*{round_desc}*")
    st.markdown(f"**Question {question_num} of 5**")
    
    # Chat interface
    st.markdown("### 💬 Interview Chat")
    
    # Display chat messages
    for message in st.session_state.interview_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Response input
    if st.session_state.interview_messages:
        response_text = st.chat_input("Type your response here...")
        
        if response_text:
            # Add user message to chat
            st.session_state.interview_messages.append({
                "role": "user",
                "content": response_text
            })
            
            # Submit response
            handle_response_submission(session_id, response_text)

def show_termination_summary():
    """Show termination summary for anti-cheating violations"""
    session_id = st.session_state.current_session_id
    
    st.markdown("## ❌ Interview Terminated")
    
    # Get interview data
    interview_data = make_api_request("GET", f"/interviews/{session_id}")
    if not interview_data:
        show_api_error("Failed to get interview data")
        return
    
    # Display termination message
    show_api_error("🚨 **Interview Terminated Due to Policy Violations**")
    
    st.markdown("### 📋 Termination Details")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Questions Answered", interview_data.get("responses_received", 0))
    
    with col2:
        st.metric("Duplicate Responses", interview_data.get("duplicate_count", 0))
    
    with col3:
        st.metric("AI-Generated Content", interview_data.get("ai_generated_count", 0))
    
    # Show termination reason
    termination_reason = interview_data.get("termination_reason", "anti_cheating")
    st.markdown(f"**Reason:** {termination_reason.replace('_', ' ').title()}")
    
    # Show policy violations
    if interview_data.get("violations"):
        st.markdown("### 🚨 Policy Violations")
        for violation in interview_data["violations"]:
            st.write(f"• {violation}")
    
    # Restart option
    st.markdown("---")
    if st.button("🔄 Start New Interview", type="primary"):
        reset_interview_state()
        st.rerun()

def show_interview_summary():
    """Show interview summary and results"""
    session_id = st.session_state.current_session_id
    
    # Get interview summary and AI summary
    summary_data = get_interview_summary(session_id)
    ai_summary_data = get_ai_summary(session_id)
    
    if not summary_data:
        show_api_error("Failed to get interview summary")
        return
    
    st.markdown("## 🎉 Interview Completed!")
    
    # Overall score
    overall_score = summary_data.get("overall_score", 0)
    st.metric("Overall Score", f"{overall_score}/100")
    
    # Score breakdown
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Technical Score", f"{summary_data.get('technical_score', 0)}/100")
    
    with col2:
        st.metric("Communication Score", f"{summary_data.get('communication_score', 0)}/100")
    
    with col3:
        st.metric("Problem Solving", f"{summary_data.get('problem_solving_score', 0)}/100")
    
    # Detailed feedback
    st.markdown("### 📊 Detailed Feedback")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ✅ Strengths")
        strengths = summary_data.get("strengths", [])
        if strengths:
            for strength in strengths:
                st.write(f"• {strength}")
        else:
            st.write("No specific strengths identified")
    
    with col2:
        st.markdown("#### 🔧 Areas for Improvement")
        improvements = summary_data.get("areas_for_improvement", [])
        if improvements:
            for improvement in improvements:
                st.write(f"• {improvement}")
        else:
            st.write("No specific areas identified")
    
    # AI Summary
    if ai_summary_data and ai_summary_data.get("summary"):
        st.markdown("### 🤖 AI Analysis")
        st.write(ai_summary_data["summary"])
    
    # Export options
    st.markdown("### 📄 Export Report")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Download PDF", use_container_width=True):
            pdf_data = generate_pdf_report(summary_data, ai_summary_data)
            if pdf_data:
                st.download_button(
                    label="📥 Download PDF Report",
                    data=pdf_data,
                    file_name=f"interview_report_{session_id}.pdf",
                    mime="application/pdf"
                )
    
    with col2:
        if st.button("📝 Download Text", use_container_width=True):
            text_report = generate_text_report(summary_data, ai_summary_data)
            st.download_button(
                label="📥 Download Text Report",
                data=text_report,
                file_name=f"interview_report_{session_id}.txt",
                mime="text/plain"
            )
    
    with col3:
        if st.button("🔄 Start New Interview", use_container_width=True):
            reset_interview_state()
            st.rerun()

if __name__ == "__main__":
    main()
