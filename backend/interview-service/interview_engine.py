"""
Interview Engine for SkillScreen
Core engine that orchestrates the interview process with sequential questioning
"""

import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid
import os

from resume_parser import ResumeParser, ParsedResume
from job_parser import JobParser, ParsedJobDescription
from llm_integration import GeminiIntegration, InterviewQuestion, InterviewResponse, InterviewSession
from config import config
from logger import logger, log_info, log_error, log_warning, log_debug

@dataclass
class InterviewState:
    """Current state of the interview"""
    session_id: str
    candidate_name: str
    job_title: str
    company: str
    current_question: Optional[InterviewQuestion]
    question_history: List[InterviewQuestion]
    response_history: List[InterviewResponse]
    current_question_index: int
    is_started: bool
    is_completed: bool
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    total_score: float
    context_valid: bool
    off_topic_count: int
    max_off_topic: int = 3

class InterviewEngine:
    """Main interview engine that orchestrates the interview process"""
    
    def __init__(self, gemini_api_key: str = None):
        """Initialize the interview engine"""
        self.resume_parser = ResumeParser()
        self.job_parser = JobParser()
        self.llm_integration = GeminiIntegration(gemini_api_key)
        
        # Interview configuration
        self.max_questions = 10
        self.min_questions = 5
        self.off_topic_threshold = 0.3  # Threshold for off-topic detection
        self.max_off_topic_responses = 3
        
        # Active sessions storage
        self.active_sessions: Dict[str, InterviewState] = {}
        
        # Interview templates
        self.interview_templates = {
            'technical': {
                'focus_areas': ['coding', 'system design', 'algorithms', 'databases'],
                'question_ratio': {'technical': 0.7, 'behavioral': 0.2, 'situational': 0.1}
            },
            'behavioral': {
                'focus_areas': ['leadership', 'teamwork', 'problem solving', 'communication'],
                'question_ratio': {'behavioral': 0.6, 'situational': 0.3, 'technical': 0.1}
            },
            'mixed': {
                'focus_areas': ['technical skills', 'soft skills', 'experience', 'cultural fit'],
                'question_ratio': {'technical': 0.4, 'behavioral': 0.4, 'situational': 0.2}
            }
        }
    
    def start_interview(self, resume_text: str, job_description: str, 
                       interview_type: str = 'mixed') -> str:
        """Start a new interview session"""
        try:
            # Parse resume and job description
            parsed_resume = self.resume_parser.parse_resume(resume_text)
            parsed_job = self.job_parser.parse_job_description(job_description)
            
            # Generate session ID
            session_id = str(uuid.uuid4())
            
            # Generate initial question
            initial_question = self.llm_integration.generate_initial_question(parsed_resume, parsed_job)
            
            # Create interview state
            interview_state = InterviewState(
                session_id=session_id,
                candidate_name=parsed_resume.name,
                job_title=parsed_job.title,
                company=parsed_job.company,
                current_question=initial_question,
                question_history=[initial_question],
                response_history=[],
                current_question_index=0,
                is_started=True,
                is_completed=False,
                start_time=datetime.now(),
                end_time=None,
                total_score=0.0,
                context_valid=True,
                off_topic_count=0
            )
            
            # Store session
            self.active_sessions[session_id] = interview_state
            
            logger.info(f"Started interview session {session_id} for {parsed_resume.name}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error starting interview: {str(e)}")
            raise
    
    def submit_response(self, session_id: str, response: str) -> Dict[str, any]:
        """Submit candidate response and get next question or summary"""
        try:
            if session_id not in self.active_sessions:
                raise ValueError(f"Session {session_id} not found")
            
            interview_state = self.active_sessions[session_id]
            
            if interview_state.is_completed:
                return self._get_interview_summary(session_id)
            
            # Evaluate the response
            current_question = interview_state.current_question
            if not current_question:
                raise ValueError("No current question available")
            
            response_evaluation = self.llm_integration.evaluate_response(
                current_question, response, self._create_session_from_state(interview_state)
            )
            
            # Update interview state
            interview_state.response_history.append(response_evaluation)
            interview_state.current_question_index += 1
            
            # Check for off-topic responses
            if not response_evaluation.is_on_topic:
                interview_state.off_topic_count += 1
                interview_state.context_valid = interview_state.off_topic_count < self.max_off_topic_responses
            
            # Check if interview should continue
            should_continue = self._should_continue_interview(interview_state, response)
            
            if not should_continue or interview_state.current_question_index >= self.max_questions:
                # End interview
                interview_state.is_completed = True
                interview_state.end_time = datetime.now()
                interview_state.current_question = None
                
                return self._get_interview_summary(session_id)
            else:
                # Generate next question
                next_question = self._generate_next_question(interview_state, response)
                
                if next_question:
                    interview_state.current_question = next_question
                    interview_state.question_history.append(next_question)
                else:
                    # No more questions, end interview
                    interview_state.is_completed = True
                    interview_state.end_time = datetime.now()
                    interview_state.current_question = None
                    
                    return self._get_interview_summary(session_id)
            
            # Return current question and evaluation
            return {
                'session_id': session_id,
                'current_question': interview_state.current_question.question if interview_state.current_question else None,
                'question_type': interview_state.current_question.question_type if interview_state.current_question else None,
                'question_context': interview_state.current_question.context if interview_state.current_question else None,
                'response_evaluation': {
                    'relevance_score': response_evaluation.relevance_score,
                    'technical_accuracy': response_evaluation.technical_accuracy,
                    'communication_quality': response_evaluation.communication_quality,
                    'confidence_level': response_evaluation.confidence_level,
                    'strengths': response_evaluation.strengths,
                    'areas_for_improvement': response_evaluation.areas_for_improvement,
                    'is_on_topic': response_evaluation.is_on_topic
                },
                'interview_progress': {
                    'questions_asked': len(interview_state.question_history),
                    'responses_given': len(interview_state.response_history),
                    'off_topic_count': interview_state.off_topic_count,
                    'context_valid': interview_state.context_valid
                },
                'is_completed': interview_state.is_completed
            }
            
        except Exception as e:
            logger.error(f"Error submitting response: {str(e)}")
            raise
    
    def get_current_question(self, session_id: str) -> Optional[Dict[str, any]]:
        """Get the current question for a session"""
        if session_id not in self.active_sessions:
            return None
        
        interview_state = self.active_sessions[session_id]
        
        if not interview_state.current_question:
            return None
        
        return {
            'question': interview_state.current_question.question,
            'question_type': interview_state.current_question.question_type,
            'difficulty': interview_state.current_question.difficulty,
            'expected_skills': interview_state.current_question.expected_skills,
            'context': interview_state.current_question.context,
            'question_index': interview_state.current_question_index
        }
    
    def get_interview_summary(self, session_id: str) -> Dict[str, any]:
        """Get comprehensive interview summary"""
        return self._get_interview_summary(session_id)
    
    def _should_continue_interview(self, interview_state: InterviewState, response: str) -> bool:
        """Determine if interview should continue"""
        # Check if response is too short
        if len(response.strip()) < 20:
            return False
        
        # Check if we've reached max questions
        if interview_state.current_question_index >= self.max_questions:
            return False
        
        # Check if context is still valid
        if not interview_state.context_valid:
            return False
        
        # Check for off-topic responses
        off_topic_indicators = [
            "i don't know", "i can't answer", "not relevant", "off topic",
            "i don't understand", "can you repeat", "what do you mean",
            "i'm not sure", "i don't have experience with that"
        ]
        
        response_lower = response.lower()
        if any(indicator in response_lower for indicator in off_topic_indicators):
            return False
        
        return True
    
    def _generate_next_question(self, interview_state: InterviewState, response: str) -> Optional[InterviewQuestion]:
        """Generate the next question based on interview progress"""
        try:
            # Create session object for LLM integration
            session = self._create_session_from_state(interview_state)
            
            # Generate follow-up question
            next_question = self.llm_integration.generate_follow_up_question(session, response)
            
            if not next_question:
                # Try to generate a different type of question
                next_question = self._generate_alternative_question(interview_state)
            
            return next_question
            
        except Exception as e:
            logger.error(f"Error generating next question: {str(e)}")
            return None
    
    def _generate_alternative_question(self, interview_state: InterviewState) -> Optional[InterviewQuestion]:
        """Generate alternative question when follow-up generation fails"""
        # Get question types that haven't been used much
        question_types = ['technical', 'behavioral', 'situational']
        used_types = [q.question_type for q in interview_state.question_history]
        
        # Find least used question type
        type_counts = {qtype: used_types.count(qtype) for qtype in question_types}
        least_used_type = min(type_counts, key=type_counts.get)
        
        # Generate question based on job requirements
        return InterviewQuestion(
            question=f"Can you tell me about your experience with {least_used_type} challenges?",
            question_type=least_used_type,
            difficulty="medium",
            expected_skills=[],
            context="Alternative question to continue interview flow"
        )
    
    def _create_session_from_state(self, interview_state: InterviewState) -> InterviewSession:
        """Create InterviewSession object from InterviewState"""
        return InterviewSession(
            session_id=interview_state.session_id,
            candidate_name=interview_state.candidate_name,
            job_title=interview_state.job_title,
            company=interview_state.company,
            start_time=interview_state.start_time,
            questions=interview_state.question_history,
            responses=interview_state.response_history,
            current_question_index=interview_state.current_question_index,
            is_completed=interview_state.is_completed,
            total_score=interview_state.total_score
        )
    
    def _get_interview_summary(self, session_id: str) -> Dict[str, any]:
        """Get comprehensive interview summary"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        interview_state = self.active_sessions[session_id]
        
        # Create session object for summary generation
        session = self._create_session_from_state(interview_state)
        
        # Generate summary using LLM
        summary = self.llm_integration.generate_interview_summary(session)
        
        # Add session metadata
        summary['session_id'] = session_id
        summary['candidate_name'] = interview_state.candidate_name
        summary['job_title'] = interview_state.job_title
        summary['company'] = interview_state.company
        summary['start_time'] = interview_state.start_time.isoformat() if interview_state.start_time else None
        summary['end_time'] = interview_state.end_time.isoformat() if interview_state.end_time else None
        summary['total_questions'] = len(interview_state.question_history)
        summary['total_responses'] = len(interview_state.response_history)
        summary['off_topic_count'] = interview_state.off_topic_count
        summary['context_valid'] = interview_state.context_valid
        
        # Add question-by-question breakdown
        summary['question_breakdown'] = []
        for i, (question, response) in enumerate(zip(interview_state.question_history, interview_state.response_history)):
            summary['question_breakdown'].append({
                'question_number': i + 1,
                'question': question.question,
                'question_type': question.question_type,
                'difficulty': question.difficulty,
                'response': response.response,
                'relevance_score': response.relevance_score,
                'technical_accuracy': response.technical_accuracy,
                'communication_quality': response.communication_quality,
                'confidence_level': response.confidence_level,
                'strengths': response.strengths,
                'areas_for_improvement': response.areas_for_improvement,
                'is_on_topic': response.is_on_topic
            })
        
        return summary
    
    def get_session_status(self, session_id: str) -> Dict[str, any]:
        """Get current status of an interview session"""
        if session_id not in self.active_sessions:
            return {'error': 'Session not found'}
        
        interview_state = self.active_sessions[session_id]
        
        return {
            'session_id': session_id,
            'candidate_name': interview_state.candidate_name,
            'job_title': interview_state.job_title,
            'company': interview_state.company,
            'is_started': interview_state.is_started,
            'is_completed': interview_state.is_completed,
            'current_question_index': interview_state.current_question_index,
            'total_questions': len(interview_state.question_history),
            'total_responses': len(interview_state.response_history),
            'off_topic_count': interview_state.off_topic_count,
            'context_valid': interview_state.context_valid,
            'start_time': interview_state.start_time.isoformat() if interview_state.start_time else None,
            'end_time': interview_state.end_time.isoformat() if interview_state.end_time else None
        }
    
    def end_interview(self, session_id: str) -> Dict[str, any]:
        """Manually end an interview session"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        interview_state = self.active_sessions[session_id]
        interview_state.is_completed = True
        interview_state.end_time = datetime.now()
        interview_state.current_question = None
        
        return self._get_interview_summary(session_id)
    
    def get_active_sessions(self) -> List[Dict[str, any]]:
        """Get list of all active interview sessions"""
        return [
            {
                'session_id': session_id,
                'candidate_name': state.candidate_name,
                'job_title': state.job_title,
                'company': state.company,
                'is_completed': state.is_completed,
                'start_time': state.start_time.isoformat() if state.start_time else None
            }
            for session_id, state in self.active_sessions.items()
        ]
    
    def cleanup_session(self, session_id: str) -> bool:
        """Remove a session from active sessions"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return True
        return False
    
    def save_session(self, session_id: str, filepath: str) -> bool:
        """Save interview session to file"""
        try:
            if session_id not in self.active_sessions:
                return False
            
            interview_state = self.active_sessions[session_id]
            
            # Convert to serializable format
            session_data = {
                'session_id': interview_state.session_id,
                'candidate_name': interview_state.candidate_name,
                'job_title': interview_state.job_title,
                'company': interview_state.company,
                'start_time': interview_state.start_time.isoformat() if interview_state.start_time else None,
                'end_time': interview_state.end_time.isoformat() if interview_state.end_time else None,
                'is_completed': interview_state.is_completed,
                'total_score': interview_state.total_score,
                'off_topic_count': interview_state.off_topic_count,
                'context_valid': interview_state.context_valid,
                'questions': [
                    {
                        'question': q.question,
                        'question_type': q.question_type,
                        'difficulty': q.difficulty,
                        'expected_skills': q.expected_skills,
                        'context': q.context
                    }
                    for q in interview_state.question_history
                ],
                'responses': [
                    {
                        'response': r.response,
                        'relevance_score': r.relevance_score,
                        'technical_accuracy': r.technical_accuracy,
                        'communication_quality': r.communication_quality,
                        'confidence_level': r.confidence_level,
                        'strengths': r.strengths,
                        'areas_for_improvement': r.areas_for_improvement,
                        'is_on_topic': r.is_on_topic
                    }
                    for r in interview_state.response_history
                ]
            }
            
            with open(filepath, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving session: {str(e)}")
            return False
