"""
LLM Integration for SkillScreen
Handles Gemini API integration for dynamic question generation and evaluation
"""

import google.generativeai as genai
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import os
from datetime import datetime
import re

from config import config
from logger import logger, log_info, log_error, log_warning, log_debug

@dataclass
class InterviewQuestion:
    """Interview question structure"""
    question: str
    question_type: str  # 'technical', 'behavioral', 'situational', 'follow_up'
    difficulty: str  # 'easy', 'medium', 'hard'
    expected_skills: List[str]
    context: str = ""
    follow_up_prompt: str = ""

@dataclass
class InterviewResponse:
    """Interview response evaluation"""
    response: str
    relevance_score: float  # 0.0 to 1.0
    technical_accuracy: float  # 0.0 to 1.0
    communication_quality: float  # 0.0 to 1.0
    confidence_level: float  # 0.0 to 1.0
    strengths: List[str]
    areas_for_improvement: List[str]
    is_on_topic: bool
    suggested_follow_up: str = ""

@dataclass
class InterviewSession:
    """Complete interview session data"""
    session_id: str
    candidate_name: str
    job_title: str
    company: str
    start_time: datetime
    questions: List[InterviewQuestion]
    responses: List[InterviewResponse]
    current_question_index: int = 0
    is_completed: bool = False
    total_score: float = 0.0

