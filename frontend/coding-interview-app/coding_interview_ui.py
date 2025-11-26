"""
LeetCode/GeeksforGeeks-Style Coding Interview UI
Streamlit frontend for the coding interview service
"""

import streamlit as st
import requests
import json
from typing import Dict, Any, Optional
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8001"

# Page configuration
st.set_page_config(
    page_title="Coding Interview - SkillScreen",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for LeetCode-style UI
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .question-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
    }
    .code-editor {
        background: #1e1e1e;
        color: #d4d4d4;
        font-family: 'Courier New', monospace;
        border-radius: 8px;
        padding: 1rem;
    }
    .test-result-pass {
        background: #d4edda;
        color: #155724;
        padding: 0.5rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    }
    .test-result-fail {
        background: #f8d7da;
        color: #721c24;
        padding: 0.5rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    }
    .difficulty-easy {
        color: #5cb85c;
        font-weight: bold;
    }
    .difficulty-medium {
        color: #f0ad4e;
        font-weight: bold;
    }
    .difficulty-hard {
        color: #d9534f;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None
    if 'current_question' not in st.session_state:
        st.session_state.current_question = None
    if 'questions' not in st.session_state:
        st.session_state.questions = []
    if 'code' not in st.session_state:
        st.session_state.code = ""
    if 'language' not in st.session_state:
        st.session_state.language = "python"
    if 'resume_data' not in st.session_state:
        st.session_state.resume_data = None
    if 'job_description' not in st.session_state:
        st.session_state.job_description = None

def make_api_request(method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
    """Make API request to coding interview service"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        else:
            return None
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return None

def upload_resume(file) -> Optional[Dict]:
    """Upload and parse resume"""
    try:
        files = {"file": (file.name, file.read(), file.type)}
        response = requests.post(f"{API_BASE_URL}/api/coding-interview/upload-resume", files=files)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("parsed_data")
        else:
            st.error(f"Failed to parse resume: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error uploading resume: {str(e)}")
        return None

def upload_job_description(job_title: str, company: str, description: str, requirements: str) -> Optional[Dict]:
    """Upload job description"""
    try:
        data = {
            "job_title": job_title,
            "company": company,
            "description": description,
            "requirements": requirements
        }
        response = requests.post(
            f"{API_BASE_URL}/api/coding-interview/upload-job-description",
            data=data
        )
        
        if response.status_code == 200:
            return response.json().get("job_data")
        else:
            st.error(f"Failed to upload job description: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error uploading job description: {str(e)}")
        return None

def start_interview(resume_data: Dict, job_description: Dict, num_questions: int) -> Optional[Dict]:
    """Start coding interview"""
    try:
        data = {
            "resume_data": resume_data,
            "job_description": job_description,
            "num_questions": num_questions
        }
        response = requests.post(f"{API_BASE_URL}/api/coding-interview/start", json=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to start interview: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error starting interview: {str(e)}")
        return None

def run_code(session_id: str, code: str, language: str) -> Optional[Dict]:
    """Run code without test cases (just execute)"""
    try:
        data = {
            "code": code,
            "language": language
        }
        response = requests.post(
            f"{API_BASE_URL}/api/coding-interview/sessions/{session_id}/run-code",
            json=data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to run code: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error running code: {str(e)}")
        return None

def submit_code(session_id: str, code: str, language: str) -> Optional[Dict]:
    """Submit code solution"""
    try:
        data = {
            "code": code,
            "language": language
        }
        response = requests.post(
            f"{API_BASE_URL}/api/coding-interview/sessions/{session_id}/submit-code",
            json=data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to submit code: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error submitting code: {str(e)}")
        return None

def get_next_question(session_id: str) -> Optional[Dict]:
    """Get next question"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/coding-interview/sessions/{session_id}/next-question"
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to get next question: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error getting next question: {str(e)}")
        return None

def show_question(question: Dict):
    """Display question in LeetCode style"""
    st.markdown(f'<div class="question-card">', unsafe_allow_html=True)
    
    # Title and difficulty
    difficulty = question.get("difficulty", "medium").lower()
    difficulty_class = f"difficulty-{difficulty}"
    st.markdown(f'### {question.get("title", "Coding Question")} <span class="{difficulty_class}">[{difficulty.upper()}]</span>', unsafe_allow_html=True)
    
    # Description
    st.markdown("**Problem Description:**")
    st.markdown(question.get("description", ""))
    
    # Examples
    examples = question.get("examples", [])
    if examples:
        st.markdown("**Examples:**")
        for i, example in enumerate(examples, 1):
            with st.expander(f"Example {i}"):
                st.code(f"Input: {example.get('input', '')}\nOutput: {example.get('output', '')}")
                if example.get("explanation"):
                    st.markdown(f"*Explanation: {example.get('explanation')}*")
    
    # Constraints
    constraints = question.get("constraints", [])
    if constraints:
        st.markdown("**Constraints:**")
        for constraint in constraints:
            st.markdown(f"- {constraint}")
    
    # Hints
    hints = question.get("hints", [])
    if hints:
        with st.expander("💡 Hints"):
            for i, hint in enumerate(hints, 1):
                st.markdown(f"{i}. {hint}")
    
    # Topics
    topics = question.get("topics", [])
    if topics:
        st.markdown("**Topics:** " + ", ".join([f"`{topic}`" for topic in topics]))
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_code_editor(question: Dict, session_id: str):
    """Show code editor in LeetCode style"""
    st.markdown("### 💻 Code Editor")
    
    # Language selector
    code_templates = question.get("code_templates", {})
    available_languages = list(code_templates.keys()) if code_templates else ["python"]
    
    if available_languages:
        selected_language = st.selectbox(
            "Select Language",
            available_languages,
            index=0 if st.session_state.language not in available_languages else available_languages.index(st.session_state.language)
        )
        st.session_state.language = selected_language
        
        # Initialize code from template
        if not st.session_state.code and selected_language in code_templates:
            st.session_state.code = code_templates[selected_language]
    
    # Code editor
    code = st.text_area(
        "Write your solution:",
        value=st.session_state.code,
        height=400,
        key="code_editor",
        label_visibility="collapsed"
    )
    st.session_state.code = code
    
    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        run_button = st.button("▶️ Run", type="primary", use_container_width=True)
    
    with col2:
        submit_button = st.button("📤 Submit", use_container_width=True)
    
    # Handle button clicks
    if run_button:
        if not code.strip():
            st.warning("Please write some code first!")
        else:
            with st.spinner("Running code..."):
                result = run_code(session_id, code, st.session_state.language)
                
                if result:
                    execution_result = result.get("execution_result", {})
                    
                    # Show execution output
                    st.markdown("### 📺 Output")
                    
                    # Check if code executed successfully
                    if execution_result.get("success", False):
                        output = execution_result.get("output", "").strip()
                        error = execution_result.get("error", "").strip()
                        
                        if output:
                            st.success("✅ Code executed successfully!")
                            st.code(output, language="text")
                        elif error:
                            st.error(f"❌ Execution Error:\n{error}")
                        else:
                            st.info("ℹ️ Code executed successfully but produced no output. Make sure your code includes print statements or returns values.")
                    else:
                        error = execution_result.get("error", "Unknown error")
                        st.error(f"❌ Code execution failed:\n{error}")
                else:
                    st.error("Failed to execute code. Please try again.")
    
    if submit_button:
        if not code.strip():
            st.warning("Please write some code first!")
        else:
            with st.spinner("Submitting and testing code..."):
                result = submit_code(session_id, code, st.session_state.language)
                
                if result:
                    execution_result = result.get("execution_result", {})
                    
                    # Show test results
                    test_results = execution_result.get("test_results", [])
                    if test_results:
                        st.markdown("### 🧪 Test Results")
                        passed = sum(1 for t in test_results if t.get("passed", False))
                        total = len(test_results)
                        
                        st.metric("Score", f"{passed}/{total}", f"{int(passed/total*100) if total > 0 else 0}%")
                        
                        for i, test in enumerate(test_results, 1):
                            if test.get("passed"):
                                st.markdown(f'<div class="test-result-pass">✅ Test {i}: PASSED</div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="test-result-fail">❌ Test {i}: FAILED</div>', unsafe_allow_html=True)
                                expected = test.get('expected_output', '')
                                actual = test.get('actual_output', '')
                                st.code(f"Expected: {expected}\nGot: {actual}")
                    else:
                        st.warning("No test results available")

def main():
    """Main application"""
    initialize_session_state()
    
    # Header
    st.markdown('<div class="main-header"><h1>💻 Coding Interview Platform</h1><p>LeetCode-style coding challenges powered by AI</p></div>', unsafe_allow_html=True)
    
    # Sidebar for setup
    with st.sidebar:
        st.header("📋 Setup")
        
        # Resume upload
        st.subheader("📄 Resume")
        resume_file = st.file_uploader("Upload Resume (PDF)", type=['pdf'])
        
        if resume_file and st.button("Parse Resume"):
            with st.spinner("Parsing resume..."):
                parsed_resume = upload_resume(resume_file)
                if parsed_resume:
                    st.session_state.resume_data = parsed_resume
                    st.success("✅ Resume parsed successfully!")
                    st.json(parsed_resume)
        
        # Job description
        st.subheader("💼 Job Description")
        job_title = st.text_input("Job Title")
        company = st.text_input("Company")
        job_description = st.text_area("Job Description", height=100)
        requirements = st.text_area("Requirements", height=100)
        
        if st.button("Set Job Description"):
            if job_title and job_description:
                job_data = upload_job_description(job_title, company, job_description, requirements)
                if job_data:
                    st.session_state.job_description = {
                        "job_title": job_title,
                        "company": company,
                        "description": job_description,
                        "required_skills": requirements.split(",") if requirements else []
                    }
                    st.success("✅ Job description set!")
        
        # Start interview
        st.markdown("---")
        num_questions = st.slider("Number of Questions", 1, 15, 5)
        
        if st.button("🚀 Start Interview", type="primary", use_container_width=True):
            if st.session_state.resume_data and st.session_state.job_description:
                with st.spinner("Generating questions..."):
                    result = start_interview(
                        st.session_state.resume_data,
                        st.session_state.job_description,
                        num_questions
                    )
                    if result:
                        st.session_state.session_id = result.get("session_id")
                        # Handle question response - it might be nested
                        question_data = result.get("question")
                        if question_data:
                            st.session_state.current_question = question_data
                            st.session_state.questions = [question_data]
                            # Store total questions for progress tracking
                            st.session_state.total_questions = result.get("total_questions", 5)
                            st.success("✅ Interview started!")
                            st.rerun()
                        else:
                            st.error("Failed to get question from response")
            else:
                st.error("Please upload resume and set job description first!")
    
    # Main content
    if st.session_state.session_id and st.session_state.current_question:
        # Show progress
        current_q_num = len(st.session_state.questions)
        total_questions = st.session_state.get("total_questions", st.session_state.current_question.get("total_questions", 5))
        
        st.progress(current_q_num / total_questions)
        st.caption(f"Question {current_q_num} of {total_questions}")
        
        # Two column layout: Question | Code Editor
        col1, col2 = st.columns([1, 1])
        
        with col1:
            show_question(st.session_state.current_question)
        
        with col2:
            show_code_editor(st.session_state.current_question, st.session_state.session_id)
        
        # Next question button
        if current_q_num < total_questions:
            if st.button("➡️ Next Question", use_container_width=True):
                with st.spinner("Generating next question..."):
                    next_q = get_next_question(st.session_state.session_id)
                    if next_q:
                        if next_q.get("session_complete"):
                            st.success("🎉 Interview completed!")
                        else:
                            # Update current question
                            question_data = next_q.get("question")
                            if question_data:
                                st.session_state.current_question = question_data
                                st.session_state.questions.append(question_data)
                                st.session_state.code = ""  # Reset code
                                # Update total questions if provided
                                if next_q.get("total_questions"):
                                    st.session_state.total_questions = next_q.get("total_questions")
                                st.rerun()
                            else:
                                st.error("Failed to get next question. Response: " + str(next_q))
                    else:
                        st.error("Failed to generate next question")
        else:
            st.success("🎉 All questions completed!")
    else:
        st.info("👈 Please set up your resume and job description in the sidebar to start the interview!")

if __name__ == "__main__":
    main()

