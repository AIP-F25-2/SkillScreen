"""
Database models for SkillScreen production system
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class Candidate(Base):
    """Candidate information and profile"""
    __tablename__ = 'candidates'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(50))
    resume_text = Column(Text)
    resume_file_path = Column(String(500))
    skills = Column(JSON)  # List of skills
    experience_years = Column(Float)
    education = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    interviews = relationship("Interview", back_populates="candidate")

class Job(Base):
    """Job description and requirements"""
    __tablename__ = 'jobs'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    description = Column(Text)
    requirements = Column(JSON)  # List of requirements
    skills_required = Column(JSON)  # List of required skills
    experience_level = Column(String(50))  # Junior, Mid-level, Senior
    job_type = Column(String(50))  # Full-time, Part-time, Contract, Remote
    location = Column(String(255))
    salary_range = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    interviews = relationship("Interview", back_populates="job")

class Interview(Base):
    """Interview session and metadata"""
    __tablename__ = 'interviews'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = Column(String, ForeignKey('candidates.id'), nullable=False)
    job_id = Column(String, ForeignKey('jobs.id'), nullable=False)
    session_id = Column(String(100), unique=True, nullable=False)
    
    # Interview configuration
    interview_type = Column(String(50), default='mixed')  # mixed, technical, behavioral
    difficulty = Column(String(50), default='medium')  # easy, medium, hard
    max_questions = Column(Integer, default=15)
    target_duration_minutes = Column(Integer, default=12)
    
    # Interview state
    status = Column(String(50), default='scheduled')  # scheduled, in_progress, completed, terminated
    current_question_index = Column(Integer, default=0)
    total_questions_asked = Column(Integer, default=0)
    total_responses_received = Column(Integer, default=0)
    
    # Timing
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration_minutes = Column(Float)
    
    # Results
    overall_score = Column(Float)
    recommendation = Column(String(50))  # Hire, Strong Consider, Consider, Do Not Hire
    termination_reason = Column(String(100))  # completed, off_topic, duplicate_responses, etc.
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    candidate = relationship("Candidate", back_populates="interviews")
    job = relationship("Job", back_populates="interviews")
    questions = relationship("InterviewQuestion", back_populates="interview")
    responses = relationship("InterviewResponse", back_populates="interview")
    summary = relationship("InterviewSummary", back_populates="interview", uselist=False)

class InterviewQuestion(Base):
    """Individual questions asked during interview"""
    __tablename__ = 'interview_questions'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    interview_id = Column(String, ForeignKey('interviews.id'), nullable=False)
    question_index = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50))  # general, technical, theoretical
    difficulty = Column(String(50))  # easy, medium, hard
    round_number = Column(Integer)  # 1, 2, 3 for different rounds
    context = Column(Text)  # Additional context for the question
    
    # Timing
    asked_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    interview = relationship("Interview", back_populates="questions")
    responses = relationship("InterviewResponse", back_populates="question")

class InterviewResponse(Base):
    """Candidate responses to interview questions"""
    __tablename__ = 'interview_responses'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    interview_id = Column(String, ForeignKey('interviews.id'), nullable=False)
    question_id = Column(String, ForeignKey('interview_questions.id'), nullable=False)
    
    # Response content
    response_text = Column(Text, nullable=False)
    response_length = Column(Integer)
    
    # Evaluation scores
    overall_score = Column(Float)
    relevance_score = Column(Float)
    technical_accuracy_score = Column(Float)
    communication_score = Column(Float)
    depth_score = Column(Float)
    job_fit_score = Column(Float)
    
    # Analysis
    strengths = Column(JSON)  # List of strengths identified
    weaknesses = Column(JSON)  # List of weaknesses identified
    feedback = Column(Text)
    improvement_tips = Column(JSON)  # List of improvement suggestions
    
    # Anti-cheating flags
    is_duplicate = Column(Boolean, default=False)
    is_off_topic = Column(Boolean, default=False)
    response_time_seconds = Column(Float)
    
    # Timing
    received_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    interview = relationship("Interview", back_populates="responses")
    question = relationship("InterviewQuestion", back_populates="responses")

class InterviewSummary(Base):
    """Comprehensive interview summary and analysis"""
    __tablename__ = 'interview_summaries'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    interview_id = Column(String, ForeignKey('interviews.id'), nullable=False)
    
    # Executive summary
    executive_summary = Column(Text)
    overall_score = Column(Float)
    recommendation = Column(String(50))
    recommendation_reason = Column(Text)
    
    # Detailed assessments
    technical_assessment_score = Column(Float)
    technical_assessment_summary = Column(Text)
    communication_assessment_score = Column(Float)
    communication_assessment_summary = Column(Text)
    cultural_fit_score = Column(Float)
    cultural_fit_summary = Column(Text)
    
    # Analysis results
    strengths = Column(JSON)
    areas_for_improvement = Column(JSON)
    key_highlights = Column(JSON)
    red_flags = Column(JSON)
    improvement_tips = Column(JSON)
    next_steps = Column(JSON)
    
    # Interviewer notes
    interviewer_notes = Column(Text)
    
    # Metadata
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    interview = relationship("Interview", back_populates="summary")

class AuditLog(Base):
    """Audit trail for all system actions"""
    __tablename__ = 'audit_logs'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Action details
    action = Column(String(100), nullable=False)  # interview_started, response_received, etc.
    entity_type = Column(String(50))  # interview, candidate, job, etc.
    entity_id = Column(String(100))
    
    # User context
    user_id = Column(String(100))
    user_type = Column(String(50))  # candidate, recruiter, admin, system
    
    # Request details
    ip_address = Column(String(45))
    user_agent = Column(Text)
    request_id = Column(String(100))
    
    # Additional data
    metadata = Column(JSON)
    details = Column(Text)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)

class SystemConfig(Base):
    """System configuration and settings"""
    __tablename__ = 'system_config'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    value_type = Column(String(50))  # string, integer, float, boolean, json
    description = Column(Text)
    is_encrypted = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
