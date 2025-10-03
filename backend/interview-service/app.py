"""
SkillScreen - Chat-based Interview AI Assistant
Main Streamlit application for conducting automated interviews
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import os
from typing import Dict, List, Optional

# Import our custom modules
from resume_parser import ResumeParser, ParsedResume
from job_parser import JobParser, ParsedJobDescription
from interview_engine import InterviewEngine
from llm_integration import InterviewQuestion, InterviewResponse
from config import config_manager, config
from logger import logger, log_info, log_error, log_warning

# Page configuration
st.set_page_config(
    page_title=config.ui.page_title,
    page_icon=config.ui.page_icon,
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main application function"""
    st.title("🎯 SkillScreen - AI Interview Assistant")
    st.markdown("**Automated Interview Platform with Dynamic Question Generation**")
    st.markdown("---")
    
    # Initialize session state
    if 'interview_engine' not in st.session_state:
        st.session_state.interview_engine = None
    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = None
    if 'interview_messages' not in st.session_state:
        st.session_state.interview_messages = []
    if 'resume_parsed' not in st.session_state:
        st.session_state.resume_parsed = None
    if 'job_parsed' not in st.session_state:
        st.session_state.job_parsed = None
    
    # Sidebar navigation
    with st.sidebar:
        st.header("Navigation")
        page = st.selectbox(
            "Choose a page:",
            ["Start Interview", "Active Interview", "Interview Results", "Settings"]
        )
        
        # API Key configuration
        st.header("Configuration")
        gemini_api_key = st.text_input(
            "Gemini API Key", 
            type="password",
            value=os.getenv('GEMINI_API_KEY', ''),
            help="Enter your Google Gemini API key"
        )
        
        if gemini_api_key:
            os.environ['GEMINI_API_KEY'] = gemini_api_key
            if st.session_state.interview_engine is None:
                try:
                    st.session_state.interview_engine = InterviewEngine(gemini_api_key)
                    st.success("✅ Interview engine initialized!")
                except Exception as e:
                    st.error(f"❌ Error initializing engine: {str(e)}")
    
    # Route to appropriate page
    if page == "Start Interview":
        start_interview_page()
    elif page == "Active Interview":
        active_interview_page()
    elif page == "Interview Results":
        interview_results_page()
    elif page == "Settings":
        settings_page()

