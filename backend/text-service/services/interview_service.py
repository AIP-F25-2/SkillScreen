"""
Interview service for orchestrating the complete interview process
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import uuid
import json
import asyncio
import logging

from database.models import (
    Interview, InterviewSession, Response,
    Candidate, JobPosition, AuditLog, Assessment, InterviewStatus
)
from services.database_service import InterviewDataService
from services.nlp_service import NLPService
from services.anti_cheating_service import AntiCheatingService
from services.rag_service import RAGExplainabilityService
from services.llm_service import llm_service
from services.behavioral_analysis_service import behavioral_analysis_service
from services.bias_detection_service import bias_detection_service
from services.quality_prediction_service import quality_prediction_service
from utils.logger import log_info, log_error, log_warning

class InterviewService:
    """Orchestrates the complete interview process"""
    
    def __init__(self):
        self.nlp_service = NLPService()
        self.anti_cheating_service = AntiCheatingService()
        self.rag_service = RAGExplainabilityService()
        self.behavioral_analysis_service = behavioral_analysis_service
        self.bias_detection_service = bias_detection_service
        self.quality_prediction_service = quality_prediction_service
        
        # Interview configuration
        self.question_templates = {
            'general': [
                "Tell me about yourself and your professional background.",
                "What are your key strengths and how do they apply to this role?",
                "Describe a challenging situation you faced and how you handled it.",
                "What motivates you in your work and career?",
                "Tell me about a time when you had to work collaboratively in a team."
            ],
            'technical': [
                "Walk me through your technical experience and the technologies you've worked with.",
                "Describe a complex technical project you've worked on recently.",
                "How do you approach debugging and troubleshooting technical issues?",
                "What development tools and methodologies do you prefer and why?",
                "Tell me about a time when you had to learn a new technology quickly."
            ],
            'theoretical': [
                "What are the best practices you follow in your field?",
                "How do you ensure code quality and maintainability in your projects?",
                "Explain your approach to system design and architecture decisions.",
                "What industry trends do you think will shape the future of this field?",
                "How do you balance performance, scalability, and maintainability in your work?"
            ]
        }
    
    async def generate_initial_question(
        self,
        candidate: Candidate,
        job: JobPosition,
        interview_type: str,
        db
    ) -> Dict:
        """Generate the initial interview question"""
        try:
            # Create context for question generation
            context = {
                'candidate_name': getattr(candidate, 'full_name', None) or getattr(candidate, 'name', 'Candidate'),
                'candidate_skills': getattr(candidate, 'skills', []) or [],
                'candidate_experience': getattr(candidate, 'experience', {}).get('years', 0) if isinstance(getattr(candidate, 'experience', None), dict) else 0,
                'job_title': job.title,
                'job_company': getattr(job, 'company', 'Company'),
                'job_skills': getattr(job, 'required_skills', []) or [],
                'job_level': getattr(job, 'experience_level', 'Mid-level') or 'Mid-level'
            }
            
            # Generate personalized question
            question_text = await self._generate_personalized_question(
                'general', context, interview_type
            )
            
            # Question will be stored in InterviewSession when response is submitted
            # No separate InterviewQuestion model exists
            
            return {
                'id': str(uuid.uuid4()),
                'question_index': 0,
                'question_text': question_text,
                'question_type': 'general',
                'difficulty': 'medium',
                'round_number': 1,
                'context': context,
                'asked_at': datetime.now(timezone.utc)
            }
            
        except Exception as e:
            log_error(f"Error generating initial question: {e}")
            return {
                'id': str(uuid.uuid4()),
                'question_index': 0,
                'question_text': "Tell me about yourself and your professional background.",
                'question_type': 'general',
                'difficulty': 'medium',
                'round_number': 1,
                'context': {},
                'asked_at': datetime.now(timezone.utc)
            }
    
    async def generate_next_question(
        self,
        interview_id: str,
        db
    ) -> Dict:
        """Generate the next question based on interview progress"""
        try:
            # Support both database and in-memory storage
            from in_memory_storage import get_interview_by_session, get_questions, get_candidate, get_job
            
            # Try in-memory storage first
            interview_data = get_interview_by_session(interview_id)
            if interview_data:
                # In-memory storage path
                previous_questions = get_questions(interview_id)
                current_question_index = len(previous_questions)
                max_questions = interview_data.get("max_questions", 15)
                
                # Check if we're in the last 1-2 questions - generate coding question
                questions_remaining = max_questions - current_question_index
                if questions_remaining <= 2 and questions_remaining > 0:
                    # Create mock Interview object for _generate_coding_question
                    class MockInterview:
                        def __init__(self, data):
                            self.id = data["id"]
                            self.settings = data.get("settings", {})
                            self.candidate_id = data.get("candidate_id")
                            self.job_position_id = data.get("job_id")
                    
                    mock_interview = MockInterview(interview_data)
                    candidate_data = get_candidate(interview_data["candidate_id"])
                    job_data = get_job(interview_data["job_id"])
                    
                    class MockCandidate:
                        def __init__(self, data):
                            self.id = data["id"]
                            self.full_name = data.get("name", "Unknown")
                            self.skills = data.get("skills", [])
                            self.experience = {"years": data.get("experience_years", 0.0)}
                    
                    class MockJob:
                        def __init__(self, data):
                            self.id = data["id"]
                            self.title = data.get("title", "")
                            self.required_skills = data.get("required_skills", [])
                            self.experience_level = data.get("experience_level", "Mid-level")
                    
                    mock_candidate = MockCandidate(candidate_data)
                    mock_job = MockJob(job_data)
                    
                    # Generate coding question
                    coding_result = await self._generate_coding_question_in_memory(
                        mock_interview, mock_candidate, mock_job, current_question_index
                    )
                    return coding_result
                
                # Regular question generation for in-memory
                question_type, round_number = self._determine_question_type(current_question_index)
                
                # Get previous responses for context
                from in_memory_storage import get_responses
                previous_responses = get_responses(interview_id)
                previous_responses_text = [r.get("response_text", "") for r in previous_responses]
                
                context = {
                    'candidate_name': candidate_data.get("name", "Candidate"),
                    'candidate_skills': candidate_data.get("skills", []),
                    'candidate_experience': candidate_data.get("experience_years", 0),
                    'candidate_resume': candidate_data.get("raw_text", ""),  # Include resume text
                    'job_title': job_data.get("title", ""),
                    'job_company': job_data.get("company", ""),
                    'job_description': job_data.get("description", ""),  # Include job description
                    'job_skills': job_data.get("required_skills", []),
                    'job_level': job_data.get("experience_level", "Mid-level"),
                    'previous_questions': [q.get("question_text", "") for q in previous_questions],
                    'previous_responses': previous_responses_text,  # Include previous responses for dynamic generation
                    'current_round': round_number
                }
                
                interview_type = interview_data.get("settings", {}).get("interview_type", "mixed")
                question_text = await self._generate_personalized_question(
                    question_type, context, interview_type
                )
                
                return {
                    'id': str(uuid.uuid4()),
                    'question_index': current_question_index,
                    'question_text': question_text,
                    'question_type': question_type,
                    'difficulty': 'medium',
                    'round_number': round_number,
                    'is_coding_question': False,
                    'asked_at': datetime.now(timezone.utc)
                }
            
            # Database path (original logic)
            interview = db.query(Interview).filter(Interview.id == interview_id).first()
            if not interview:
                raise ValueError(f"Interview {interview_id} not found")
            
            # Get previous questions from interview sessions
            previous_sessions = db.query(InterviewSession).filter(
                InterviewSession.interview_id == interview_id
            ).order_by(InterviewSession.created_at).all()
            previous_questions = [s.question_text for s in previous_sessions if s.question_text]
            
            # Determine question type based on progress
            current_question_index = len(previous_questions)
            
            # Get max_questions from interview settings or default to 12
            max_questions = interview.settings.get('max_questions', 12) if interview.settings else 12
            
            # Check if we're in the last 1-2 questions - generate coding question
            questions_remaining = max_questions - current_question_index
            if questions_remaining <= 2 and questions_remaining > 0:
                # Generate coding question for last 1-2 questions
                return await self._generate_coding_question(interview, current_question_index, db)
            
            question_type, round_number = self._determine_question_type(current_question_index)
            
            # Get candidate and job context
            # interview.candidate_id is a User ID, get Candidate from settings or User
            candidate = None
            if interview.settings and interview.settings.get('candidate_record_id'):
                candidate_id = interview.settings.get('candidate_record_id')
                candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            
            # If not found in settings, try to get from User email
            if not candidate:
                from database.models import User
                user = db.query(User).filter(User.id == interview.candidate_id).first()
                if user:
                    candidate = db.query(Candidate).filter(Candidate.email == user.email).first()
            
            job = db.query(JobPosition).filter(JobPosition.id == interview.job_position_id).first()
            
            if not candidate or not job:
                raise ValueError("Candidate or job not found")
            
            # Create context for question generation
            context = {
                'candidate_name': getattr(candidate, 'full_name', None) or getattr(candidate, 'name', 'Candidate'),
                'candidate_skills': getattr(candidate, 'skills', []) or [],
                'candidate_experience': getattr(candidate, 'experience', {}).get('years', 0) if isinstance(getattr(candidate, 'experience', None), dict) else 0,
                'job_title': job.title,
                'job_company': getattr(job, 'company', 'Company'),
                'job_skills': getattr(job, 'required_skills', []) or [],
                'job_level': getattr(job, 'experience_level', 'Mid-level') or 'Mid-level',
                'previous_questions': previous_questions,
                'current_round': round_number
            }
            
            # Generate personalized question
            # Get interview type from settings or default
            interview_type = interview.settings.get('interview_type', 'mixed') if interview.settings else 'mixed'
            question_text = await self._generate_personalized_question(
                question_type, context, interview_type
            )
            
            # Create question record
            # Question will be stored in InterviewSession when response is submitted
            # No separate InterviewQuestion model exists
            
            return {
                'id': str(uuid.uuid4()),
                'question_index': current_question_index,
                'question_text': question_text,
                'question_type': question_type,
                'difficulty': 'medium',
                'round_number': round_number,
                'context': context,
                'asked_at': datetime.now(timezone.utc)
            }
            
        except Exception as e:
            log_error(f"Error generating next question: {e}")
            # Return fallback question
            return {
                'id': str(uuid.uuid4()),
                'question_index': len(previous_questions) if 'previous_questions' in locals() else 0,
                'question_text': "Can you tell me more about your experience in this field?",
                'question_type': 'general',
                'difficulty': 'medium',
                'round_number': 1,
                'context': {},
                'asked_at': datetime.now(timezone.utc)
            }
    
    async def generate_interview_summary(
        self,
        interview_id: str,
        db
    ) -> Dict:
        """Generate comprehensive interview summary"""
        try:
            # Get interview data
            interview = db.query(Interview).filter(Interview.id == interview_id).first()
            if not interview:
                raise ValueError(f"Interview {interview_id} not found")
            
            # Get candidate from settings (interview.candidate_id is User ID)
            candidate = None
            if interview.settings and interview.settings.get('candidate_record_id'):
                candidate_id = interview.settings.get('candidate_record_id')
                candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            
            # If not found in settings, try to get from User email
            if not candidate:
                from database.models import User
                user = db.query(User).filter(User.id == interview.candidate_id).first()
                if user:
                    candidate = db.query(Candidate).filter(Candidate.email == user.email).first()
            
            job = db.query(JobPosition).filter(JobPosition.id == interview.job_position_id).first()
            responses = db.query(Response).filter(
                Response.interview_id == interview_id
            ).order_by(Response.created_at).all()
            
            if not candidate or not job:
                raise ValueError("Candidate or job not found")
            
            # Calculate overall metrics
            total_responses = len(responses)
            if total_responses > 0:
                # Get scores from Score model
                from database.models import Score
                response_ids = [str(r.id) for r in responses]
                scores = db.query(Score).filter(Score.response_id.in_(response_ids)).all()
                score_map = {str(s.response_id): float(s.auto_score) if s.auto_score else 0.0 for s in scores}
                
                overall_score = sum(score_map.get(str(r.id), 0.0) for r in responses) / total_responses if total_responses > 0 else 0.0
                avg_response_length = sum(len(r.response_text or '') for r in responses) / total_responses
            else:
                overall_score = 0.0
                avg_response_length = 0.0
            
            # Analyze response patterns - these would need to be stored separately or calculated
            duplicate_responses = 0  # Would need to be calculated from response similarity
            off_topic_responses = 0  # Would need to be calculated from NLP analysis
            
            # Generate detailed assessments
            technical_assessment = await self._generate_technical_assessment(responses, job, db)
            communication_assessment = await self._generate_communication_assessment(responses, db)
            cultural_fit_assessment = await self._generate_cultural_fit_assessment(responses, candidate, job, db)
            
            # Generate executive summary
            executive_summary = await self._generate_executive_summary(
                candidate, job, overall_score, total_responses, duplicate_responses, off_topic_responses
            )
            
            # Determine recommendation
            recommendation, recommendation_reason = await self._determine_recommendation(
                overall_score, duplicate_responses, off_topic_responses, total_responses
            )
            
            # Generate strengths and weaknesses
            strengths, weaknesses = await self._generate_strengths_weaknesses(responses, db)
            
            # Generate improvement tips
            improvement_tips = await self._generate_improvement_tips(responses, job, db)
            
            # Create summary data
            summary_data = {
                'executive_summary': executive_summary,
                'overall_score': round(overall_score, 1),
                'recommendation': recommendation,
                'recommendation_reason': recommendation_reason,
                'technical_assessment': technical_assessment,
                'communication_assessment': communication_assessment,
                'cultural_fit': cultural_fit_assessment,
                'strengths': strengths,
                'areas_for_improvement': weaknesses,
                'key_highlights': await self._generate_key_highlights(responses, db),
                'red_flags': await self._generate_red_flags(responses, duplicate_responses, off_topic_responses),
                'improvement_tips': improvement_tips,
                'next_steps': await self._generate_next_steps(recommendation, overall_score),
                'interviewer_notes': await self._generate_interviewer_notes(
                    candidate, job, overall_score, total_responses, duplicate_responses, off_topic_responses
                )
            }
            
            # Save summary to database using Assessment model
            from database.models import Assessment
            assessment = Assessment(
                interview_id=interview_id,
                overall_score=overall_score,
                technical_score=technical_assessment['score'],
                communication_score=communication_assessment['score'],
                soft_skills_score=cultural_fit_assessment['score'],
                recommendation=recommendation,
                summary=executive_summary
            )
            
            db.add(assessment)
            
            # Update interview with final score
            interview.status = InterviewStatus.COMPLETED
            interview.completed_at = datetime.now(timezone.utc)
            
            db.commit()
            
            log_info(f"Generated interview summary for {interview_id}")
            
            # Store the summary in ai_analysis table
            await self._store_interview_summary_analysis(
                interview_id=interview_id,
                summary_data=summary_data,
                db=db
            )
            
            return summary_data
            
        except Exception as e:
            log_error(f"Error generating interview summary: {e}")
            return self._fallback_summary()
    
    async def _store_interview_summary_analysis(
        self,
        interview_id: str,
        summary_data: Dict,
        db
    ) -> None:
        """Store the final interview summary in ai_analysis table"""
        try:
            import time
            start_time = time.time()
            
            # Initialize database service if not provided
            if db is None:
                from database.database import db_manager
                db = db_manager.get_session_sync()
                should_close = True
            else:
                should_close = False
            
            db_service = InterviewDataService(db)
            
            # Prepare raw_results with the complete summary data
            raw_results = {
                'interview_summary': summary_data,  # Full summary from generate_interview_summary
                'summary_type': 'final_assessment',
                'metadata': {
                    'interview_id': interview_id,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'analysis_version': 'v1.0'
                }
            }
            
            # Calculate a confidence score based on the summary
            # Use overall_score from summary (already in 1-10 range if applicable)
            overall_score = summary_data.get('overall_score', 5.0)
            confidence_score = float(overall_score) if overall_score else 5.0
            
            # Ensure confidence score is in 1-10 range
            if confidence_score < 1.0:
                confidence_score = 1.0
            if confidence_score > 10.0:
                confidence_score = 10.0
            
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Store in ai_analysis table
            ai_analysis = db_service.create_ai_analysis(
                interview_id=interview_id,
                session_id=None,  # Summary is interview-level, not session-level
                analysis_type='interview_summary',
                service_name='text-service',
                raw_results=raw_results,
                confidence_score=confidence_score,
                processing_time=processing_time_ms,
                version='v1.0'
            )
            
            if should_close:
                db.close()
            
            log_info(f"[OK] Stored interview summary analysis for interview {interview_id}")
            
        except Exception as e:
            log_error(f"Error storing interview summary analysis: {e}")
            # Don't raise - this is supplementary data
    
    async def generate_pdf_report(
        self,
        interview_id: str,
        db
    ) -> str:
        """Generate PDF report for interview"""
        try:
            # This would integrate with the existing PDF generation logic
            # For now, return a placeholder
            return f"reports/interview_{interview_id}_report.pdf"
            
        except Exception as e:
            log_error(f"Error generating PDF report: {e}")
            raise
    
    def _determine_question_type(self, question_index: int) -> tuple:
        """Determine question type and round based on index"""
        if question_index < 5:
            return 'general', 1
        elif question_index < 10:
            return 'technical', 2
        else:
            return 'theoretical', 3
    
    async def _generate_coding_question_in_memory(
        self,
        interview,
        candidate,
        job,
        current_question_index: int
    ) -> Dict:
        """Generate coding question for in-memory storage"""
        try:
            from services.coding_question_service import coding_question_service
            
            # Determine difficulty
            difficulty = 'medium'
            job_level = getattr(job, 'experience_level', 'Mid-level') or 'Mid-level'
            candidate_exp = getattr(candidate, 'experience', {}).get('years', 0) if isinstance(getattr(candidate, 'experience', None), dict) else 0
            
            if 'senior' in job_level.lower() or 'lead' in job_level.lower() or candidate_exp >= 5:
                difficulty = 'hard'
            elif 'entry' in job_level.lower() or candidate_exp < 2:
                difficulty = 'easy'
            
            # Generate coding question
            coding_question_data = await coding_question_service.generate_coding_question(
                interview_id=str(interview.id),
                job=job,
                candidate=candidate,
                difficulty=difficulty,
                db=None  # No database for in-memory
            )
            
            # Format question text
            question_text = f"""💻 **Coding Challenge**

