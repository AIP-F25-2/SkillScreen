"""
Database operations for SkillScreen interview data
This module provides CRUD operations for storing interview information using repository pattern
"""

import sys
import os
sys.path.append("/common-service")

# Add parent directory to path for repositories
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from typing import Optional, List, Dict, Any
from db import UnitOfWork
from repositories.organization_repository import OrganizationRepository
from repositories.user_repository import UserRepository
from repositories.job_position_repository import JobPositionRepository
from repositories.interview_template_repository import InterviewTemplateRepository
from repositories.interview_repository import InterviewRepository
from repositories.interview_session_repository import InterviewSessionRepository
from repositories.response_repository import ResponseRepository
from repositories.score_repository import ScoreRepository
from repositories.assessment_repository import AssessmentRepository
from repositories.ai_analysis_repository import AIAnalysisRepository
from repositories.candidate_repository import CandidateRepository
from database.models import (
    Organization, User, JobPosition, InterviewTemplate, Interview,
    InterviewSession, Response, Score, Assessment, AIAnalysis, Candidate,
    UserRole, InterviewStatus, InterviewMode
)
from datetime import datetime, timezone


class InterviewDataService:
    """Service for managing interview data in the database using repository pattern"""
    
    def __init__(self, uow: Optional[UnitOfWork] = None):
        """
        Initialize the service with a UnitOfWork from common-service
        
        Args:
            uow: UnitOfWork instance from common-service. If None, creates a new one.
        """
        self.uow = uow or UnitOfWork()
        self._init_repositories()
    
    def _init_repositories(self):
        """Initialize all repositories"""
        self.org_repo = OrganizationRepository(self.uow)
        self.user_repo = UserRepository(self.uow)
        self.job_repo = JobPositionRepository(self.uow)
        self.template_repo = InterviewTemplateRepository(self.uow)
        self.interview_repo = InterviewRepository(self.uow)
        self.session_repo = InterviewSessionRepository(self.uow)
        self.response_repo = ResponseRepository(self.uow)
        self.score_repo = ScoreRepository(self.uow)
        self.assessment_repo = AssessmentRepository(self.uow)
        self.ai_analysis_repo = AIAnalysisRepository(self.uow)
        self.candidate_repo = CandidateRepository(self.uow)
    
    # Organization operations
    def create_organization(self, name: str, domain: Optional[str] = None, settings: Optional[Dict] = None) -> Organization:
        """Create a new organization"""
        return self.org_repo.create(name, domain, settings)
    
    def get_organization(self, org_id: str) -> Optional[Organization]:
        """Get organization by ID"""
        return self.org_repo.get_by_id(org_id)
    
    # User operations
    def create_user(self, organization_id: str, email: str, first_name: str, last_name: str, 
                   role: UserRole, password_hash: Optional[str] = None) -> User:
        """Create a new user"""
        return self.user_repo.create(organization_id, email, first_name, last_name, role, password_hash)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.user_repo.get_by_email(email)
    
    # Job Position operations
    def create_job_position(self, organization_id: str, title: str, description: Optional[str] = None,
                          required_skills: Optional[List[str]] = None, department: Optional[str] = None,
                          created_by: Optional[str] = None) -> JobPosition:
        """Create a new job position"""
        return self.job_repo.create(organization_id, title, description, required_skills, department, created_by)
    
    def get_job_position(self, job_id: str) -> Optional[JobPosition]:
        """Get job position by ID"""
        return self.job_repo.get_by_id(job_id)
    
    # Interview Template operations
    def create_interview_template(self, organization_id: str, name: str, template_type: str,
                                 questions: Optional[List[Dict]] = None, settings: Optional[Dict] = None,
                                 created_by: Optional[str] = None) -> InterviewTemplate:
        """Create a new interview template"""
        return self.template_repo.create(organization_id, name, template_type, questions, settings, created_by)
    
    def get_interview_template(self, template_id: str) -> Optional[InterviewTemplate]:
        """Get interview template by ID"""
        return self.template_repo.get_by_id(template_id)
    
    # Interview operations
    def create_interview(self, organization_id: str, job_position_id: str, template_id: str,
                        candidate_id: Optional[str] = None, interviewer_id: Optional[str] = None,
                        mode: InterviewMode = InterviewMode.CHAT, scheduled_at: Optional[datetime] = None) -> Interview:
        """Create a new interview"""
        return self.interview_repo.create(organization_id, job_position_id, template_id, candidate_id, interviewer_id, mode, scheduled_at)
    
    def start_interview(self, interview_id: str) -> Optional[Interview]:
        """Start an interview"""
        return self.interview_repo.start(interview_id)
    
    def complete_interview(self, interview_id: str) -> Optional[Interview]:
        """Complete an interview"""
        return self.interview_repo.complete(interview_id)
    
    def get_interview(self, interview_id: str) -> Optional[Interview]:
        """Get interview by ID"""
        return self.interview_repo.get_by_id(interview_id)
    
    def get_interviews_by_candidate(self, candidate_id: str) -> List[Interview]:
        """Get all interviews for a candidate"""
        return self.interview_repo.get_by_candidate_id(candidate_id)
    
    # Interview Session operations
    def create_interview_session(self, interview_id: str, question_id: Optional[str] = None,
                                question_text: Optional[str] = None, question_type: Optional[str] = None) -> InterviewSession:
        """Create a new interview session"""
        return self.session_repo.create(interview_id, question_id, question_text, question_type)
    
    def complete_interview_session(self, session_id: str, candidate_response: Optional[str] = None,
                                  response_duration: Optional[int] = None) -> Optional[InterviewSession]:
        """Complete an interview session"""
        return self.session_repo.complete(session_id, candidate_response, response_duration)
    
    def get_interview_sessions(self, interview_id: str) -> List[InterviewSession]:
        """Get all sessions for an interview"""
        return self.session_repo.get_by_interview_id(interview_id)
    
    # Response operations
    def create_response(self, interview_id: str, session_id: str, responder_id: str,
                       response_text: str, response_json: Optional[Dict] = None,
                       latency_ms: Optional[int] = None, duration_ms: Optional[int] = None) -> Response:
        """Create a new response"""
        return self.response_repo.create(interview_id, session_id, responder_id, response_text, response_json, latency_ms, duration_ms)
    
    def get_responses_by_interview(self, interview_id: str) -> List[Response]:
        """Get all responses for an interview"""
        return self.response_repo.get_by_interview_id(interview_id)
    
    # Score operations
    def create_score(self, interview_id: str, response_id: str, dimension: str,
                    auto_score: Optional[float] = None, human_override_score: Optional[float] = None,
                    rubric: Optional[Dict] = None, evidence_refs: Optional[List[str]] = None,
                    notes: Optional[str] = None, created_by: Optional[str] = None) -> Score:
        """Create a new score"""
        return self.score_repo.create(interview_id, response_id, dimension, auto_score, human_override_score, rubric, evidence_refs, notes, created_by)
    
    def get_scores_by_interview(self, interview_id: str) -> List[Score]:
        """Get all scores for an interview"""
        return self.score_repo.get_by_interview_id(interview_id)
    
    # Assessment operations
    def create_assessment(self, interview_id: str, overall_score: Optional[float] = None,
                         hard_skills_score: Optional[float] = None, soft_skills_score: Optional[float] = None,
                         communication_score: Optional[float] = None, technical_score: Optional[float] = None,
                         proctoring_risk_score: Optional[float] = None, recommendation: Optional[str] = None,
                         evidence_clips: Optional[List[str]] = None, summary: Optional[str] = None,
                         reviewer_notes: Optional[str] = None, reviewed_by: Optional[str] = None) -> Assessment:
        """Create a new assessment"""
        return self.assessment_repo.create(interview_id, overall_score, hard_skills_score, soft_skills_score,
                                          communication_score, technical_score, proctoring_risk_score,
                                          recommendation, evidence_clips, summary, reviewer_notes, reviewed_by)
    
    def get_assessment_by_interview(self, interview_id: str) -> Optional[Assessment]:
        """Get assessment for an interview"""
        return self.assessment_repo.get_by_interview_id(interview_id)
    
    # Utility methods
    def get_or_create_default_organization(self) -> Organization:
        """Get or create a default organization for testing"""
        return self.org_repo.get_or_create_default()
    
    def get_or_create_demo_user(self, email: str = "demo@skillscreen.com") -> User:
        """Get or create a demo user"""
        return self.user_repo.get_or_create_demo(email)
    
    # AI Analysis operations
    def create_ai_analysis(
        self,
        interview_id: str,
        session_id: Optional[str] = None,
        analysis_type: str = "text_analysis",
        service_name: str = "text-service",
        raw_results: Optional[Dict] = None,
        confidence_score: Optional[float] = None,
        processing_time: Optional[int] = None,
        version: str = "v1.0"
    ) -> AIAnalysis:
        """Create a new AI analysis record"""
        return self.ai_analysis_repo.create(interview_id, session_id, analysis_type, service_name,
                                           raw_results, confidence_score, processing_time, version)
    
    def get_ai_analysis_by_interview(self, interview_id: str) -> List[AIAnalysis]:
        """Get all AI analysis records for an interview"""
        return self.ai_analysis_repo.get_by_interview_id(interview_id)
    
    def get_ai_analysis_by_session(self, session_id: str) -> List[AIAnalysis]:
        """Get all AI analysis records for a session"""
        return self.ai_analysis_repo.get_by_session_id(session_id)
    
    # Candidate operations
    def create_candidate(
        self,
        organization_id: str,
        full_name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        location: Optional[str] = None,
        resume_url: Optional[str] = None,
        skills: Optional[List[str]] = None,
        experience: Optional[Dict] = None,
        education: Optional[Dict] = None,
        projects: Optional[List[Dict]] = None
    ) -> Candidate:
        """Create a new candidate"""
        return self.candidate_repo.create(organization_id, full_name, email, phone, location,
                                        resume_url, skills, experience, education, projects)
    
    def get_candidate(self, candidate_id: str) -> Optional[Candidate]:
        """Get candidate by ID"""
        return self.candidate_repo.get_by_id(candidate_id)
    
    def get_candidate_by_email(self, email: str) -> Optional[Candidate]:
        """Get candidate by email"""
        return self.candidate_repo.get_by_email(email)
    
    def get_candidates_by_organization(self, organization_id: str) -> List[Candidate]:
        """Get all candidates for an organization"""
        return self.candidate_repo.get_by_organization_id(organization_id)
    
    def update_candidate(
        self,
        candidate_id: str,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        location: Optional[str] = None,
        resume_url: Optional[str] = None,
        skills: Optional[List[str]] = None,
        experience: Optional[Dict] = None,
        education: Optional[Dict] = None,
        projects: Optional[List[Dict]] = None
    ) -> Optional[Candidate]:
        """Update candidate information"""
        return self.candidate_repo.update(candidate_id, full_name, email, phone, location,
                                        resume_url, skills, experience, education, projects)
    
    def commit(self):
        """Commit the current transaction"""
        self.uow.session.commit()
    
    def rollback(self):
        """Rollback the current transaction"""
        self.uow.session.rollback()
    
    def close(self):
        """Close the database session"""
        self.uow.session.close()
