"""
Streamlit Frontend for SkillScreen FastAPI Backend
This frontend connects to the FastAPI backend to provide a user-friendly interface
"""

import streamlit as st
import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional
import time
import base64
from io import BytesIO
import sys
import os

# Add the backend utils to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'interview-service', 'utils'))
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
            st.error(f"Unsupported HTTP method: {method}")
            return None
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to FastAPI backend. Please ensure it's running on http://localhost:8000")
        return None
    except Exception as e:
        st.error(f"❌ Error making API request: {str(e)}")
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
        "name": resume_data.get("name", "Candidate"),
        "email": resume_data.get("email", "candidate@example.com"),
        "resume_text": resume_data.get("resume_text", ""),
        "experience_years": resume_data.get("experience_years", 0),
        "skills": resume_data.get("skills", [])
    }
    
    result = make_api_request("POST", "/candidates", candidate_data)
    if result:
        return result.get("candidate_id")
    return None

def create_job(job_data: Dict) -> Optional[str]:
    """Create job in the backend"""
    result = make_api_request("POST", "/jobs", job_data)
    if result:
        return result.get("job_id")
    return None

def start_interview(candidate_id: str, job_id: str) -> Optional[Dict]:
    """Start interview session"""
    interview_data = {
        "candidate_id": candidate_id,
        "job_id": job_id
    }
    
    return make_api_request("POST", "/interviews/start", interview_data)

def submit_response(session_id: str, response_text: str) -> Optional[Dict]:
    """Submit candidate response"""
    response_data = {
        "response_text": response_text
    }
    
    return make_api_request("POST", f"/interviews/{session_id}/respond", response_data)

def get_interview_summary(session_id: str) -> Optional[Dict]:
    """Get interview summary"""
    return make_api_request("GET", f"/interviews/{session_id}/summary")