def start_interview_page():
    """Page for starting a new interview"""
    st.header("🚀 Start New Interview")
    
    # Check if engine is initialized
    if st.session_state.interview_engine is None:
        st.error("❌ Please configure your Gemini API key in the sidebar first.")
        return
    
    # Two-column layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📄 Resume Input")
        resume_input_method = st.radio(
            "How would you like to input the resume?",
            ["Paste Text", "Upload File"]
        )
        
        resume_text = ""
        if resume_input_method == "Paste Text":
            resume_text = st.text_area(
                "Paste resume text here:",
                height=300,
                placeholder="Paste the candidate's resume text here..."
            )
        else:
            uploaded_file = st.file_uploader(
                "Upload resume file",
                type=['txt', 'pdf', 'docx'],
                help="Supported formats: TXT, PDF, DOCX"
            )
            if uploaded_file:
                if uploaded_file.type == "text/plain":
                    resume_text = str(uploaded_file.read(), "utf-8")
                else:
                    st.warning("File parsing for PDF/DOCX not implemented yet. Please use text format.")
    
    with col2:
        st.subheader("💼 Job Description")
        job_input_method = st.radio(
            "How would you like to input the job description?",
            ["Paste Text", "Upload File"]
        )
        
        job_description = ""
        if job_input_method == "Paste Text":
            job_description = st.text_area(
                "Paste job description here:",
                height=300,
                placeholder="Paste the job description here..."
            )
        else:
            uploaded_file = st.file_uploader(
                "Upload job description file",
                type=['txt', 'pdf', 'docx'],
                help="Supported formats: TXT, PDF, DOCX"
            )
            if uploaded_file:
                if uploaded_file.type == "text/plain":
                    job_description = str(uploaded_file.read(), "utf-8")
                else:
                    st.warning("File parsing for PDF/DOCX not implemented yet. Please use text format.")
    
    # Interview configuration
    st.subheader("⚙️ Interview Configuration")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        interview_type = st.selectbox(
            "Interview Type",
            ["mixed", "technical", "behavioral"],
            help="Choose the focus of the interview"
        )
    
    with col2:
        max_questions = st.slider(
            "Maximum Questions",
            min_value=5,
            max_value=15,
            value=10,
            help="Maximum number of questions to ask"
        )
    
    with col3:
        difficulty = st.selectbox(
            "Difficulty Level",
            ["easy", "medium", "hard"],
            help="Overall difficulty of questions"
        )
    
    # Parse inputs
    if st.button("🔍 Parse Resume & Job Description", type="primary"):
        if not resume_text.strip():
            st.error("❌ Please provide resume text.")
            return
        if not job_description.strip():
            st.error("❌ Please provide job description.")
            return
        
        with st.spinner("Parsing resume and job description..."):
            try:
                # Parse resume
                resume_parser = ResumeParser()
                parsed_resume = resume_parser.parse_resume(resume_text)
                st.session_state.resume_parsed = parsed_resume
                
                # Parse job description
                job_parser = JobParser()
                parsed_job = job_parser.parse_job_description(job_description)
                st.session_state.job_parsed = parsed_job
                
                st.success("✅ Parsing completed!")
                
                # Display parsed information
                display_parsed_info(parsed_resume, parsed_job)
                
            except Exception as e:
                st.error(f"❌ Error parsing: {str(e)}")
    
    # Start interview button
    if st.session_state.resume_parsed and st.session_state.job_parsed:
        if st.button("🎯 Start Interview", type="primary", use_container_width=True):
            try:
                with st.spinner("Starting interview..."):
                    session_id = st.session_state.interview_engine.start_interview(
                        resume_text=resume_text,
                        job_description=job_description,
                        interview_type=interview_type
                    )
                    
                    st.session_state.current_session_id = session_id
                    st.session_state.interview_messages = []
                    
                    # Get initial question
                    current_question = st.session_state.interview_engine.get_current_question(session_id)
                    
                    if current_question:
                        st.session_state.interview_messages.append({
                            "role": "assistant",
                            "content": current_question['question'],
                            "question_type": current_question['question_type'],
                            "difficulty": current_question['difficulty']
                        })
                    
                    st.success("🎉 Interview started! Navigate to 'Active Interview' to continue.")
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Error starting interview: {str(e)}")

def active_interview_page():
    """Page for conducting the active interview"""
    st.header("💬 Active Interview")
    
    if st.session_state.current_session_id is None:
        st.warning("⚠️ No active interview session. Please start an interview first.")
        return
    
    # Get session status
    try:
        session_status = st.session_state.interview_engine.get_session_status(st.session_state.current_session_id)
        
        # Display session info
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Candidate", session_status['candidate_name'])
        with col2:
            st.metric("Position", session_status['job_title'])
        with col3:
            st.metric("Questions Asked", session_status['total_questions'])
        with col4:
            st.metric("Responses Given", session_status['total_responses'])
        
        # Interview progress
        if session_status['total_questions'] > 0:
            progress = session_status['total_responses'] / session_status['total_questions']
            st.progress(progress, text=f"Progress: {session_status['total_responses']}/{session_status['total_questions']} questions")
        
        # Chat interface
        st.subheader("💬 Interview Chat")
        
        # Display chat messages
        for message in st.session_state.interview_messages:
            if message["role"] == "assistant":
                with st.chat_message("assistant"):
                    st.markdown(message["content"])
                    if "question_type" in message:
                        st.caption(f"Type: {message['question_type'].title()} | Difficulty: {message['difficulty'].title()}")
            else:
                with st.chat_message("user"):
                    st.markdown(message["content"])
        
        # Chat input
        if not session_status['is_completed']:
            if prompt := st.chat_input("Type your answer here..."):
                # Add user message to chat
                st.session_state.interview_messages.append({"role": "user", "content": prompt})
                
                # Display user message
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # Submit response and get next question
                with st.spinner("Processing your response..."):
                    try:
                        response_data = st.session_state.interview_engine.submit_response(
                            st.session_state.current_session_id, prompt
                        )
                        
                        # Display response evaluation
                        if 'response_evaluation' in response_data:
                            eval_data = response_data['response_evaluation']
                            
                            # Show evaluation metrics
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Relevance", f"{eval_data['relevance_score']:.2f}")
                            with col2:
                                st.metric("Technical", f"{eval_data['technical_accuracy']:.2f}")
                            with col3:
                                st.metric("Communication", f"{eval_data['communication_quality']:.2f}")
                            with col4:
                                st.metric("Confidence", f"{eval_data['confidence_level']:.2f}")
                            
                            # Show strengths and improvements
                            if eval_data['strengths']:
                                st.success(f"✅ **Strengths:** {', '.join(eval_data['strengths'])}")
                            
                            if eval_data['areas_for_improvement']:
                                st.info(f"💡 **Areas for Improvement:** {', '.join(eval_data['areas_for_improvement'])}")
                            
                            if not eval_data['is_on_topic']:
                                st.warning("⚠️ Response seems off-topic. Please try to stay focused on the question.")
                        
                        # Check if interview is completed
                        if response_data.get('is_completed', False):
                            st.success("🎉 Interview completed! Navigate to 'Interview Results' to see the summary.")
                            st.session_state.interview_messages.append({
                                "role": "assistant",
                                "content": "Interview completed! Thank you for your time."
                            })
                        else:
                            # Add next question to chat
                            if response_data.get('current_question'):
                                st.session_state.interview_messages.append({
                                    "role": "assistant",
                                    "content": response_data['current_question'],
                                    "question_type": response_data.get('question_type', ''),
                                    "difficulty": response_data.get('question_context', '')
                                })
                        
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error processing response: {str(e)}")
        else:
            st.success("✅ Interview completed! Check the results below.")
            
            # Show final summary
            try:
                summary = st.session_state.interview_engine.get_interview_summary(st.session_state.current_session_id)
                display_interview_summary(summary)
            except Exception as e:
                st.error(f"❌ Error getting summary: {str(e)}")
    
    except Exception as e:
        st.error(f"❌ Error getting session status: {str(e)}")