**Problem:** {coding_question_data.get('title', 'Coding Challenge')}

**Description:**
{coding_question_data.get('description', 'Solve the given coding problem.')}

**Difficulty:** {coding_question_data.get('difficulty', 'medium').title()}
**Time Limit:** {coding_question_data.get('time_limit_minutes', 30)} minutes

**Topics:** {', '.join(coding_question_data.get('topics', []))}

**Examples:**
{chr(10).join([f"Input: {ex.get('input', '')}{chr(10)}Output: {ex.get('output', '')}" for ex in coding_question_data.get('examples', [])[:2]])}

Please write your solution in the code editor. You can choose from Python, JavaScript, Java, C++, or SQL.

**Coding Session ID:** {coding_question_data.get('session_id', '')}
"""
            
            log_info(f"[OK] Generated coding question (in-memory) for question {current_question_index + 1}")
            
            return {
                'id': str(uuid.uuid4()),
                'question_index': current_question_index,
                'question_text': question_text,
                'question_type': 'coding',
                'difficulty': difficulty,
                'round_number': 3,
                'is_coding_question': True,
                'coding_session_id': coding_question_data.get('session_id'),
                'coding_question_id': coding_question_data.get('question_id'),
                'coding_data': coding_question_data,
                'asked_at': datetime.now(timezone.utc)
            }
            
        except Exception as e:
            log_error(f"Error generating coding question (in-memory): {e}")
            return {
                'id': str(uuid.uuid4()),
                'question_index': current_question_index,
                'question_text': "Can you walk me through a technical problem you've solved recently?",
                'question_type': 'technical',
                'difficulty': 'medium',
                'round_number': 3,
                'is_coding_question': False,
                'asked_at': datetime.now(timezone.utc)
            }
    
    async def _generate_coding_question(
        self,
        interview: Interview,
        current_question_index: int,
        db
    ) -> Dict:
        """Generate a coding question for the last 1-2 questions"""
        try:
            from services.coding_question_service import coding_question_service
            
            # Get candidate and job
            candidate = None
            if interview.settings and interview.settings.get('candidate_record_id'):
                candidate_id = interview.settings.get('candidate_record_id')
                candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            
            if not candidate:
                from database.models import User
                user = db.query(User).filter(User.id == interview.candidate_id).first()
                if user:
                    candidate = db.query(Candidate).filter(Candidate.email == user.email).first()
            
            job = db.query(JobPosition).filter(JobPosition.id == interview.job_position_id).first()
            
            if not candidate or not job:
                raise ValueError("Candidate or job not found")
            
            # Determine difficulty based on job level and candidate experience
            difficulty = 'medium'  # Default
            job_level = getattr(job, 'experience_level', 'Mid-level') or 'Mid-level'
            candidate_exp = getattr(candidate, 'experience', {}).get('years', 0) if isinstance(getattr(candidate, 'experience', None), dict) else 0
            
            if 'senior' in job_level.lower() or 'lead' in job_level.lower() or candidate_exp >= 5:
                difficulty = 'hard'
            elif 'entry' in job_level.lower() or candidate_exp < 2:
                difficulty = 'easy'
            
            # Generate coding question using coding_question_service
            coding_question_data = await coding_question_service.generate_coding_question(
                interview_id=str(interview.id),
                job=job,
                candidate=candidate,
                difficulty=difficulty,
                db=db
            )
            
            # Format as a question response that can be displayed in chat
            question_text = f"""💻 **Coding Challenge**