def get_ai_summary(session_id: str) -> Optional[Dict]:
    """Get AI-generated summary"""
    return make_api_request("GET", f"/interviews/{session_id}/ai-summary")

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
           python SkillScreen/simple_fastapi_app.py
           ```
        
        2. **Ensure it's running** on `http://localhost:8000`
        
        3. **Refresh this page** once the backend is running
        """)
        return
    
    # Show welcome message if no session is active
    if 'current_session_id' not in st.session_state:
        show_welcome_message()
    
    st.markdown("---")
    
    # Display parsed data in main frame
    if 'parsed_resume' in st.session_state or 'parsed_job' in st.session_state:
        st.subheader("🔍 Parsed Data Review")
        st.info("📋 Review the extracted information before starting the interview")
        
        # Parsing methodology note removed for cleaner UI
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'parsed_resume' in st.session_state:
                st.markdown("### 📄 Parsed Resume")
                resume = st.session_state.parsed_resume
                st.write(f"**Name:** {resume['name']}")
                st.write(f"**Email:** {resume['email']}")
                st.write(f"**Phone:** {resume['phone']}")
                st.write(f"**Experience:** {resume['experience_years']} years")
                st.write(f"**Skills Found:** {', '.join(resume['skills'])}")
                with st.expander("View Full Resume Data"):
                    st.json(resume)
        
        with col2:
            if 'parsed_job' in st.session_state:
                st.markdown("### 💼 Parsed Job")
                job = st.session_state.parsed_job
                st.write(f"**Position:** {job['title']}")
                st.write(f"**Required Skills:** {', '.join(job['required_skills'])}")
                st.write(f"**Experience Level:** {job['experience_level']}")
                with st.expander("View Full Job Data"):
                    st.json(job)
        
        st.markdown("---")
    
    # Initialize session state
    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = None
    if 'candidate_id' not in st.session_state:
        st.session_state.candidate_id = None
    if 'job_id' not in st.session_state:
        st.session_state.job_id = None
    if 'interview_messages' not in st.session_state:
        st.session_state.interview_messages = []
    if 'interview_completed' not in st.session_state:
        st.session_state.interview_completed = False
    if 'interview_terminated' not in st.session_state:
        st.session_state.interview_terminated = False
    
    # Sidebar for setup
    with st.sidebar:
        st.header("📋 Interview Setup")
        
        # Resume upload
        st.subheader("📄 Resume")
        resume_file = st.file_uploader("Upload Resume", type=['pdf', 'docx', 'txt'], key="resume_upload")
        resume_text = st.text_area("Or paste resume text:", height=100, key="resume_text")
        
        # Job description
        st.subheader("💼 Job Description")
        job_title = st.text_input("Job Title:", placeholder="e.g., Senior Python Developer")
        company_name = st.text_input("Company:", placeholder="e.g., TechCorp")
        job_description = st.text_area("Job Description:", height=150, key="job_description")
        
        # Parse and create candidate/job
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 Parse Resume", use_container_width=True):
                if resume_file or resume_text:
                    import re
                    from datetime import datetime
                    
                    # Extract text from PDF if file is uploaded
                    if resume_file is not None:
                        try:
                            import io
                            # Use OpenResume-based PDF parser
                            parsed_data = resume_parser.parse_resume_from_pdf(resume_file)
                            resume_text = parsed_data['raw_text']
                            pdf_parsed = True
                            st.success("✅ PDF parsed using OpenResume-based parser")
                        except Exception as e:
                            st.warning(f"⚠️ OpenResume parser failed: {str(e)}")
                            # Fallback to basic extraction
                            try:
                                import PyPDF2
                                pdf_reader = PyPDF2.PdfReader(resume_file)
                                resume_text = ""
                                for page in pdf_reader.pages:
                                    resume_text += page.extract_text() + "\n"
                                pdf_parsed = True
                                st.success("✅ PDF parsed using basic text extraction")
                            except Exception as e:
                                st.warning(f"⚠️ Basic extraction failed: {str(e)}")
                                
                        except Exception as e:
                            st.error(f"❌ Error reading PDF file: {str(e)}")
                            st.info("💡 **Tip**: Try copying and pasting the text content instead of uploading the PDF file.")
                            return
                    else:
                        # Use pasted text
                        resume_text = resume_text or ""
                    
                    # Use OpenResume-based parser
                    parsed_data = resume_parser.parse_resume(resume_text)
                    
                    parsed_resume = {
                        "name": parsed_data['name'] or "Candidate",
                        "email": parsed_data['email'] or "candidate@example.com",
                        "phone": parsed_data['phone'] or "Not provided",
                        "resume_text": resume_text or "Resume uploaded",
                        "experience_years": parsed_data['experience_years'],
                        "skills": parsed_data['skills'] if parsed_data['skills'] else ["General"],
                        "education": parsed_data['education'],
                        "work_experience": parsed_data['work_experience'],
                        "parsing_method": "OpenResume-based parser (Tang, 2024)"
                    }
                    
                    candidate_id = create_candidate(parsed_resume)
                    if candidate_id:
                        st.session_state.candidate_id = candidate_id
                        st.session_state.parsed_resume = parsed_resume
                        st.success("✅ Resume parsed and candidate created!")
                    else:
                        st.error("❌ Failed to create candidate")
                else:
                    st.error("❌ Please upload a resume or paste text")
        
        with col2:
            if st.button("💼 Parse Job", use_container_width=True):
                if job_title and company_name and job_description:
                    import re
                    
                    # Extract skills from job description
                    job_lower = job_description.lower()
                    
                    # Common tech skills to look for (using regex for word boundaries)
                    tech_skills = ['python', 'java', 'javascript', 'c\\+\\+', 'sql', 'fastapi', 'django', 
                                   'flask', 'react', 'vue', 'angular', 'node', 'mongodb', 'postgresql',
                                   'machine learning', 'deep learning', 'nlp', 'computer vision',
                                   'data science', 'data analysis', 'tableau', 'power bi', 'excel',
                                   'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'git', 'streamlit',
                                   'tensorflow', 'pytorch', 'pandas', 'numpy', 'scikit-learn', 'ml']
                    
                    required_skills = []
                    for skill in tech_skills:
                        if re.search(rf'\b{skill}\b', job_lower):
                            # Clean up display name
                            display_skill = skill.replace('\\+\\+', '++').title()
                            if display_skill not in required_skills:
                                required_skills.append(display_skill)
                    
                    # Determine experience level
                    if 'senior' in job_lower or 'lead' in job_lower:
                        exp_level = "senior"
                    elif 'junior' in job_lower or 'entry' in job_lower or 'intern' in job_lower:
                        exp_level = "junior"
                    else:
                        exp_level = "mid"
                    
                    job_data = {
                        "title": job_title,
                        "company": company_name,
                        "description": job_description,
                        "required_skills": required_skills if required_skills else ["General"],
                        "experience_level": exp_level
                    }
                    
                    job_id = create_job(job_data)
                    if job_id:
                        st.session_state.job_id = job_id
                        st.session_state.parsed_job = job_data
                        st.success("✅ Job created successfully!")
                    else:
                        st.error("❌ Failed to create job")
                else:
                    st.error("❌ Please fill in job title, company, and description")
        
        
        # Start interview button
        if st.session_state.candidate_id and st.session_state.job_id:
            if st.button("🚀 Start Interview", type="primary", use_container_width=True):
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
                            
                            st.success("✅ Interview started successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to start interview")
                            
                except Exception as e:
                    st.error(f"❌ Error starting interview: {str(e)}")
        
        # Show current status
        if st.session_state.candidate_id:
            st.success("✅ Candidate ready")
        if st.session_state.job_id:
            st.success("✅ Job ready")
        if st.session_state.current_session_id:
            st.success("✅ Interview active")
    
    # Main content area
    if st.session_state.current_session_id and not st.session_state.interview_completed:
        show_interview_interface()
    elif st.session_state.interview_completed:
        if st.session_state.interview_terminated:
            show_termination_summary()
        else:
            show_interview_summary()
    else:
        st.info("👈 Please set up your resume and job description in the sidebar to start the interview.")

def show_interview_interface():
    """Show the main interview interface"""
    session_id = st.session_state.current_session_id
    
    # Get current interview status
    interview_data = make_api_request("GET", f"/interviews/{session_id}")
    if not interview_data:
        st.error("❌ Failed to get interview data")
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
        round_info = "🧠 Round 3: Theoretical Assessment"
        round_desc = "Concepts, best practices, and deep knowledge"
    
    # Progress bar
    progress = min(question_num / 9, 1.0)
    st.progress(progress, text=f"Question {question_num}/9")
    st.markdown(f"### {round_info}")
    st.markdown(f"*{round_desc}*")
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Questions Asked", interview_data["questions_asked"])
    with col2:
        st.metric("Responses Given", interview_data["responses_received"])
    with col3:
        st.metric("Current Score", f"{interview_data['total_score']:.1f}")
    
    st.markdown("---")
    
    # Chat interface
    st.subheader("💬 Interview Chat")
    
    # Display chat messages
    for message in st.session_state.interview_messages:
        if message["role"] == "assistant":
            with st.chat_message("assistant"):
                st.write(message["content"])
        elif message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
    
    # Current question
    if interview_data["current_question"]:
        with st.chat_message("assistant"):
            st.write(interview_data["current_question"])
    
    # Response input
    if interview_data["status"] == "active":
        user_response = st.chat_input("Type your response here...")
        
        if user_response:
            # Add user response to chat
            st.session_state.interview_messages.append({
                "role": "user",
                "content": user_response
            })
            
            # Submit response
            try:
                with st.spinner("Processing your response..."):
                    result = submit_response(session_id, user_response)
                    
                    if result:
                        if result["status"] == "continue":
                            # Show warnings if any
                            if result.get("warnings"):
                                for warning in result["warnings"]:
                                    st.warning(warning)
                            
                            # Show anti-cheating counters
                            if result.get("duplicate_count", 0) > 0:
                                st.info(f"⚠️ Duplicate responses detected: {result['duplicate_count']}")
                            
                            if result.get("ai_generated_count", 0) > 0:
                                st.info(f"🤖 AI-generated content detected: {result['ai_generated_count']}")
                            
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
                            st.error(result.get("message", "Interview terminated due to policy violations"))
                            st.session_state.interview_completed = True
                            st.session_state.interview_terminated = True
                            st.rerun()
                    else:
                        st.error("❌ Failed to submit response")
                        
            except Exception as e:
                st.error(f"❌ Error submitting response: {str(e)}")

def show_termination_summary():
    """Show termination summary for anti-cheating violations"""
    session_id = st.session_state.current_session_id
    
    st.markdown("## ❌ Interview Terminated")
    
    # Get interview data
    interview_data = make_api_request("GET", f"/interviews/{session_id}")
    if not interview_data:
        st.error("❌ Failed to get interview data")
        return
    
    # Display termination message
    st.error("🚨 **Interview Terminated Due to Policy Violations**")
    
    st.markdown("### 📋 Termination Details")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Final Score", "0/10")
    
    with col2:
        st.metric("Questions Answered", interview_data.get("questions_asked", 0))
    
    with col3:
        st.metric("Status", "Terminated")
    
    # Show termination reason
    termination_reason = interview_data.get("termination_reason", "anti_cheating")
    termination_message = interview_data.get("termination_message", "Interview terminated due to policy violations")
    
    st.markdown("### ⚠️ Reason for Termination")
    st.warning(termination_message)
    
    # Show policy violations
    st.markdown("### 📜 Policy Violations Detected")
    
    violations = []
    if interview_data.get("duplicate_count", 0) > 0:
        violations.append(f"• Duplicate responses: {interview_data['duplicate_count']} times")
    
    if interview_data.get("ai_generated_count", 0) > 0:
        violations.append(f"• AI-generated content: {interview_data['ai_generated_count']} times")
    
    if violations:
        for violation in violations:
            st.write(violation)
    else:
        st.write("• Multiple suspicious activities detected")
    
    # Show warnings history
    warnings = interview_data.get("warnings", [])
    if warnings:
        st.markdown("### ⚠️ Warnings Issued")
        for i, warning in enumerate(warnings, 1):
            st.write(f"{i}. {warning}")
    
    # Show next steps
    st.markdown("### 📝 Next Steps")
    st.info("""
    **For Future Interviews:**
    - Provide original, personal responses based on your own experience
    - Avoid copying from external sources or AI tools
    - Ensure each response is unique and relevant to the question
    - Take time to think before responding
    """)
    
    # Restart option
    st.markdown("---")
    if st.button("🔄 Start New Interview", type="secondary", use_container_width=True):
        # Reset session state
        st.session_state.current_session_id = None
        st.session_state.candidate_id = None
        st.session_state.job_id = None
        st.session_state.interview_messages = []
        st.session_state.interview_completed = False
        st.session_state.interview_terminated = False
        st.rerun()

def show_interview_summary():
    """Show interview summary and results"""
    session_id = st.session_state.current_session_id
    
    # Get interview summary and AI summary
    summary_data = get_interview_summary(session_id)
    ai_summary_data = get_ai_summary(session_id)
    
    if not summary_data:
        st.error("❌ Failed to get interview summary")
        return
    
    st.markdown("## 🎉 Interview Completed!")
    
    # Display basic metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Final Score", f"{summary_data['overall_score']}/10")
    
    with col2:
        st.metric("Total Questions", summary_data['total_questions'])
    
    with col3:
        st.metric("Recommendation", summary_data['recommendation'])
    
    # Show AI-generated summary
    if ai_summary_data:
        st.markdown("### 🤖 AI-Generated Feedback")
        st.markdown("**Human-like interview feedback:**")
        st.markdown(ai_summary_data['ai_summary'])
        st.markdown("---")
    
    # Show violations analysis with funny messages
    if summary_data.get('violations_analysis'):
        violations_data = summary_data['violations_analysis']
        funny_analysis = violations_data.get('funny_analysis', {})
        
        st.markdown("### 🎭 Interview Integrity Analysis")
        
        # Display funny title and message
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"#### {funny_analysis.get('title', '🎭 Analysis Complete')}")
            st.markdown(f"**{funny_analysis.get('message', 'Analysis completed!')}**")
        with col2:
            st.markdown(f"# {funny_analysis.get('emoji', '🎭')}")
        
        # Show fun fact
        if funny_analysis.get('fun_fact'):
            st.info(f"💡 **Fun Fact:** {funny_analysis['fun_fact']}")
        
        # Show violation statistics
        if violations_data.get('violation_count', 0) > 0:
            st.markdown("#### 📊 Violation Statistics")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Violations", violations_data.get('violation_count', 0))
            with col2:
                st.metric("Duplicate Responses", violations_data.get('duplicate_count', 0))
            with col3:
                st.metric("AI-Generated Content", violations_data.get('ai_generated_count', 0))
            
            # Show detailed violations
            violations = violations_data.get('violations', [])
            if violations:
                st.markdown("#### 🔍 Detailed Violations")
                
                for i, violation in enumerate(violations, 1):
                    violation_type = violation.get('type', 'unknown')
                    question_num = violation.get('question', 0)
                    response_preview = violation.get('response', '')
                    
                    if violation_type == 'duplicate':
                        st.warning(f"**#{i} Duplicate Response (Question {question_num}):** {response_preview}")
                    elif violation_type == 'ai_generated':
                        st.error(f"**#{i} AI-Generated Content (Question {question_num}):** {response_preview}")
        else:
            st.success("🎉 **Clean Interview!** No violations detected - you provided original, authentic responses throughout!")
        
        st.markdown("---")
    
    # Show detailed summary
    st.markdown("### 📊 Executive Summary")
    st.write(summary_data['summary'])
    
    # Show strengths and areas for improvement
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ✅ Strengths")
        for strength in summary_data['strengths']:
            st.write(f"• {strength}")
    
    with col2:
        st.markdown("#### 📈 Areas for Improvement")
        for improvement in summary_data['areas_for_improvement']:
            st.write(f"• {improvement}")
    
    # Show detailed assessment
    st.markdown("### 📋 Detailed Assessment")
    assessment = summary_data['detailed_assessment']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Technical Skills", f"{assessment['technical_skills']}/10")
    
    with col2:
        st.metric("Communication", f"{assessment['communication']}/10")
    
    with col3:
        st.metric("Cultural Fit", f"{assessment['cultural_fit']}/10")
    
    # Download options
    st.markdown("---")
    st.markdown("### 📥 Download Interview Report")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Download PDF Report", type="primary"):
            if REPORTLAB_AVAILABLE:
                pdf_buffer = generate_pdf_report(summary_data, ai_summary_data)
                if pdf_buffer:
                    st.download_button(
                        label="📥 Download PDF",
                        data=pdf_buffer.getvalue(),
                        file_name=f"interview_report_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.error("❌ Failed to generate PDF")
            else:
                st.error("❌ PDF generation not available. Install reportlab: `pip install reportlab`")
    
    with col2:
        if st.button("📝 Download Text Report"):
            text_content = generate_text_report(summary_data, ai_summary_data)
            st.download_button(
                label="📥 Download Text Report",
                data=text_content,
                file_name=f"interview_report_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
    
    with col3:
        if st.button("📊 Download JSON Data"):
            json_data = json.dumps(summary_data, indent=2, default=str)
            st.download_button(
                label="📥 Download JSON",
                data=json_data,
                file_name=f"interview_data_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    # Restart option
    st.markdown("---")
    if st.button("🔄 Start New Interview", type="secondary", use_container_width=True):
        # Reset session state
        st.session_state.current_session_id = None
        st.session_state.candidate_id = None
        st.session_state.job_id = None
        st.session_state.interview_messages = []
        st.session_state.interview_completed = False
        st.rerun()

def generate_pdf_report(summary_data, ai_summary_data):
    """Generate PDF report"""
    if not REPORTLAB_AVAILABLE:
        return None
    
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.darkblue,
            alignment=1
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        normal_style = styles['Normal']
        
        # Build PDF content
        story = []
        
        # Title
        story.append(Paragraph("INTERVIEW REPORT", title_style))
        story.append(Paragraph("SkillScreen - AI Interview Assistant", normal_style))
        story.append(Spacer(1, 20))
        
        # Basic info
        story.append(Paragraph("INTERVIEW SUMMARY", heading_style))
        story.append(Paragraph(f"<b>Candidate:</b> {summary_data.get('candidate_name', 'N/A')}", normal_style))
        story.append(Paragraph(f"<b>Position:</b> {summary_data.get('job_title', 'N/A')}", normal_style))
        story.append(Paragraph(f"<b>Final Score:</b> {summary_data['overall_score']}/10", normal_style))
        story.append(Paragraph(f"<b>Recommendation:</b> {summary_data['recommendation']}", normal_style))
        story.append(Paragraph(f"<b>Total Questions:</b> {summary_data['total_questions']}", normal_style))
        story.append(Spacer(1, 20))
        
        # AI Summary
        if ai_summary_data:
            story.append(Paragraph("AI-GENERATED FEEDBACK", heading_style))
            story.append(Paragraph(ai_summary_data['ai_summary'], normal_style))
            story.append(Spacer(1, 20))
        
        # Executive Summary
        story.append(Paragraph("EXECUTIVE SUMMARY", heading_style))
        story.append(Paragraph(summary_data['summary'], normal_style))
        story.append(Spacer(1, 20))
        
        # Strengths
        story.append(Paragraph("STRENGTHS", heading_style))
        for strength in summary_data['strengths']:
            story.append(Paragraph(f"• {strength}", normal_style))
        story.append(Spacer(1, 15))
        
        # Areas for Improvement
        story.append(Paragraph("AREAS FOR IMPROVEMENT", heading_style))
        for improvement in summary_data['areas_for_improvement']:
            story.append(Paragraph(f"• {improvement}", normal_style))
        story.append(Spacer(1, 15))
        
        # Detailed Assessment
        story.append(Paragraph("DETAILED ASSESSMENT", heading_style))
        assessment = summary_data['detailed_assessment']
        story.append(Paragraph(f"<b>Technical Skills:</b> {assessment['technical_skills']}/10", normal_style))
        story.append(Paragraph(f"<b>Communication:</b> {assessment['communication']}/10", normal_style))
        story.append(Paragraph(f"<b>Cultural Fit:</b> {assessment['cultural_fit']}/10", normal_style))
        story.append(Spacer(1, 20))
        
        # Footer
        story.append(Paragraph(f"<i>Report generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</i>", normal_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")
        return None

def generate_text_report(summary_data, ai_summary_data):
    """Generate text report"""
    report = f"""