def interview_results_page():
    """Page for viewing interview results"""
    st.header("📊 Interview Results")
    
    if st.session_state.current_session_id is None:
        st.warning("⚠️ No interview session available.")
        return
    
    try:
        # Get interview summary
        summary = st.session_state.interview_engine.get_interview_summary(st.session_state.current_session_id)
        
        # Display summary
        display_interview_summary(summary)
        
        # Download results
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Download Results (JSON)"):
                json_data = json.dumps(summary, indent=2)
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name=f"interview_results_{st.session_state.current_session_id}.json",
                    mime="application/json"
                )
        
        with col2:
            if st.button("🔄 Start New Interview"):
                st.session_state.current_session_id = None
                st.session_state.interview_messages = []
                st.session_state.resume_parsed = None
                st.session_state.job_parsed = None
                st.rerun()
    
    except Exception as e:
        st.error(f"❌ Error getting interview results: {str(e)}")

def settings_page():
    """Page for application settings"""
    st.header("⚙️ Settings")
    
    st.subheader("🔧 Interview Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.number_input(
            "Maximum Questions",
            min_value=5,
            max_value=20,
            value=10,
            help="Maximum number of questions per interview"
        )
        
        st.number_input(
            "Off-topic Threshold",
            min_value=0.1,
            max_value=1.0,
            value=0.3,
            step=0.1,
            help="Threshold for detecting off-topic responses"
        )
    
    with col2:
        st.number_input(
            "Max Off-topic Responses",
            min_value=1,
            max_value=10,
            value=3,
            help="Maximum number of off-topic responses before ending interview"
        )
        
        st.selectbox(
            "Default Interview Type",
            ["mixed", "technical", "behavioral"],
            help="Default interview type when not specified"
        )
    
    st.subheader("📊 Analytics")
    
    if st.button("📈 View Interview Analytics"):
        try:
            active_sessions = st.session_state.interview_engine.get_active_sessions()
            
            if active_sessions:
                df = pd.DataFrame(active_sessions)
                st.dataframe(df, use_container_width=True)
                
                # Analytics charts
                if len(active_sessions) > 1:
                    st.subheader("📊 Session Analytics")
                    
                    # Interview duration chart
                    fig = px.bar(df, x='candidate_name', y='start_time', title='Interview Sessions')
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No active interview sessions found.")
        
        except Exception as e:
            st.error(f"❌ Error getting analytics: {str(e)}")
    
    st.subheader("🗑️ Cleanup")
    
    if st.button("🧹 Clear All Sessions", type="secondary"):
        if st.session_state.interview_engine:
            try:
                # Get all active sessions
                active_sessions = st.session_state.interview_engine.get_active_sessions()
                
                # Clean up each session
                for session in active_sessions:
                    st.session_state.interview_engine.cleanup_session(session['session_id'])
                
                st.success(f"✅ Cleared {len(active_sessions)} sessions")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error clearing sessions: {str(e)}")