**Problem:** {coding_question_data.get('title', 'Coding Challenge')}

**Description:**
{coding_question_data.get('description', 'Solve the given coding problem.')}

**Difficulty:** {coding_question_data.get('difficulty', 'medium').title()}
**Time Limit:** {coding_question_data.get('time_limit_minutes', 30)} minutes

**Topics:** {', '.join(coding_question_data.get('topics', []))}

**Examples:**
{chr(10).join([f"Input: {ex.get('input', '')}{chr(10)}Output: {ex.get('output', '')}" for ex in coding_question_data.get('examples', [])[:2]])}

Please write your solution in the code editor. You can choose from Python, JavaScript, Java, C++, or SQL.

**Coding Session ID:** {coding_question_data.get('session_id', '')}
"""
            
            log_info(f"[OK] Generated coding question for interview {interview.id} (question {current_question_index + 1})")
            
            return {
                'id': str(uuid.uuid4()),
                'question_index': current_question_index,
                'question_text': question_text,
                'question_type': 'coding',
                'difficulty': difficulty,
                'round_number': 3,  # Final round
                'is_coding_question': True,
                'coding_session_id': coding_question_data.get('session_id'),
                'coding_question_id': coding_question_data.get('question_id'),
                'coding_data': coding_question_data,  # Include full coding question data
                'asked_at': datetime.now(timezone.utc)
            }
            
        except Exception as e:
            log_error(f"Error generating coding question: {e}")
            # Fallback to regular technical question
            return {
                'id': str(uuid.uuid4()),
                'question_index': current_question_index,
                'question_text': "Can you walk me through a technical problem you've solved recently?",
                'question_type': 'technical',
                'difficulty': 'medium',
                'round_number': 3,
                'is_coding_question': False,
                'asked_at': datetime.now(timezone.utc)
            }
    
    async def _generate_personalized_question(
        self,
        question_type: str,
        context: Dict,
        interview_type: str
    ) -> str:
        """Generate personalized question using LLM service with previous responses"""
        try:
            # Prepare candidate context
            candidate_context = {
                'name': context.get('candidate_name', 'Candidate'),
                'skills': context.get('candidate_skills', []),
                'experience_years': context.get('candidate_experience', 0),
                'resume_text': context.get('candidate_resume', '')  # Include full resume text
            }
            
            # Prepare job context
            job_context = {
                'title': context.get('job_title', 'Position'),
                'company': context.get('job_company', 'Company'),
                'description': context.get('job_description', ''),  # Include full job description
                'required_skills': context.get('job_skills', []),
                'experience_level': context.get('job_level', 'mid')
            }
            
            # Get previous questions AND responses for dynamic generation
            previous_questions = context.get('previous_questions', [])
            previous_responses = context.get('previous_responses', [])  # Include previous responses
            question_number = context.get('current_round', 1)
            
            # Generate question using LLM service with previous responses
            # The LLM service should use Gemini to generate questions based on:
            # 1. Resume content
            # 2. Job description
            # 3. Previous questions asked
            # 4. Previous responses given (to avoid repetition and build on answers)
            question = await llm_service.generate_interview_question(
                question_type=question_type,
                candidate_context=candidate_context,
                job_context=job_context,
                previous_questions=previous_questions,
                previous_responses=previous_responses,  # Pass previous responses
                question_number=question_number
            )
            
            log_info(f"[OK] Generated personalized {question_type} question using LLM with context")
            return question
            
        except Exception as e:
            log_error(f"Error generating personalized question: {e}")
            import traceback
            log_error(f"Traceback: {traceback.format_exc()}")
            # Fallback to template-based approach
            return self._get_template_question(question_type, context)
    
    def _get_template_question(self, question_type: str, context: Dict) -> str:
        """Fallback template-based question generation"""
        templates = self.question_templates.get(question_type, self.question_templates['general'])
        question_index = context.get('current_round', 1) - 1
        
        if question_index < len(templates):
            base_question = templates[question_index]
        else:
            base_question = templates[0]
        
        # Personalize the question
        personalized_question = base_question
        
        # Add job-specific elements
        if context.get('job_skills'):
            skills_mention = f" particularly with {', '.join(context['job_skills'][:2])}"
            personalized_question = personalized_question.replace(
                "in this field", f"in {context.get('job_title', 'this role')}{skills_mention}"
            )
        
        return personalized_question
    
    def _get_response_scores(self, db, responses: List[Response]) -> Dict:
        """Helper to get scores for responses from Score model"""
        from database.models import Score
        response_ids = [str(r.id) for r in responses]
        scores = db.query(Score).filter(Score.response_id.in_(response_ids)).all()
        
        score_map = {}
        for s in scores:
            rid = str(s.response_id)
            if rid not in score_map:
                score_map[rid] = {}
            score_map[rid][s.dimension.value if hasattr(s.dimension, 'value') else str(s.dimension)] = float(s.auto_score) if s.auto_score else 0.0
        
        return score_map
    
    async def _generate_technical_assessment(
        self,
        responses: List[Response],
        job: JobPosition,
        db=None
    ) -> Dict:
        """Generate technical assessment"""
        try:
            if not responses:
                return {
                    'score': 0.0,
                    'summary': 'No technical responses to evaluate'
                }
            
            # Calculate technical score from Score model
            if db and responses:
                score_map = self._get_response_scores(db, responses)
                technical_scores = []
                for r in responses:
                    rid = str(r.id)
                    if rid in score_map:
                        tech_score = score_map[rid].get('technical_skills', score_map[rid].get('overall', 0.0))
                        if tech_score > 0:
                            technical_scores.append(tech_score)
                avg_technical_score = sum(technical_scores) / len(technical_scores) if technical_scores else 0.0
            else:
                avg_technical_score = 0.0
            
            # Generate summary
            if avg_technical_score >= 8:
                summary = "Demonstrated strong technical knowledge with specific examples and relevant experience"
            elif avg_technical_score >= 6:
                summary = "Showed good technical understanding with some specific examples"
            elif avg_technical_score >= 4:
                summary = "Basic technical knowledge demonstrated but lacks depth and specificity"
            else:
                summary = "Limited technical knowledge shown, significant gaps in required skills"
            
            return {
                'score': round(avg_technical_score, 1),
                'summary': summary
            }
            
        except Exception as e:
            log_warning(f"Error generating technical assessment: {e}")
            return {
                'score': 5.0,
                'summary': 'Technical assessment completed'
            }
    
    async def _generate_communication_assessment(
        self,
        responses: List[Response]
    ) -> Dict:
        """Generate communication assessment"""
        try:
            if not responses:
                return {
                    'score': 0.0,
                    'summary': 'No communication responses to evaluate'
                }
            
            # Calculate communication score from Score model
            if db and responses:
                score_map = self._get_response_scores(db, responses)
                comm_scores = []
                for r in responses:
                    rid = str(r.id)
                    if rid in score_map:
                        comm_score = score_map[rid].get('communication', score_map[rid].get('overall', 0.0))
                        if comm_score > 0:
                            comm_scores.append(comm_score)
                avg_comm_score = sum(comm_scores) / len(comm_scores) if comm_scores else 0.0
            else:
                avg_comm_score = 0.0
            
            # Generate summary
            if avg_comm_score >= 8:
                summary = "Excellent communication skills with clear, structured, and professional responses"
            elif avg_comm_score >= 6:
                summary = "Good communication skills with generally clear and professional responses"
            elif avg_comm_score >= 4:
                summary = "Adequate communication skills but responses could be more structured and clear"
            else:
                summary = "Communication skills need improvement in clarity, structure, and professionalism"
            
            return {
                'score': round(avg_comm_score, 1),
                'summary': summary
            }
            
        except Exception as e:
            log_warning(f"Error generating communication assessment: {e}")
            return {
                'score': 5.0,
                'summary': 'Communication assessment completed'
            }
    
    async def _generate_cultural_fit_assessment(
        self,
        responses: List[Response],
        candidate: Candidate,
        job: JobPosition,
        db=None
    ) -> Dict:
        """Generate cultural fit assessment"""
        try:
            if not responses:
                return {
                    'score': 0.0,
                    'summary': 'No responses to evaluate cultural fit'
                }
            
            # Calculate job fit score from Score model
            if db and responses:
                score_map = self._get_response_scores(db, responses)
                fit_scores = []
                for r in responses:
                    rid = str(r.id)
                    if rid in score_map:
                        fit_score = score_map[rid].get('cultural_fit', score_map[rid].get('overall', 0.0))
                        if fit_score > 0:
                            fit_scores.append(fit_score)
                avg_fit_score = sum(fit_scores) / len(fit_scores) if fit_scores else 0.0
            else:
                avg_fit_score = 0.0
            
            # Generate summary
            if avg_fit_score >= 8:
                summary = "Strong alignment with role requirements and company culture"
            elif avg_fit_score >= 6:
                summary = "Good fit with role requirements and cultural indicators"
            elif avg_fit_score >= 4:
                summary = "Moderate fit with some alignment to role requirements"
            else:
                summary = "Limited fit with role requirements and cultural expectations"
            
            return {
                'score': round(avg_fit_score, 1),
                'summary': summary
            }
            
        except Exception as e:
            log_warning(f"Error generating cultural fit assessment: {e}")
            return {
                'score': 5.0,
                'summary': 'Cultural fit assessment completed'
            }
    
    async def _generate_executive_summary(
        self,
        candidate: Candidate,
        job: JobPosition,
        overall_score: float,
        total_responses: int,
        duplicate_responses: int,
        off_topic_responses: int
    ) -> str:
        """Generate executive summary"""
        try:
            summary_parts = []
            
            # Overall performance
            if overall_score >= 8:
                summary_parts.append(f"{candidate.name} demonstrated exceptional performance throughout the interview")
            elif overall_score >= 6:
                summary_parts.append(f"{candidate.name} showed good performance with solid responses")
            elif overall_score >= 4:
                summary_parts.append(f"{candidate.name} provided adequate responses but showed room for improvement")
            else:
                summary_parts.append(f"{candidate.name} struggled throughout the interview with below-average responses")
            
            # Response quality
            if duplicate_responses > 0:
                summary_parts.append(f"However, {duplicate_responses} duplicate responses were detected, indicating potential issues with engagement")
            
            if off_topic_responses > 0:
                summary_parts.append(f"Additionally, {off_topic_responses} off-topic responses suggest difficulties in understanding questions")
            
            # Job fit
            company = getattr(job, 'company', 'Company')
            summary_parts.append(f"The candidate's responses were evaluated for the {job.title} position at {company}")
            
            return ". ".join(summary_parts) + "."
            
        except Exception as e:
            log_warning(f"Error generating executive summary: {e}")
            return f"Interview completed for {candidate.name} with overall score of {overall_score:.1f}/10"
    
    async def _determine_recommendation(
        self,
        overall_score: float,
        duplicate_responses: int,
        off_topic_responses: int,
        total_responses: int
    ) -> tuple:
        """Determine hiring recommendation"""
        try:
            # Check for disqualifying factors
            if duplicate_responses >= 3 or off_topic_responses >= 3:
                return "Do Not Hire", "Excessive duplicate or off-topic responses indicate lack of engagement"
            
            if total_responses < 5:
                return "Do Not Hire", "Insufficient responses to make an informed decision"
            
            # Score-based recommendation
            if overall_score >= 8.5:
                return "Hire", "Exceptional performance across all evaluation criteria"
            elif overall_score >= 7.0:
                return "Strong Consider", "Strong performance with good demonstration of required skills"
            elif overall_score >= 5.0:
                return "Consider", "Adequate performance with potential for development"
            else:
                return "Do Not Hire", "Below-average performance with significant areas for improvement"
            
        except Exception as e:
            log_warning(f"Error determining recommendation: {e}")
            return "Consider", "Standard evaluation completed"
    
    async def _generate_strengths_weaknesses(
        self,
        responses: List[Response],
        db=None
    ) -> tuple:
        """Generate strengths and weaknesses"""
        try:
            strengths = []
            weaknesses = []
            
            if not responses:
                return strengths, weaknesses
            
            # Get scores from Score model if available
            if db:
                score_map = self._get_response_scores(db, responses)
                high_scores = 0
                low_scores = 0
                technical_scores = []
                comm_scores = []
                
                for r in responses:
                    rid = str(r.id)
                    if rid in score_map:
                        overall = score_map[rid].get('overall', 0.0)
                        if overall >= 7:
                            high_scores += 1
                        if overall <= 4:
                            low_scores += 1
                        
                        tech = score_map[rid].get('technical_skills', 0.0)
                        if tech > 0:
                            technical_scores.append(tech)
                        
                        comm = score_map[rid].get('communication', 0.0)
                        if comm > 0:
                            comm_scores.append(comm)
                
                if high_scores >= len(responses) * 0.6:
                    strengths.append("Consistently high-quality responses")
                
                if low_scores >= len(responses) * 0.4:
                    weaknesses.append("Multiple low-scoring responses")
                
                if technical_scores and sum(technical_scores) / len(technical_scores) >= 7:
                    strengths.append("Strong technical knowledge and experience")
                
                if comm_scores and sum(comm_scores) / len(comm_scores) >= 7:
                    strengths.append("Clear and professional communication")
            
            # Default strengths/weaknesses if none identified
            if not strengths:
                strengths.append("Participated actively in the interview")
            
            if not weaknesses:
                weaknesses.append("Continue developing interview skills")
            
            return strengths, weaknesses
            
        except Exception as e:
            log_warning(f"Error generating strengths/weaknesses: {e}")
            return ["Interview completed"], ["Continue professional development"]
    
    async def _generate_improvement_tips(
        self,
        responses: List[Response],
        job: JobPosition,
        db=None
    ) -> List[str]:
        """Generate improvement tips"""
        try:
            tips = []
            
            # Get scores from Score model if available
            if db and responses:
                score_map = self._get_response_scores(db, responses)
                technical_scores = []
                comm_scores = []
                
                for r in responses:
                    rid = str(r.id)
                    if rid in score_map:
                        tech = score_map[rid].get('technical_skills', 0.0)
                        if tech > 0:
                            technical_scores.append(tech)
                        comm = score_map[rid].get('communication', 0.0)
                        if comm > 0:
                            comm_scores.append(comm)
                
                # Check for technical improvement
                if technical_scores and sum(technical_scores) / len(technical_scores) < 6:
                    tips.append("Provide more specific technical examples and details")
                
                # Check for communication improvement
                if comm_scores and sum(comm_scores) / len(comm_scores) < 6:
                    tips.append("Structure responses more clearly with specific examples")
            
            # General tips
            tips.extend([
                "Use the STAR method (Situation, Task, Action, Result) for behavioral questions",
                "Prepare specific examples that demonstrate your skills and experience",
                "Practice explaining technical concepts in simple terms"
            ])
            
            return tips[:5]  # Limit to 5 tips
            
        except Exception as e:
            log_warning(f"Error generating improvement tips: {e}")
            return [
                "Provide more specific examples from your experience",
                "Structure responses more clearly",
                "Address questions more directly"
            ]
    
    async def _generate_key_highlights(
        self,
        responses: List[Response],
        db=None
    ) -> List[str]:
        """Generate key highlights"""
        try:
            highlights = []
            
            if not responses:
                return highlights
            
            # Get scores from Score model if available
            if db:
                score_map = self._get_response_scores(db, responses)
                high_scoring_count = 0
                has_high_tech = False
                has_high_comm = False
                
                for r in responses:
                    rid = str(r.id)
                    if rid in score_map:
                        overall = score_map[rid].get('overall', 0.0)
                        if overall >= 8:
                            high_scoring_count += 1
                        
                        if score_map[rid].get('technical_skills', 0.0) >= 8:
                            has_high_tech = True
                        
                        if score_map[rid].get('communication', 0.0) >= 8:
                            has_high_comm = True
                
                if high_scoring_count > 0:
                    highlights.append(f"{high_scoring_count} exceptional responses demonstrating strong competency")
                
                if has_high_tech:
                    highlights.append("Demonstrated strong technical knowledge and experience")
                
                if has_high_comm:
                    highlights.append("Excellent communication skills and clarity")
            
            return highlights
            
        except Exception as e:
            log_warning(f"Error generating key highlights: {e}")
            return ["Interview completed successfully"]
    
    async def _generate_red_flags(
        self,
        responses: List[Response],
        duplicate_responses: int,
        off_topic_responses: int
    ) -> List[str]:
        """Generate red flags"""
        try:
            red_flags = []
            
            if duplicate_responses >= 2:
                red_flags.append(f"{duplicate_responses} duplicate responses detected")
            
            if off_topic_responses >= 2:
                red_flags.append(f"{off_topic_responses} off-topic responses")
            
            # Check for consistently low scores
            if responses:
                low_scores = sum(1 for r in responses if r.overall_score and r.overall_score <= 3)
                if low_scores >= len(responses) * 0.5:
                    red_flags.append("Consistently low performance across multiple responses")
            
            return red_flags
            
        except Exception as e:
            log_warning(f"Error generating red flags: {e}")
            return []
    
    async def _generate_next_steps(
        self,
        recommendation: str,
        overall_score: float
    ) -> List[str]:
        """Generate next steps"""
        try:
            next_steps = []
            
            if recommendation == "Hire":
                next_steps.extend([
                    "Proceed with reference checks",
                    "Schedule final interview with hiring manager",
                    "Prepare offer letter and onboarding plan"
                ])
            elif recommendation == "Strong Consider":
                next_steps.extend([
                    "Conduct additional technical assessment",
                    "Schedule follow-up interview",
                    "Check references"
                ])
            elif recommendation == "Consider":
                next_steps.extend([
                    "Review responses in detail",
                    "Consider additional screening",
                    "Evaluate against other candidates"
                ])
            else:  # Do Not Hire
                next_steps.extend([
                    "Document reasons for rejection",
                    "Provide feedback to candidate if requested",
                    "Continue with other candidates"
                ])
            
            return next_steps
            
        except Exception as e:
            log_warning(f"Error generating next steps: {e}")
            return ["Review interview results", "Make hiring decision"]
    
    async def _generate_interviewer_notes(
        self,
        candidate: Candidate,
        job: JobPosition,
        overall_score: float,
        total_responses: int,
        duplicate_responses: int,
        off_topic_responses: int
    ) -> str:
        """Generate interviewer notes"""
        try:
            notes = []
            
            notes.append(f"Interview completed for {candidate.name} for {job.title} position")
            notes.append(f"Overall score: {overall_score:.1f}/10 based on {total_responses} responses")
            
            if duplicate_responses > 0:
                notes.append(f"Note: {duplicate_responses} duplicate responses detected")
            
            if off_topic_responses > 0:
                notes.append(f"Note: {off_topic_responses} off-topic responses")
            
            if overall_score >= 7:
                notes.append("Candidate demonstrated strong competency and should be considered for next round")
            elif overall_score >= 5:
                notes.append("Candidate showed adequate performance but may need additional assessment")
            else:
                notes.append("Candidate struggled with interview questions and may not be suitable for this role")
            
            return ". ".join(notes) + "."
            
        except Exception as e:
            log_warning(f"Error generating interviewer notes: {e}")
            return f"Interview completed for {candidate.name} with score of {overall_score:.1f}/10"
    
    def _fallback_summary(self) -> Dict:
        """Fallback summary when generation fails"""
        return {
            'executive_summary': 'Interview completed successfully',
            'overall_score': 5.0,
            'recommendation': 'Consider',
            'recommendation_reason': 'Standard evaluation completed',
            'technical_assessment': {'score': 5.0, 'summary': 'Assessment completed'},
            'communication_assessment': {'score': 5.0, 'summary': 'Assessment completed'},
            'cultural_fit': {'score': 5.0, 'summary': 'Assessment completed'},
            'strengths': ['Completed interview'],
            'areas_for_improvement': ['Continue professional development'],
            'key_highlights': ['Interview completed'],
            'red_flags': [],
            'improvement_tips': ['Continue professional development'],
            'next_steps': ['Review interview results'],
            'interviewer_notes': 'Interview completed successfully'
        }
    
    async def evaluate_and_store_response_analysis(
        self,
        interview_id: str,
        session_id: str,
        question_text: str,
        response_text: str,
        response_time_seconds: Optional[float] = None,
        question_number: int = 0,
        candidate_context: Optional[Dict] = None,
        job_context: Optional[Dict] = None,
        db = None
    ) -> Dict:
        """
        Comprehensive response evaluation using all ML services and store results in ai_analysis table.
        This method:
        1. Runs behavioral analysis
        2. Runs quality prediction
        3. Runs bias detection (if applicable)
        4. Stores analysis results as SEPARATE records in ai_analysis table
        5. Returns aggregated scores for immediate use
        """
        import time
        start_time = time.time()
        
        try:
            # Initialize database service if not provided
            if db is None:
                from database.database import db_manager
                db = db_manager.get_session_sync()
                should_close = True
            else:
                should_close = False
            
            db_service = InterviewDataService(db)
            
            # Run all ML analyses in parallel
            analysis_tasks = []
            
            # 1. Behavioral Analysis
            analysis_tasks.append(
                self.behavioral_analysis_service.analyze_behavioral_patterns(
                    response_text=response_text,
                    interview_id=interview_id,
                    response_time_seconds=response_time_seconds,
                    question_number=question_number
                )
            )
            
            # 2. Quality Prediction
            analysis_tasks.append(
                self.quality_prediction_service.predict_quality_score(
                    question=question_text,
                    response=response_text,
                    candidate_context=candidate_context,
                    job_context=job_context
                )
            )
            
            # Run analyses
            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            behavioral_analysis = results[0] if not isinstance(results[0], Exception) else {}
            quality_prediction = results[1] if not isinstance(results[1], Exception) else {}
            
            # 3. Bias Detection (run separately as it may need interview-level data)
            bias_analysis = {}
            try:
                # Get previous responses for bias detection
                # Use Response model from database.models
                from database.models import Response
                previous_responses = db.query(Response).filter(
                    Response.interview_id == interview_id
                ).order_by(Response.created_at).all()
                
                if len(previous_responses) >= 2:  # Need at least 2 responses for bias detection
                    # Get scores from Score model if available
                    from database.models import Score
                    response_ids = [str(r.id) for r in previous_responses]
                    scores = db.query(Score).filter(
                        Score.response_id.in_(response_ids)
                    ).all()
                    score_map = {str(s.response_id): float(s.auto_score) if s.auto_score else 5.0 for s in scores}
                    
                    response_texts = [r.response_text for r in previous_responses if r.response_text]
                    response_scores = [score_map.get(str(r.id), 5.0) for r in previous_responses if r.response_text]
                    
                    if len(response_texts) >= 2:
                        bias_analysis = await self.bias_detection_service.detect_bias(
                            interview_id=interview_id,
                            responses=response_texts,
                            scores=response_scores
                        )
            except Exception as e:
                log_warning(f"Bias detection failed: {e}")
            
            # Calculate final confidence score (range: 1-10)
            # Weighted average of quality prediction score and behavioral consistency
            quality_score = quality_prediction.get('predicted_score', 5.0)
            behavioral_consistency = behavioral_analysis.get('consistency_score', 0.5)
            behavioral_engagement = behavioral_analysis.get('engagement_score', 0.5)
            
            # Normalize behavioral scores (0-1) to 1-10 range
            # Convert 0-1 consistency/engagement to 1-10 scale
            consistency_10 = 1.0 + (behavioral_consistency * 9.0)  # 0.5 -> 5.5, 1.0 -> 10.0
            engagement_10 = 1.0 + (behavioral_engagement * 9.0)  # 0.5 -> 5.5, 1.0 -> 10.0
            
            # Ensure quality_score is in 1-10 range
            if quality_score < 1.0:
                quality_score = 1.0
            if quality_score > 10.0:
                quality_score = 10.0
            
            # Calculate weighted final score (all in 1-10 range)
            final_confidence_score = (
                quality_score * 0.6 +  # 60% weight on quality
                consistency_10 * 0.25 +  # 25% weight on consistency
                engagement_10 * 0.15  # 15% weight on engagement
            )
            
            # Ensure score is between 1 and 10
            final_confidence_score = max(1.0, min(10.0, final_confidence_score))
            
            # --- STORE RESULTS AS SEPARATE RECORDS ---
            
            stored_ids = []
            
            # 1. Store Behavioral Analysis
            behavioral_data = {
                'behavior_type': behavioral_analysis.get('behavior_type', 'unknown'),
                'anomaly_score': behavioral_analysis.get('anomaly_score', 0.0),
                'engagement_trend': behavioral_analysis.get('engagement_trend', 'stable'),
                'consistency_score': behavioral_analysis.get('consistency_score', 0.0),
                'behavioral_flags': behavioral_analysis.get('behavioral_flags', []),
                'engagement_score': behavioral_analysis.get('engagement_score', 0.5),
                'metadata': {
                    'response_time_seconds': response_time_seconds,
                    'question_number': question_number
                }
            }
            
            # Calculate specific confidence for behavioral (consistency)
            behavioral_conf = consistency_10
            
            ai_analysis_beh = db_service.create_ai_analysis(
                interview_id=interview_id,
                session_id=session_id,
                analysis_type='behavioral_analysis',
                service_name='behavioral_analysis_service',
                raw_results=behavioral_data,
                confidence_score=float(behavioral_conf),
                processing_time=int((time.time() - start_time) * 1000), # Approx share
                version='v1.0'
            )
            stored_ids.append(str(ai_analysis_beh.id))
            
            # 2. Store Quality Prediction
            quality_data = {
                'predicted_score': quality_prediction.get('predicted_score', 5.0),
                'confidence': quality_prediction.get('confidence', 0.5),
                'feature_importance': quality_prediction.get('feature_importance', {}),
                'model_used': quality_prediction.get('model_used', 'ensemble'),
                'metadata': {
                    'response_length': len(response_text),
                    'question_number': question_number
                }
            }
            
            # Use model confidence if available, else default
            quality_conf = quality_prediction.get('confidence', 0.5) * 10.0 # Scale 0-1 to 1-10
            
            ai_analysis_qual = db_service.create_ai_analysis(
                interview_id=interview_id,
                session_id=session_id,
                analysis_type='quality_prediction',
                service_name='quality_prediction_service',
                raw_results=quality_data,
                confidence_score=float(quality_conf),
                processing_time=int((time.time() - start_time) * 1000),
                version='v1.0'
            )
            stored_ids.append(str(ai_analysis_qual.id))
            
            # 3. Store Bias Detection (if available)
            if bias_analysis:
                bias_data = bias_analysis
                # Bias confidence? Maybe inverse of bias score?
                # For now, use default 5.0 or derived from bias probability
                bias_prob = bias_analysis.get('bias_probability', 0.0)
                bias_conf = (1.0 - bias_prob) * 10.0
                
                ai_analysis_bias = db_service.create_ai_analysis(
                    interview_id=interview_id,
                    session_id=session_id,
                    analysis_type='bias_detection',
                    service_name='bias_detection_service',
                    raw_results=bias_data,
                    confidence_score=float(bias_conf),
                    processing_time=int((time.time() - start_time) * 1000),
                    version='v1.0'
                )
                stored_ids.append(str(ai_analysis_bias.id))
            
            if should_close:
                db.close()
            
            log_info(f"[OK] Stored {len(stored_ids)} AI analysis records for interview {interview_id}, session {session_id}")
            
            # Return aggregated results for API response
            return {
                'analysis_id': stored_ids[0] if stored_ids else None, # Return first ID for compatibility
                'analysis_ids': stored_ids, # Return all IDs
                'confidence_score': final_confidence_score,
                'quality_score': quality_score,
                'behavioral_consistency': behavioral_consistency,
                'behavioral_engagement': behavioral_engagement,
                'processing_time_ms': int((time.time() - start_time) * 1000),
                'analysis_stored': True
            }
            
        except Exception as e:
            log_error(f"Error evaluating and storing response analysis: {e}")
            if should_close and db:
                db.close()
            return {
                'analysis_id': None,
                'confidence_score': 0.5,
                'quality_score': 5.0,
                'behavioral_consistency': 0.5,
                'behavioral_engagement': 0.5,
                'processing_time_ms': int((time.time() - start_time) * 1000),
                'analysis_stored': False,
                'error': str(e)
            }
