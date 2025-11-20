"""
SQLAlchemy models for SkillScreen database based on ERD structure.
This module defines all database models for the interview platform.
"""

from sqlalchemy import (
    Column, String, Text, Integer, BigInteger, Boolean, Numeric, 
    DateTime, ForeignKey, Enum, JSON, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from enum import Enum as PyEnum

Base = declarative_base()

# Constants for foreign key table names
FK_ORGANIZATIONS_ID = "organizations.id"
FK_USERS_ID = "users.id"
FK_INTERVIEWS_ID = "interviews.id"
FK_INTERVIEW_SESSIONS_ID = "interview_sessions.id"

# Enums
class UserRole(PyEnum):
    ADMIN = "admin"
    RECRUITER = "recruiter"
    INTERVIEWER = "interviewer"
    CANDIDATE = "candidate"
    TECHNICAL_EVALUATOR = "technical_evaluator"
    COMPLIANCE_OFFICER = "compliance_officer"

class InterviewStatus(PyEnum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class InterviewMode(PyEnum):
    CHAT = "chat"
    AUDIO = "audio"
    VIDEO = "video"
    HYBRID = "hybrid"

class ScoreDimension(PyEnum):
    TECHNICAL_SKILLS = "technical_skills"
    SOFT_SKILLS = "soft_skills"
    COMMUNICATION = "communication"
    PROBLEM_SOLVING = "problem_solving"
    LEADERSHIP = "leadership"
    CULTURAL_FIT = "cultural_fit"
    OVERALL = "overall"

class DifficultyLevel(PyEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"

class Recommendation(PyEnum):
    STRONG_HIRE = "strong_hire"
    HIRE = "hire"
    NO_HIRE = "no_hire"
    STRONG_NO_HIRE = "strong_no_hire"
    NEEDS_REVIEW = "needs_review"

# Base model with common fields
class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

# Core Models
class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=True)
    settings = Column(JSONB, nullable=True)
    
    # Relationships
    users = relationship("User", back_populates="organization")
    job_positions = relationship("JobPosition", back_populates="organization")
    interview_templates = relationship("InterviewTemplate", back_populates="organization")
    coding_questions = relationship("CodingQuestion", back_populates="organization")
    interviews = relationship("Interview", back_populates="organization")
    webhooks = relationship("Webhook", back_populates="organization")
    audit_logs = relationship("AuditLog", back_populates="organization")

class User(Base, TimestampMixin):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey(FK_ORGANIZATIONS_ID), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    # Use native PostgreSQL enum with explicit values to match database
    role = Column(Enum(UserRole, name='user_role', values_callable=lambda x: [e.value for e in x]), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    profile_data = Column(JSONB, nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    created_job_positions = relationship("JobPosition", foreign_keys="JobPosition.created_by", back_populates="creator")
    created_interview_templates = relationship("InterviewTemplate", foreign_keys="InterviewTemplate.created_by", back_populates="creator")
    created_coding_questions = relationship("CodingQuestion", foreign_keys="CodingQuestion.created_by", back_populates="creator")
    candidate_interviews = relationship("Interview", foreign_keys="Interview.candidate_id", back_populates="candidate")
    interviewer_interviews = relationship("Interview", foreign_keys="Interview.interviewer_id", back_populates="interviewer")
    scores_created = relationship("Score", foreign_keys="Score.created_by", back_populates="creator")
    assessments_reviewed = relationship("Assessment", foreign_keys="Assessment.reviewed_by", back_populates="reviewer")
    evidence_clips_created = relationship("EvidenceClip", foreign_keys="EvidenceClip.created_by", back_populates="creator")
    reports_generated = relationship("Report", foreign_keys="Report.generated_by", back_populates="generator")
    proctoring_events_reviewed = relationship("ProctoringEvent", foreign_keys="ProctoringEvent.reviewed_by", back_populates="reviewer")
    audit_logs = relationship("AuditLog", back_populates="user")

class JobPosition(Base, TimestampMixin):
    __tablename__ = "job_positions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey(FK_ORGANIZATIONS_ID), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    required_skills = Column(JSONB, nullable=True)
    department = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey(FK_USERS_ID), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="job_positions")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_job_positions")
    interviews = relationship("Interview", back_populates="job_position")

class InterviewTemplate(Base, TimestampMixin):
    __tablename__ = "interview_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey(FK_ORGANIZATIONS_ID), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=True)
    questions = Column(JSONB, nullable=True)
    settings = Column(JSONB, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey(FK_USERS_ID), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="interview_templates")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_interview_templates")
    interviews = relationship("Interview", back_populates="template")

class Interview(Base, TimestampMixin):
    __tablename__ = "interviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey(FK_ORGANIZATIONS_ID), nullable=False)
    job_position_id = Column(UUID(as_uuid=True), ForeignKey("job_positions.id"), nullable=False)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey(FK_USERS_ID), nullable=True)
    interviewer_id = Column(UUID(as_uuid=True), ForeignKey(FK_USERS_ID), nullable=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey("interview_templates.id"), nullable=False)
    status = Column(Enum(InterviewStatus), nullable=False)
    mode = Column(Enum(InterviewMode), nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    settings = Column(JSONB, nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="interviews")
    job_position = relationship("JobPosition", back_populates="interviews")
    candidate = relationship("User", foreign_keys=[candidate_id], back_populates="candidate_interviews")
    interviewer = relationship("User", foreign_keys=[interviewer_id], back_populates="interviewer_interviews")
    template = relationship("InterviewTemplate", back_populates="interviews")
    sessions = relationship("InterviewSession", back_populates="interview")
    responses = relationship("Response", back_populates="interview")
    media_files = relationship("MediaFile", back_populates="interview")
    coding_sessions = relationship("CodingSession", back_populates="interview")
    transcripts = relationship("Transcript", back_populates="interview")
    evidence_clips = relationship("EvidenceClip", back_populates="interview")
    ai_analysis = relationship("AIAnalysis", back_populates="interview")
    assessments = relationship("Assessment", back_populates="interview")
    proctoring_events = relationship("ProctoringEvent", back_populates="interview")
    reports = relationship("Report", back_populates="interview")

class InterviewSession(Base):
    __tablename__ = "interview_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), ForeignKey(FK_INTERVIEWS_ID), nullable=False)
    question_id = Column(String(255), nullable=True)
    question_text = Column(Text, nullable=True)
    question_type = Column(String(100), nullable=True)
    candidate_response = Column(Text, nullable=True)
    response_duration = Column(Integer, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    session_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    interview = relationship("Interview", back_populates="sessions")
    responses = relationship("Response", back_populates="session")
    media_files = relationship("MediaFile", back_populates="session")
    transcripts = relationship("Transcript", back_populates="session")
    evidence_clips = relationship("EvidenceClip", back_populates="session")
    ai_analysis = relationship("AIAnalysis", back_populates="session")
    proctoring_events = relationship("ProctoringEvent", back_populates="session")

class Response(Base):
    __tablename__ = "responses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), ForeignKey(FK_INTERVIEWS_ID), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey(FK_INTERVIEW_SESSIONS_ID), nullable=False)
    responder_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    response_text = Column(Text, nullable=True)
    response_json = Column(JSONB, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    interview = relationship("Interview", back_populates="responses")
    session = relationship("InterviewSession", back_populates="responses")
    responder = relationship("User")
    scores = relationship("Score", back_populates="response")

class Score(Base, TimestampMixin):
    __tablename__ = "scores"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), ForeignKey(FK_INTERVIEWS_ID), nullable=False)
    response_id = Column(UUID(as_uuid=True), ForeignKey("responses.id"), nullable=False)
    dimension = Column(Enum(ScoreDimension), nullable=False)
    auto_score = Column(Numeric(5, 2), nullable=True)
    human_override_score = Column(Numeric(5, 2), nullable=True)
    rubric = Column(JSONB, nullable=True)
    evidence_refs = Column(JSONB, nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey(FK_USERS_ID), nullable=True)
    
    # Relationships
    interview = relationship("Interview")
    response = relationship("Response", back_populates="scores")
    creator = relationship("User", foreign_keys=[created_by], back_populates="scores_created")

class MediaFile(Base, TimestampMixin):
    __tablename__ = "media_files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), ForeignKey(FK_INTERVIEWS_ID), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=True)
    file_type = Column(String(50), nullable=True)
    file_path = Column(String(500), nullable=True)
    storage_uri = Column(String(1024), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    duration = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    checksum = Column(String(255), nullable=True)
    session_metadata = Column(JSONB, nullable=True)
    
    # Relationships
    interview = relationship("Interview", back_populates="media_files")
    session = relationship("InterviewSession", back_populates="media_files")
    evidence_clips = relationship("EvidenceClip", back_populates="media_file")

class CodingQuestion(Base, TimestampMixin):
    __tablename__ = "coding_questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey(FK_ORGANIZATIONS_ID), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    difficulty = Column(Enum(DifficultyLevel), nullable=True)
    languages = Column(JSONB, nullable=True)
    test_cases = Column(JSONB, nullable=True)
    starter_code = Column(JSONB, nullable=True)
    solution = Column(JSONB, nullable=True)
    tags = Column(JSONB, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey(FK_USERS_ID), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="coding_questions")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_coding_questions")
    coding_sessions = relationship("CodingSession", back_populates="question")

class CodingSession(Base):
    __tablename__ = "coding_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), ForeignKey(FK_INTERVIEWS_ID), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("coding_questions.id"), nullable=False)
    language = Column(String(50), nullable=True)
    code = Column(Text, nullable=True)
    execution_results = Column(JSONB, nullable=True)
    is_correct = Column(Boolean, nullable=True)
    execution_time = Column(Integer, nullable=True)
    memory_usage = Column(Integer, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    interview = relationship("Interview", back_populates="coding_sessions")
    question = relationship("CodingQuestion", back_populates="coding_sessions")

class Transcript(Base):
    __tablename__ = "transcripts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), ForeignKey(FK_INTERVIEWS_ID), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=True)
    speaker = Column(String(100), nullable=True)
    text = Column(Text, nullable=True)
    confidence_score = Column(Numeric(3, 2), nullable=True)
    start_time = Column(Integer, nullable=True)
    end_time = Column(Integer, nullable=True)
    word_timestamps = Column(JSONB, nullable=True)
    disfluencies = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    interview = relationship("Interview", back_populates="transcripts")
    session = relationship("InterviewSession", back_populates="transcripts")

class EvidenceClip(Base, TimestampMixin):
    __tablename__ = "evidence_clips"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), ForeignKey(FK_INTERVIEWS_ID), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=True)
    media_file_id = Column(UUID(as_uuid=True), ForeignKey("media_files.id"), nullable=False)
    start_ms = Column(Integer, nullable=False)
    end_ms = Column(Integer, nullable=False)
    label = Column(String(255), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey(FK_USERS_ID), nullable=True)
    
    # Relationships
    interview = relationship("Interview", back_populates="evidence_clips")
    session = relationship("InterviewSession", back_populates="evidence_clips")
    media_file = relationship("MediaFile", back_populates="evidence_clips")
    creator = relationship("User", foreign_keys=[created_by], back_populates="evidence_clips_created")

class AIAnalysis(Base):
    __tablename__ = "ai_analysis"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), ForeignKey(FK_INTERVIEWS_ID), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=True)
    analysis_type = Column(String(100), nullable=True)
    service_name = Column(String(100), nullable=True)
    raw_results = Column(JSONB, nullable=True)
    confidence_score = Column(Numeric(3, 2), nullable=True)
    processing_time = Column(Integer, nullable=True)
    version = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    interview = relationship("Interview", back_populates="ai_analysis")
    session = relationship("InterviewSession", back_populates="ai_analysis")

class Assessment(Base, TimestampMixin):
    __tablename__ = "assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), ForeignKey(FK_INTERVIEWS_ID), nullable=False)
    overall_score = Column(Numeric(5, 2), nullable=True)
    hard_skills_score = Column(Numeric(5, 2), nullable=True)
    soft_skills_score = Column(Numeric(5, 2), nullable=True)
    communication_score = Column(Numeric(5, 2), nullable=True)
    technical_score = Column(Numeric(5, 2), nullable=True)
    proctoring_risk_score = Column(Numeric(5, 2), nullable=True)
    recommendation = Column(Enum(Recommendation), nullable=True)
    evidence_clips = Column(JSONB, nullable=True)
    summary = Column(Text, nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    interview = relationship("Interview", back_populates="assessments")
    reviewer = relationship("User", foreign_keys=[reviewed_by], back_populates="assessments_reviewed")

class Webhook(Base, TimestampMixin):
    __tablename__ = "webhooks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey(FK_ORGANIZATIONS_ID), nullable=False)
    event_type = Column(String(100), nullable=True)
    url = Column(String(500), nullable=True)
    secret = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    last_triggered = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="webhooks")

class ProctoringEvent(Base):
    __tablename__ = "proctoring_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), ForeignKey(FK_INTERVIEWS_ID), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=True)
    event_type = Column(String(100), nullable=True)
    severity = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    rule_id = Column(String(100), nullable=True)
    event_time_ms = Column(Integer, nullable=True)
    evidence = Column(JSONB, nullable=True)
    flagged_for_review = Column(Boolean, default=False, nullable=False)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    interview = relationship("Interview", back_populates="proctoring_events")
    session = relationship("InterviewSession", back_populates="proctoring_events")
    reviewer = relationship("User", foreign_keys=[reviewed_by], back_populates="proctoring_events_reviewed")

class Candidate(Base, TimestampMixin):
    __tablename__ = "candidates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey(FK_ORGANIZATIONS_ID), nullable=False)
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    resume_url = Column(String(1024), nullable=True)
    skills = Column(JSONB, nullable=True)
    experience = Column(JSONB, nullable=True)
    education = Column(JSONB, nullable=True)
    projects = Column(JSONB, nullable=True)
    
    # Relationships
    organization = relationship("Organization")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey(FK_ORGANIZATIONS_ID), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=True)
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    changes = Column(JSONB, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="audit_logs")
    user = relationship("User", back_populates="audit_logs")

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), ForeignKey(FK_INTERVIEWS_ID), nullable=False)
    report_type = Column(String(100), nullable=True)
    format = Column(String(50), nullable=True)
    file_path = Column(String(500), nullable=True)
    generated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    generated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    interview = relationship("Interview", back_populates="reports")
    generator = relationship("User", foreign_keys=[generated_by], back_populates="reports_generated")

# Indexes for performance
Index('idx_interviews_organization_id', Interview.organization_id)
Index('idx_interviews_candidate_id', Interview.candidate_id)
Index('idx_interviews_status', Interview.status)
Index('idx_responses_interview_id', Response.interview_id)
Index('idx_responses_session_id', Response.session_id)
Index('idx_scores_interview_id', Score.interview_id)
Index('idx_scores_response_id', Score.response_id)
Index('idx_media_files_interview_id', MediaFile.interview_id)
Index('idx_transcripts_interview_id', Transcript.interview_id)
Index('idx_audit_logs_organization_id', AuditLog.organization_id)
Index('idx_audit_logs_user_id', AuditLog.user_id)
Index('idx_audit_logs_created_at', AuditLog.created_at)