def display_parsed_info(parsed_resume: ParsedResume, parsed_job: ParsedJobDescription):
    """Display parsed resume and job information"""
    st.subheader("📋 Parsed Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**👤 Candidate Information**")
        st.write(f"**Name:** {parsed_resume.name}")
        st.write(f"**Email:** {parsed_resume.email}")
        st.write(f"**Phone:** {parsed_resume.phone}")
        st.write(f"**Location:** {parsed_resume.location}")
        
        if parsed_resume.summary:
            st.write(f"**Summary:** {parsed_resume.summary[:200]}...")
        
        st.write(f"**Skills:** {', '.join(parsed_resume.skills[:10])}")
        st.write(f"**Experience:** {len(parsed_resume.experience)} positions")
        st.write(f"**Education:** {len(parsed_resume.education)} entries")
    
    with col2:
        st.markdown("**💼 Job Information**")
        st.write(f"**Title:** {parsed_job.title}")
        st.write(f"**Company:** {parsed_job.company}")
        st.write(f"**Location:** {parsed_job.location}")
        st.write(f"**Type:** {parsed_job.job_type}")
        st.write(f"**Level:** {parsed_job.experience_level}")
        
        if parsed_job.salary_range:
            st.write(f"**Salary:** {parsed_job.salary_range}")
        
        st.write(f"**Required Skills:** {', '.join(parsed_job.skills_required[:10])}")
        st.write(f"**Requirements:** {len(parsed_job.requirements)} items")

def display_interview_summary(summary: Dict):
    """Display comprehensive interview summary"""
    st.subheader("📊 Interview Summary")
    
    # Overall metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Overall Score", f"{summary['overall_score']:.2f}")
    with col2:
        st.metric("Technical Score", f"{summary['technical_score']:.2f}")
    with col3:
        st.metric("Communication Score", f"{summary['communication_score']:.2f}")
    with col4:
        st.metric("Confidence Score", f"{summary['confidence_score']:.2f}")
    
    # Recommendation
    recommendation_color = {
        'hire': 'green',
        'no_hire': 'red',
        'maybe': 'orange'
    }
    
    st.markdown(f"**Recommendation:** :{recommendation_color.get(summary['recommendation'], 'gray')}[{summary['recommendation'].upper()}]")
    
    # Assessment
    st.subheader("📝 Assessment")
    st.write(summary['assessment'])
    
    # Strengths and improvements
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("✅ Key Strengths")
        for strength in summary['key_strengths']:
            st.write(f"• {strength}")
    
    with col2:
        st.subheader("💡 Areas for Improvement")
        for improvement in summary['areas_for_improvement']:
            st.write(f"• {improvement}")
    
    # Technical and communication assessment
    st.subheader("🔍 Detailed Assessment")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Technical Competency:**")
        st.write(summary['technical_competency'])
    
    with col2:
        st.markdown("**Communication Skills:**")
        st.write(summary['communication_skills'])
    
    # Question-by-question breakdown
    if 'question_breakdown' in summary and summary['question_breakdown']:
        st.subheader("📋 Question-by-Question Analysis")
        
        for qa in summary['question_breakdown']:
            with st.expander(f"Q{qa['question_number']}: {qa['question'][:50]}..."):
                st.write(f"**Question:** {qa['question']}")
                st.write(f"**Type:** {qa['question_type']} | **Difficulty:** {qa['difficulty']}")
                st.write(f"**Response:** {qa['response']}")
                
                # Scores
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Relevance", f"{qa['relevance_score']:.2f}")
                with col2:
                    st.metric("Technical", f"{qa['technical_accuracy']:.2f}")
                with col3:
                    st.metric("Communication", f"{qa['communication_quality']:.2f}")
                with col4:
                    st.metric("Confidence", f"{qa['confidence_level']:.2f}")
                
                if qa['strengths']:
                    st.write(f"**Strengths:** {', '.join(qa['strengths'])}")
                if qa['areas_for_improvement']:
                    st.write(f"**Areas for Improvement:** {', '.join(qa['areas_for_improvement'])}")
                
                if not qa['is_on_topic']:
                    st.warning("⚠️ Response was off-topic")

if __name__ == "__main__":
    main()