class GeminiIntegration:
    """Main Gemini API integration class"""
    
    def __init__(self, api_key: str = None):
        """Initialize Gemini integration"""
        self.api_key = api_key or config.llm.api_key
        if not self.api_key:
            raise ValueError("Gemini API key is required")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Configure generation settings for better responses
        generation_config = genai.types.GenerationConfig(
            temperature=config.llm.temperature,
            max_output_tokens=1000,  # Increased for detailed responses
            candidate_count=1,
        )
        
        self.model = genai.GenerativeModel(
            model_name=config.llm.model_name,
            generation_config=generation_config
        )
        
        # Interview configuration from config
        self.max_questions = config.interview.max_questions
        self.min_questions = config.interview.min_questions
        self.context_window = config.interview.context_window
        self.general_questions = config.interview.general_questions
        self.technical_questions = config.interview.technical_questions
        self.theoretical_questions = config.interview.theoretical_questions
        
        # Question templates
        self.question_templates = {
            'technical': {
                'easy': [
                    "Can you explain {skill} and how you've used it in your projects?",
                    "What is your experience with {skill}?",
                    "How would you approach a problem using {skill}?"
                ],
                'medium': [
                    "Describe a challenging project where you used {skill}. What were the key technical decisions you made?",
                    "How would you optimize a {skill} application for better performance?",
                    "What are the advantages and disadvantages of {skill} compared to alternatives?"
                ],
                'hard': [
                    "Design a system using {skill} that can handle {scale_requirement}. Walk me through your architecture decisions.",
                    "How would you troubleshoot a complex issue in a {skill} application?",
                    "Explain the trade-offs between different {skill} approaches for {specific_use_case}."
                ]
            },
            'behavioral': {
                'easy': [
                    "Tell me about a time when you had to learn a new technology quickly.",
                    "Describe a project you're particularly proud of.",
                    "How do you handle tight deadlines?"
                ],
                'medium': [
                    "Tell me about a time when you had to work with a difficult team member. How did you handle it?",
                    "Describe a situation where you had to make a technical decision that affected the entire team.",
                    "How do you stay updated with the latest technologies in your field?"
                ],
                'hard': [
                    "Tell me about a time when you had to lead a major technical initiative. What challenges did you face?",
                    "Describe a situation where you had to make a difficult trade-off between technical excellence and business requirements.",
                    "How do you mentor junior developers and help them grow?"
                ]
            },
            'situational': {
                'easy': [
                    "If you were given a project with unclear requirements, how would you proceed?",
                    "How would you handle a situation where your code review was rejected?",
                    "What would you do if you discovered a critical bug in production?"
                ],
                'medium': [
                    "If you had to choose between two technical approaches, how would you make the decision?",
                    "How would you handle a situation where the client wants to change requirements mid-project?",
                    "What would you do if you disagreed with your team lead on a technical decision?"
                ],
                'hard': [
                    "If you had to design a system to handle 10x the current traffic, how would you approach it?",
                    "How would you handle a situation where you had to choose between technical debt and new features?",
                    "If you had to rebuild a legacy system, how would you plan the migration?"
                ]
            }
        }
    
    def generate_initial_question(self, parsed_resume, parsed_job) -> InterviewQuestion:
        """Generate the first interview question based on resume and job description"""
        try:
            # Create context for the LLM
            context = self._create_interview_context(parsed_resume, parsed_job)
            
            prompt = f"""
            You are conducting a technical interview for a {parsed_job.title} position at {parsed_job.company}.
            
            Candidate Profile:
            - Name: {parsed_resume.name}
            - Skills: {', '.join(parsed_resume.skills[:10])}
            - Experience: {len(parsed_resume.experience)} positions
            - Summary: {parsed_resume.summary[:200]}
            
            Job Requirements:
            - Title: {parsed_job.title}
            - Required Skills: {', '.join(parsed_job.skills_required[:10])}
            - Experience Level: {parsed_job.experience_level}
            - Key Requirements: {', '.join([req.requirement for req in parsed_job.requirements[:3]])}
            
            Generate an engaging opening question that:
            1. Is relevant to the job requirements
            2. Allows the candidate to showcase their experience
            3. Is appropriate for their skill level
            4. Sets a professional but friendly tone
            
            Return your response in JSON format:
            {{
                "question": "Your question here",
                "question_type": "technical|behavioral|situational",
                "difficulty": "easy|medium|hard",
                "expected_skills": ["skill1", "skill2"],
                "context": "Brief context for the question"
            }}
            """
            
            response = self.model.generate_content(prompt)
            question_data = self._parse_json_response(response.text)
            
            return InterviewQuestion(
                question=question_data.get('question', 'Tell me about yourself and your experience.'),
                question_type=question_data.get('question_type', 'behavioral'),
                difficulty=question_data.get('difficulty', 'medium'),
                expected_skills=question_data.get('expected_skills', []),
                context=question_data.get('context', '')
            )
            
        except Exception as e:
            logger.error(f"Error generating initial question: {str(e)}")
            return InterviewQuestion(
                question="Tell me about yourself and your experience with the technologies mentioned in this role.",
                question_type="behavioral",
                difficulty="medium",
                expected_skills=parsed_job.skills_required[:3]
            )
    
    def generate_follow_up_question(self, session: InterviewSession, candidate_response: str) -> Optional[InterviewQuestion]:
        """Generate follow-up question based on candidate's response"""
        try:
            # Check if we should continue the interview
            if not self._should_continue_interview(session, candidate_response):
                return None
            
            # Create context from previous questions and responses
            context = self._create_session_context(session)
            
            prompt = f"""
            You are conducting a technical interview. Based on the candidate's response, generate an appropriate follow-up question.
            
            Interview Context:
            {context}
            
            Candidate's Latest Response:
            "{candidate_response}"
            
            Previous Questions Asked:
            {[q.question for q in session.questions[-3:]]}
            
            Generate a follow-up question that:
            1. Builds on their previous response
            2. Dives deeper into relevant technical areas
            3. Is appropriate for their demonstrated skill level
            4. Keeps the interview flowing naturally
            
            Return your response in JSON format:
            {{
                "question": "Your follow-up question here",
                "question_type": "technical|behavioral|situational|follow_up",
                "difficulty": "easy|medium|hard",
                "expected_skills": ["skill1", "skill2"],
                "context": "Why this follow-up is relevant",
                "follow_up_prompt": "Additional guidance for the interviewer"
            }}
            """
            
            response = self.model.generate_content(prompt)
            question_data = self._parse_json_response(response.text)
            
            return InterviewQuestion(
                question=question_data.get('question', 'Can you elaborate on that?'),
                question_type=question_data.get('question_type', 'follow_up'),
                difficulty=question_data.get('difficulty', 'medium'),
                expected_skills=question_data.get('expected_skills', []),
                context=question_data.get('context', ''),
                follow_up_prompt=question_data.get('follow_up_prompt', '')
            )
            
        except Exception as e:
            logger.error(f"Error generating follow-up question: {str(e)}")
            return None
    
    def evaluate_response(self, question: InterviewQuestion, response: str, session: InterviewSession) -> InterviewResponse:
        """Evaluate candidate's response to a question"""
        try:
            prompt = f"""
            You are evaluating a candidate's response in a technical interview.
            
            Question: "{question.question}"
            Question Type: {question.question_type}
            Difficulty: {question.difficulty}
            Expected Skills: {', '.join(question.expected_skills)}
            
            Candidate's Response: "{response}"
            
            Evaluate the response on the following criteria (0.0 to 1.0 scale):
            1. Relevance: How well does the response address the question?
            2. Technical Accuracy: How technically correct is the response?
            3. Communication Quality: How clear and well-structured is the response?
            4. Confidence Level: How confident does the candidate sound?
            
            Also identify:
            - Key strengths in the response
            - Areas for improvement
            - Whether the response is on-topic
            - Suggested follow-up questions
            
            Return your evaluation in JSON format:
            {{
                "relevance_score": 0.0-1.0,
                "technical_accuracy": 0.0-1.0,
                "communication_quality": 0.0-1.0,
                "confidence_level": 0.0-1.0,
                "strengths": ["strength1", "strength2"],
                "areas_for_improvement": ["area1", "area2"],
                "is_on_topic": true/false,
                "suggested_follow_up": "suggested question"
            }}
            """
            
            llm_response = self.model.generate_content(prompt)
            evaluation_data = self._parse_json_response(llm_response.text)
            
            return InterviewResponse(
                response=response,
                relevance_score=float(evaluation_data.get('relevance_score', 0.5)),
                technical_accuracy=float(evaluation_data.get('technical_accuracy', 0.5)),
                communication_quality=float(evaluation_data.get('communication_quality', 0.5)),
                confidence_level=float(evaluation_data.get('confidence_level', 0.5)),
                strengths=evaluation_data.get('strengths', []),
                areas_for_improvement=evaluation_data.get('areas_for_improvement', []),
                is_on_topic=bool(evaluation_data.get('is_on_topic', True)),
                suggested_follow_up=evaluation_data.get('suggested_follow_up', '')
            )
            
        except Exception as e:
            logger.error(f"Error evaluating response: {str(e)}")
            return InterviewResponse(
                response=response,
                relevance_score=0.5,
                technical_accuracy=0.5,
                communication_quality=0.5,
                confidence_level=0.5,
                strengths=[],
                areas_for_improvement=[],
                is_on_topic=True
            )
    
    def generate_interview_summary(self, session: InterviewSession) -> Dict[str, any]:
        """Generate comprehensive interview summary and feedback"""
        try:
            # Calculate overall scores
            total_responses = len(session.responses)
            if total_responses == 0:
                return self._generate_empty_summary()
            
            avg_relevance = sum(r.relevance_score for r in session.responses) / total_responses
            avg_technical = sum(r.technical_accuracy for r in session.responses) / total_responses
            avg_communication = sum(r.communication_quality for r in session.responses) / total_responses
            avg_confidence = sum(r.confidence_level for r in session.responses) / total_responses
            
            overall_score = (avg_relevance + avg_technical + avg_communication + avg_confidence) / 4
            
            # Collect all strengths and improvements
            all_strengths = []
            all_improvements = []
            for response in session.responses:
                all_strengths.extend(response.strengths)
                all_improvements.extend(response.areas_for_improvement)
            
            # Generate detailed feedback
            prompt = f"""
            Generate a comprehensive interview summary for a {session.job_title} position.
            
            Interview Details:
            - Candidate: {session.candidate_name}
            - Position: {session.job_title} at {session.company}
            - Questions Asked: {len(session.questions)}
            - Overall Score: {overall_score:.2f}/1.0
            
            Question-by-Question Analysis:
            {self._format_qa_analysis(session)}
            
            Provide a detailed summary including:
            1. Overall assessment and recommendation
            2. Key strengths demonstrated
            3. Areas for improvement
            4. Technical competency evaluation
            5. Communication skills assessment
            6. Specific recommendations for hiring decision
            7. Suggested next steps if proceeding
            
            Return your analysis in JSON format:
            {{
                "overall_assessment": "detailed assessment",
                "recommendation": "hire|no_hire|maybe",
                "key_strengths": ["strength1", "strength2"],
                "areas_for_improvement": ["area1", "area2"],
                "technical_competency": "assessment of technical skills",
                "communication_skills": "assessment of communication",
                "specific_recommendations": ["rec1", "rec2"],
                "next_steps": "suggested next steps"
            }}
            """
            
            llm_response = self.model.generate_content(prompt)
            summary_data = self._parse_json_response(llm_response.text)
            
            return {
                'overall_score': overall_score,
                'relevance_score': avg_relevance,
                'technical_score': avg_technical,
                'communication_score': avg_communication,
                'confidence_score': avg_confidence,
                'total_questions': len(session.questions),
                'total_responses': total_responses,
                'assessment': summary_data.get('overall_assessment', ''),
                'recommendation': summary_data.get('recommendation', 'maybe'),
                'key_strengths': summary_data.get('key_strengths', []),
                'areas_for_improvement': summary_data.get('areas_for_improvement', []),
                'technical_competency': summary_data.get('technical_competency', ''),
                'communication_skills': summary_data.get('communication_skills', ''),
                'specific_recommendations': summary_data.get('specific_recommendations', []),
                'next_steps': summary_data.get('next_steps', ''),
                'interview_duration': self._calculate_duration(session),
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating interview summary: {str(e)}")
            return self._generate_empty_summary()
    
    def _create_interview_context(self, parsed_resume, parsed_job) -> str:
        """Create context for interview generation"""
        return f"""
        Job: {parsed_job.title} at {parsed_job.company}
        Required Skills: {', '.join(parsed_job.skills_required[:10])}
        Experience Level: {parsed_job.experience_level}
        
        Candidate: {parsed_resume.name}
        Skills: {', '.join(parsed_resume.skills[:10])}
        Experience: {len(parsed_resume.experience)} positions
        Summary: {parsed_resume.summary[:200]}
        """
    
    def _create_session_context(self, session: InterviewSession) -> str:
        """Create context from interview session"""
        context_parts = []
        
        for i, (question, response) in enumerate(zip(session.questions[-3:], session.responses[-3:])):
            context_parts.append(f"Q{i+1}: {question.question}")
            context_parts.append(f"A{i+1}: {response.response[:200]}...")
            context_parts.append(f"Evaluation: Relevance={response.relevance_score:.2f}, Technical={response.technical_accuracy:.2f}")
        
        return "\n".join(context_parts)
    
    def _should_continue_interview(self, session: InterviewSession, response: str) -> bool:
        """Determine if interview should continue based on response"""
        # Check if response is too short or off-topic
        if len(response.strip()) < 20:
            return False
        
        # Check if we've reached max questions
        if len(session.questions) >= self.max_questions:
            return False
        
        # Check for off-topic responses
        off_topic_indicators = [
            "i don't know", "i can't answer", "not relevant", "off topic",
            "i don't understand", "can you repeat", "what do you mean"
        ]
        
        response_lower = response.lower()
        if any(indicator in response_lower for indicator in off_topic_indicators):
            return False
        
        return True
    
    def _parse_json_response(self, response_text: str) -> Dict:
        """Parse JSON response from LLM"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {}
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON response from LLM")
            return {}
    
    def _format_qa_analysis(self, session: InterviewSession) -> str:
        """Format Q&A analysis for summary generation"""
        analysis_parts = []
        
        for i, (question, response) in enumerate(zip(session.questions, session.responses)):
            analysis_parts.append(f"Q{i+1}: {question.question}")
            analysis_parts.append(f"A{i+1}: {response.response[:100]}...")
            analysis_parts.append(f"Scores: R={response.relevance_score:.2f}, T={response.technical_accuracy:.2f}, C={response.communication_quality:.2f}")
            analysis_parts.append("")
        
        return "\n".join(analysis_parts)
    
    def _calculate_duration(self, session: InterviewSession) -> str:
        """Calculate interview duration"""
        if not session.start_time:
            return "Unknown"
        
        duration = datetime.now() - session.start_time
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def _generate_empty_summary(self) -> Dict[str, any]:
        """Generate empty summary when no data is available"""
        return {
            'overall_score': 0.0,
            'relevance_score': 0.0,
            'technical_score': 0.0,
            'communication_score': 0.0,
            'confidence_score': 0.0,
            'total_questions': 0,
            'total_responses': 0,
            'assessment': 'No interview data available',
            'recommendation': 'no_hire',
            'key_strengths': [],
            'areas_for_improvement': [],
            'technical_competency': 'Unable to assess',
            'communication_skills': 'Unable to assess',
            'specific_recommendations': [],
            'next_steps': 'Conduct a proper interview',
            'interview_duration': '0m',
            'generated_at': datetime.now().isoformat()
        }
