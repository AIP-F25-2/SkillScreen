"""
Coding Question Service for SkillScreen
Manages coding questions, integrates with LeetCode, and handles coding sessions
"""

import uuid
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
import logging

from database.models import CodingQuestion, CodingSession, Interview, Candidate, JobPosition, DifficultyLevel
from services.leetcode_service import leetcode_service
from services.code_execution_service import code_execution_service
from utils.logger import log_info, log_error, log_warning

class CodingQuestionService:
    """Service for managing coding questions and sessions"""
    
    def __init__(self):
        # Default time limits for coding questions (in minutes)
        self.time_limits = {
            'easy': 15,      # 15 minutes for easy questions
            'medium': 30,    # 30 minutes for medium questions
            'hard': 45       # 45 minutes for hard questions
        }
        
        log_info("[OK] Coding Question Service initialized")
    
    async def generate_coding_question(
        self,
        interview_id: str,
        job: JobPosition,
        candidate: Candidate,
        difficulty: str = 'medium',
        db = None
    ) -> Dict[str, Any]:
        """Generate a coding question based on job requirements, candidate skills, resume, and job description"""
        try:
            # Get job skills and candidate skills
            job_skills = getattr(job, 'required_skills', getattr(job, 'skills_required', [])) or []
            candidate_skills = getattr(candidate, 'skills', []) or []
            
            # Get job description and candidate resume information
            job_description = getattr(job, 'description', '') or ''
            candidate_experience = getattr(candidate, 'experience', {})
            if isinstance(candidate_experience, dict):
                experience_years = candidate_experience.get('years', 0)
            else:
                experience_years = 0
            
            # Determine question type based on job requirements
            question_type = self._determine_question_type(job_skills)
            
            # Use LLM to generate personalized coding question based on resume and job description
            personalized_question = await self._generate_personalized_coding_question(
                job_skills=job_skills,
                candidate_skills=candidate_skills,
                job_description=job_description,
                candidate_experience_years=experience_years,
                difficulty=difficulty,
                question_type=question_type
            )
            
            # Fetch question from LeetCode (using web search via LeetCode service)
            leetcode_question = await leetcode_service.get_question_by_requirements(
                job_skills=job_skills,
                candidate_skills=candidate_skills,
                difficulty=difficulty,
                question_type=question_type
            )
            
            # Enhance LeetCode question with personalized context from LLM
            if leetcode_question and personalized_question:
                # Merge LLM-generated context with LeetCode question
                leetcode_question['personalized_context'] = personalized_question
                leetcode_question['description'] = f"{personalized_question}\n\n{leetcode_question.get('description', '')}"
            
            if not leetcode_question:
                log_warning("Failed to fetch LeetCode question, using fallback")
                leetcode_question = await leetcode_service._get_fallback_question(difficulty, question_type)
            
            # Get organization from interview
            interview = db.query(Interview).filter(Interview.id == interview_id).first()
            if not interview:
                raise ValueError(f"Interview {interview_id} not found")
            
            # Create or get coding question in database
            coding_question = self._create_or_get_coding_question(
                leetcode_question=leetcode_question,
                organization_id=str(interview.organization_id),
                db=db
            )
            
            # Create coding session
            coding_session = self._create_coding_session(
                interview_id=interview_id,
                question_id=str(coding_question.id),
                db=db
            )
            
            # Format response
            return {
                'session_id': str(coding_session.id),
                'question_id': str(coding_question.id),
                'title': coding_question.title,
                'description': coding_question.description,
                'difficulty': coding_question.difficulty.value if coding_question.difficulty else difficulty,
                'code_templates': coding_question.starter_code or leetcode_question.get('code_templates', {}),
                'test_cases': coding_question.test_cases or [],
                'examples': leetcode_question.get('examples', []),
                'constraints': leetcode_question.get('constraints', []),
                'topics': coding_question.tags or leetcode_question.get('topics', []),
                'time_limit_minutes': self.time_limits.get(difficulty, 30),
                'started_at': coding_session.started_at.isoformat() if coding_session.started_at else datetime.now(timezone.utc).isoformat(),
                'leetcode_url': leetcode_question.get('url', '')
            }
            
        except Exception as e:
            log_error(f"Error generating coding question: {e}")
            raise
    
    def _create_or_get_coding_question(
        self,
        leetcode_question: Dict,
        organization_id: str,
        db
    ) -> CodingQuestion:
        """Create or get existing coding question from database"""
        try:
            # Check if question already exists (by LeetCode ID or title)
            existing = db.query(CodingQuestion).filter(
                CodingQuestion.title == leetcode_question.get('title', '')
            ).first()
            
            if existing:
                return existing
            
            # Create new coding question
            difficulty_enum = DifficultyLevel.MEDIUM
            difficulty_str = leetcode_question.get('difficulty', 'medium').lower()
            if difficulty_str == 'easy':
                difficulty_enum = DifficultyLevel.EASY
            elif difficulty_str == 'hard':
                difficulty_enum = DifficultyLevel.HARD
            
            coding_question = CodingQuestion(
                id=uuid.uuid4(),
                organization_id=uuid.UUID(organization_id),
                title=leetcode_question.get('title', 'Coding Challenge'),
                description=leetcode_question.get('description', ''),
                difficulty=difficulty_enum,
                languages=list(leetcode_question.get('code_templates', {}).keys()) or ['python', 'javascript', 'java'],
                test_cases=leetcode_question.get('examples', []),
                starter_code=leetcode_question.get('code_templates', {}),
                tags=leetcode_question.get('topics', [])
            )
            
            db.add(coding_question)
            db.commit()
            db.refresh(coding_question)
            
            log_info(f"[OK] Created coding question: {coding_question.title}")
            return coding_question
            
        except Exception as e:
            log_error(f"Error creating coding question: {e}")
            raise
    
    def _create_coding_session(
        self,
        interview_id: str,
        question_id: str,
        db
    ) -> CodingSession:
        """Create a new coding session"""
        try:
            coding_session = CodingSession(
                id=uuid.uuid4(),
                interview_id=uuid.UUID(interview_id),
                question_id=uuid.UUID(question_id),
                started_at=datetime.now(timezone.utc),
                language=None,
                code=None,
                execution_results=None,
                is_correct=None
            )
            
            db.add(coding_session)
            db.commit()
            db.refresh(coding_session)
            
            log_info(f"[OK] Created coding session: {coding_session.id}")
            return coding_session
            
        except Exception as e:
            log_error(f"Error creating coding session: {e}")
            raise
    
    async def submit_code_solution(
        self,
        session_id: str,
        code: str,
        language: str,
        db
    ) -> Dict[str, Any]:
        """Submit code solution for a coding session"""
        try:
            # Get coding session
            coding_session = db.query(CodingSession).filter(CodingSession.id == session_id).first()
            if not coding_session:
                raise ValueError(f"Coding session {session_id} not found")
            
            # Check if time limit exceeded
            if coding_session.started_at:
                elapsed = datetime.now(timezone.utc) - coding_session.started_at
                question = db.query(CodingQuestion).filter(CodingQuestion.id == coding_session.question_id).first()
                difficulty = question.difficulty.value.lower() if question and question.difficulty else 'medium'
                time_limit = timedelta(minutes=self.time_limits.get(difficulty, 30))
                
                if elapsed > time_limit:
                    return {
                        'success': False,
                        'error': 'Time limit exceeded',
                        'elapsed_minutes': elapsed.total_seconds() / 60,
                        'time_limit_minutes': time_limit.total_seconds() / 60
                    }
            
            # Get test cases from question
            question = db.query(CodingQuestion).filter(CodingQuestion.id == coding_session.question_id).first()
            test_cases = question.test_cases if question and question.test_cases else []
            
            # Execute code
            execution_result = await code_execution_service.execute_code(
                code=code,
                language=language,
                test_cases=test_cases,
                timeout=30  # 30 second timeout per execution
            )
            
            # Update coding session
            coding_session.code = code
            coding_session.language = language
            coding_session.execution_results = execution_result
            coding_session.execution_time = int(execution_result.get('execution_time', 0) * 1000)  # Convert to ms
            
            # Check if all test cases passed
            test_results = execution_result.get('test_results', [])
            all_passed = all(t.get('passed', False) for t in test_results) if test_results else False
            coding_session.is_correct = all_passed
            
            coding_session.submitted_at = datetime.now(timezone.utc)
            db.commit()
            
            # Calculate score based on test results
            passed_tests = sum(1 for t in test_results if t.get('passed', False))
            total_tests = len(test_results) if test_results else 1
            score = (passed_tests / total_tests) * 10.0 if total_tests > 0 else 0.0
            
            log_info(f"[OK] Code submitted: {passed_tests}/{total_tests} tests passed")
            
            return {
                'success': True,
                'session_id': str(coding_session.id),
                'execution_result': execution_result,
                'test_results': test_results,
                'passed_tests': passed_tests,
                'total_tests': total_tests,
                'score': round(score, 1),
                'is_correct': all_passed,
                'execution_time_ms': coding_session.execution_time,
                'submitted_at': coding_session.submitted_at.isoformat()
            }
            
        except Exception as e:
            log_error(f"Error submitting code solution: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_coding_session_status( # nosonar
        self,
        session_id: str,
        db
    ) -> Dict[str, Any]:
        """Get status of a coding session"""
        try:
            coding_session = db.query(CodingSession).filter(CodingSession.id == session_id).first()
            if not coding_session:
                raise ValueError(f"Coding session {session_id} not found")
            
            question = db.query(CodingQuestion).filter(CodingQuestion.id == coding_session.question_id).first()
            
            # Calculate remaining time
            remaining_time = None
            if coding_session.started_at and question:
                elapsed = datetime.now(timezone.utc) - coding_session.started_at
                difficulty = question.difficulty.value.lower() if question.difficulty else 'medium'
                time_limit = timedelta(minutes=self.time_limits.get(difficulty, 30))
                remaining = time_limit - elapsed
                remaining_time = max(0, remaining.total_seconds() / 60)  # minutes
            
            return {
                'session_id': str(coding_session.id),
                'question_id': str(coding_session.question_id),
                'question_title': question.title if question else None,
                'language': coding_session.language,
                'has_code': coding_session.code is not None,
                'is_submitted': coding_session.submitted_at is not None,
                'is_correct': coding_session.is_correct,
                'started_at': coding_session.started_at.isoformat() if coding_session.started_at else None,
                'submitted_at': coding_session.submitted_at.isoformat() if coding_session.submitted_at else None,
                'remaining_time_minutes': remaining_time,
                'execution_time_ms': coding_session.execution_time
            }
            
        except Exception as e:
            log_error(f"Error getting coding session status: {e}")
            raise
    
    async def _generate_personalized_coding_question(
        self,
        job_skills: List[str],
        candidate_skills: List[str],
        job_description: str,
        candidate_experience_years: float,
        difficulty: str,
        question_type: str
    ) -> str:
        """Generate personalized coding question context using LLM based on resume and job description"""
        try:
            from services.llm_service import llm_service
            
            # Build prompt for LLM to generate personalized coding question context
            prompt = f"""You are generating a coding interview question for a candidate. Based on the following information, create a personalized context that explains why this coding question is relevant.

JOB REQUIREMENTS:
- Required Skills: {', '.join(job_skills[:10]) if job_skills else 'Various technical skills'}
- Job Description: {job_description[:500] if job_description else 'Technical development role'}
- Difficulty Level: {difficulty}

CANDIDATE BACKGROUND:
- Skills: {', '.join(candidate_skills[:10]) if candidate_skills else 'Technical skills'}
- Experience: {candidate_experience_years} years

QUESTION TYPE: {question_type}

Generate a brief, personalized introduction (2-3 sentences) that:
1. Connects the coding question to the job requirements
2. References the candidate's skills and experience level
3. Explains why this question is relevant for this specific role
4. Makes it feel tailored to this candidate

Return only the personalized context text, no additional formatting."""
            
            # Use LLM to generate personalized context
            if llm_service and llm_service.gemini_model:
                try:
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(
                        None,
                        lambda: llm_service.gemini_model.generate_content(prompt)
                    )
                    if response and response.text:
                        return response.text.strip()
                except Exception as e:
                    log_warning(f"LLM generation failed, using fallback: {e}")
            
            # Fallback personalized context
            return f"Based on your experience with {', '.join(candidate_skills[:3]) if candidate_skills else 'technical skills'} and the requirements for this {difficulty} level position, please solve the following coding challenge."
            
        except Exception as e:
            log_warning(f"Error generating personalized coding question: {e}")
            return f"Please solve the following {difficulty} level coding challenge relevant to this position."
    
    def _determine_question_type(self, job_skills: List[str]) -> str:
        """Determine question type based on job skills"""
        skills_lower = [s.lower() for s in job_skills]
        
        # Algorithm-focused roles
        if any(skill in ['algorithm', 'data structure', 'dsa', 'leetcode'] for skill in skills_lower):
            return 'algorithm'
        
        # System design roles
        if any(skill in ['system design', 'architecture', 'distributed'] for skill in skills_lower):
            return 'system_design'
        
        # Database roles
        if any(skill in ['sql', 'database', 'postgresql', 'mysql'] for skill in skills_lower):
            return 'database'
        
        # Default to algorithm
        return 'algorithm'

# Global instance
coding_question_service = CodingQuestionService()