INTERVIEW REPORT
SkillScreen - AI Interview Assistant
Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

========================================

INTERVIEW SUMMARY
========================================
Candidate: {summary_data.get('candidate_name', 'N/A')}
Position: {summary_data.get('job_title', 'N/A')}
Final Score: {summary_data['overall_score']}/10
Recommendation: {summary_data['recommendation']}
Total Questions: {summary_data['total_questions']}

========================================

AI-GENERATED FEEDBACK
========================================
"""
    
    if ai_summary_data:
        report += ai_summary_data['ai_summary']
    else:
        report += "AI-generated feedback not available."
    
    report += f"""

========================================

EXECUTIVE SUMMARY
========================================
{summary_data['summary']}

========================================

STRENGTHS
========================================
"""
    
    for strength in summary_data['strengths']:
        report += f"• {strength}\n"
    
    report += f"""
========================================

AREAS FOR IMPROVEMENT
========================================
"""
    
    for improvement in summary_data['areas_for_improvement']:
        report += f"• {improvement}\n"
    
    report += f"""
========================================

DETAILED ASSESSMENT
========================================
Technical Skills: {summary_data['detailed_assessment']['technical_skills']}/10
Communication: {summary_data['detailed_assessment']['communication']}/10
Cultural Fit: {summary_data['detailed_assessment']['cultural_fit']}/10

========================================

Report generated by SkillScreen AI Interview Assistant
"""
    
    return report

if __name__ == "__main__":
    main()
