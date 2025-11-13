"""
Database operations for SkillScreen interview data
This module provides CRUD operations for storing interview information
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from database.models import (
    Organization, User, JobPosition, InterviewTemplate, Interview,
    InterviewSession, Response, Score, Assessment, AIAnalysis, Candidate,
    UserRole, InterviewStatus, InterviewMode
)
import uuid
from datetime import datetime, timezone

class InterviewDataService:
    """Service for managing interview data in the database"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    # Organization operations
    def create_organization(self, name: str, domain: Optional[str] = None, settings: Optional[Dict] = None) -> Organization:
        """Create a new organization"""
        org = Organization(
            name=name,
            domain=domain,
            settings=settings or {}
        )
        self.db.add(org)
        self.db.commit()
        self.db.refresh(org)
        return org
    
    def get_organization(self, org_id: str) -> Optional[Organization]:
        """Get organization by ID"""
        return self.db.query(Organization).filter(Organization.id == org_id).first()
    
    # User operations
    def create_user(self, organization_id: str, email: str, first_name: str, last_name: str, 
                   role: UserRole, password_hash: Optional[str] = None) -> User:
        """Create a new user"""
        # Use the enum value directly (lowercase) - database should accept it
        role_value = role.value if hasattr(role, 'value') else str(role)
        user = User(
            organization_id=organization_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role_value,
            password_hash=password_hash,
            is_active=True
        )
        self.db.add(user)
        self.db.commit()
        # Skip refresh to avoid enum mismatch on read - just return the object
        return user
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    # Job Position operations
    def create_job_position(self, organization_id: str, title: str, description: Optional[str] = None,
                          required_skills: Optional[List[str]] = None, department: Optional[str] = None,
                          created_by: Optional[str] = None) -> JobPosition:
        """Create a new job position"""
        job = JobPosition(
            organization_id=organization_id,
            title=title,
            description=description,
            required_skills=required_skills or [],
            department=department,
            created_by=created_by,
            is_active=True
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job
    
    def get_job_position(self, job_id: str) -> Optional[JobPosition]:
        """Get job position by ID"""
        return self.db.query(JobPosition).filter(JobPosition.id == job_id).first()
    
    # Interview Template operations
    def create_interview_template(self, organization_id: str, name: str, template_type: str,
                                 questions: Optional[List[Dict]] = None, settings: Optional[Dict] = None,
                                 created_by: Optional[str] = None) -> InterviewTemplate:
        """Create a new interview template"""
        template = InterviewTemplate(
            organization_id=organization_id,
            name=name,
            type=template_type,
            questions=questions or [],
            settings=settings or {},
            created_by=created_by
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template
    
    def get_interview_template(self, template_id: str) -> Optional[InterviewTemplate]:
        """Get interview template by ID"""
        return self.db.query(InterviewTemplate).filter(InterviewTemplate.id == template_id).first()
    
    # Interview operations
    def create_interview(self, organization_id: str, job_position_id: str, template_id: str,
                        candidate_id: Optional[str] = None, interviewer_id: Optional[str] = None,
                        mode: InterviewMode = InterviewMode.CHAT, scheduled_at: Optional[datetime] = None) -> Interview:
        """Create a new interview"""
        interview = Interview(
            organization_id=organization_id,
            job_position_id=job_position_id,
            template_id=template_id,
            candidate_id=candidate_id,
            interviewer_id=interviewer_id,
            status=InterviewStatus.SCHEDULED,
            mode=mode,
            scheduled_at=scheduled_at
        )
        self.db.add(interview)
        self.db.commit()
        self.db.refresh(interview)
        return interview
    
    def start_interview(self, interview_id: str) -> Optional[Interview]:
        """Start an interview"""
        interview = self.db.query(Interview).filter(Interview.id == interview_id).first()
        if interview:
            interview.status = InterviewStatus.IN_PROGRESS
            interview.started_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(interview)
        return interview
    
    def complete_interview(self, interview_id: str) -> Optional[Interview]:
        """Complete an interview"""
        interview = self.db.query(Interview).filter(Interview.id == interview_id).first()
        if interview:
            interview.status = InterviewStatus.COMPLETED
            interview.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(interview)
        return interview
    
    def get_interview(self, interview_id: str) -> Optional[Interview]:
        """Get interview by ID"""
        return self.db.query(Interview).filter(Interview.id == interview_id).first()
    
    def get_interviews_by_candidate(self, candidate_id: str) -> List[Interview]:
        """Get all interviews for a candidate"""
        return self.db.query(Interview).filter(Interview.candidate_id == candidate_id).order_by(desc(Interview.created_at)).all()
    
    # Interview Session operations
    def create_interview_session(self, interview_id: str, question_id: Optional[str] = None,
                                question_text: Optional[str] = None, question_type: Optional[str] = None) -> InterviewSession:
        """Create a new interview session"""
        session = InterviewSession(
            interview_id=interview_id,
            question_id=question_id,
            question_text=question_text,
            question_type=question_type,
            started_at=datetime.now(timezone.utc)
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def complete_interview_session(self, session_id: str, candidate_response: Optional[str] = None,
                                  response_duration: Optional[int] = None) -> Optional[InterviewSession]:
        """Complete an interview session"""
        session = self.db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        if session:
            session.candidate_response = candidate_response
            session.response_duration = response_duration
            session.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(session)
        return session
    
    def get_interview_sessions(self, interview_id: str) -> List[InterviewSession]:
        """Get all sessions for an interview"""
        return self.db.query(InterviewSession).filter(InterviewSession.interview_id == interview_id).order_by(InterviewSession.created_at).all()
    
    # Response operations
    def create_response(self, interview_id: str, session_id: str, responder_id: str,
                       response_text: str, response_json: Optional[Dict] = None,
                       latency_ms: Optional[int] = None, duration_ms: Optional[int] = None) -> Response:
        """Create a new response"""
        response = Response(
            interview_id=interview_id,
            session_id=session_id,
            responder_id=responder_id,
            response_text=response_text,
            response_json=response_json,
            latency_ms=latency_ms,
            duration_ms=duration_ms,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc)
        )
        self.db.add(response)
        self.db.commit()
        self.db.refresh(response)
        return response
    
    def get_responses_by_interview(self, interview_id: str) -> List[Response]:
        """Get all responses for an interview"""
        return self.db.query(Response).filter(Response.interview_id == interview_id).order_by(Response.created_at).all()
    
    # Score operations
    def create_score(self, interview_id: str, response_id: str, dimension: str,
                    auto_score: Optional[float] = None, human_override_score: Optional[float] = None,
                    rubric: Optional[Dict] = None, evidence_refs: Optional[List[str]] = None,
                    notes: Optional[str] = None, created_by: Optional[str] = None) -> Score:
        """Create a new score"""
        score = Score(
            interview_id=interview_id,
            response_id=response_id,
            dimension=dimension,
            auto_score=auto_score,
            human_override_score=human_override_score,
            rubric=rubric,
            evidence_refs=evidence_refs,
            notes=notes,
            created_by=created_by
        )
        self.db.add(score)
        self.db.commit()
        self.db.refresh(score)
        return score
    
    def get_scores_by_interview(self, interview_id: str) -> List[Score]:
        """Get all scores for an interview"""
        return self.db.query(Score).filter(Score.interview_id == interview_id).all()
    
    # Assessment operations
    def create_assessment(self, interview_id: str, overall_score: Optional[float] = None,
                         hard_skills_score: Optional[float] = None, soft_skills_score: Optional[float] = None,
                         communication_score: Optional[float] = None, technical_score: Optional[float] = None,
                         proctoring_risk_score: Optional[float] = None, recommendation: Optional[str] = None,
                         evidence_clips: Optional[List[str]] = None, summary: Optional[str] = None,
                         reviewer_notes: Optional[str] = None, reviewed_by: Optional[str] = None) -> Assessment:
        """Create a new assessment"""
        assessment = Assessment(
            interview_id=interview_id,
            overall_score=overall_score,
            hard_skills_score=hard_skills_score,
            soft_skills_score=soft_skills_score,
            communication_score=communication_score,
            technical_score=technical_score,
            proctoring_risk_score=proctoring_risk_score,
            recommendation=recommendation,
            evidence_clips=evidence_clips,
            summary=summary,
            reviewer_notes=reviewer_notes,
            reviewed_by=reviewed_by
        )
        self.db.add(assessment)
        self.db.commit()
        self.db.refresh(assessment)
        return assessment
    
    def get_assessment_by_interview(self, interview_id: str) -> Optional[Assessment]:
        """Get assessment for an interview"""
        return self.db.query(Assessment).filter(Assessment.interview_id == interview_id).first()
    
    # Utility methods
    def get_or_create_default_organization(self) -> Organization:
        """Get or create a default organization for testing"""
        org = self.db.query(Organization).filter(Organization.name == "SkillScreen Demo").first()
        if not org:
            org = self.create_organization(
                name="SkillScreen Demo",
                domain="skillscreen.demo",
                settings={"demo": True}
            )
        return org
    
    def get_or_create_demo_user(self, email: str = "demo@skillscreen.com") -> User:
        """Get or create a demo user"""
        user = self.get_user_by_email(email)
        if not user:
            org = self.get_or_create_default_organization()
            user = self.create_user(
                organization_id=str(org.id),
                email=email,
                first_name="Demo",
                last_name="User",
                role=UserRole.CANDIDATE
            )
        return user
    
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
        analysis = AIAnalysis(
            interview_id=interview_id,
            session_id=session_id,
            analysis_type=analysis_type,
            service_name=service_name,
            raw_results=raw_results,
            confidence_score=confidence_score,
            processing_time=processing_time,
            version=version
        )
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis
    
    def get_ai_analysis_by_interview(self, interview_id: str) -> List[AIAnalysis]:
        """Get all AI analysis records for an interview"""
        return self.db.query(AIAnalysis).filter(AIAnalysis.interview_id == interview_id).order_by(AIAnalysis.created_at).all()
    
    def get_ai_analysis_by_session(self, session_id: str) -> List[AIAnalysis]:
        """Get all AI analysis records for a session"""
        return self.db.query(AIAnalysis).filter(AIAnalysis.session_id == session_id).order_by(AIAnalysis.created_at).all()
    
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
        candidate = Candidate(
            organization_id=organization_id,
            full_name=full_name,
            email=email,
            phone=phone,
            location=location,
            resume_url=resume_url,
            skills=skills or [],
            experience=experience or {},
            education=education or {},
            projects=projects or []
        )
        self.db.add(candidate)
        self.db.commit()
        self.db.refresh(candidate)
        return candidate
    
    def get_candidate(self, candidate_id: str) -> Optional[Candidate]:
        """Get candidate by ID"""
        return self.db.query(Candidate).filter(Candidate.id == candidate_id).first()
    
    def get_candidate_by_email(self, email: str) -> Optional[Candidate]:
        """Get candidate by email"""
        return self.db.query(Candidate).filter(Candidate.email == email).first()
    
    def get_candidates_by_organization(self, organization_id: str) -> List[Candidate]:
        """Get all candidates for an organization"""
        return self.db.query(Candidate).filter(Candidate.organization_id == organization_id).order_by(Candidate.created_at.desc()).all()
    
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
        candidate = self.db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if candidate:
            if full_name is not None:
                candidate.full_name = full_name
            if email is not None:
                candidate.email = email
            if phone is not None:
                candidate.phone = phone
            if location is not None:
                candidate.location = location
            if resume_url is not None:
                candidate.resume_url = resume_url
            if skills is not None:
                candidate.skills = skills
            if experience is not None:
                candidate.experience = experience
            if education is not None:
                candidate.education = education
            if projects is not None:
                candidate.projects = projects
            
            self.db.commit()
            self.db.refresh(candidate)
        return candidate


