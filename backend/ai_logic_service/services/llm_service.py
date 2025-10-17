"""
LLM Service for SkillScreen using Google Gemini Pro
Handles dynamic question generation and advanced NLP tasks
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any
import google.generativeai as genai
from datetime import datetime
import logging

from utils.logger import log_info, log_error, log_warning

class LLMService:
    """Service for LLM-powered question generation and analysis"""
    
    def __init__(self):
        self.model = None
        self.is_initialized = False
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize Google Gemini Pro model"""
        try:
            # Get API key from environment
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                log_warning("GEMINI_API_KEY not found in environment variables - using mock LLM service")
                # Initialize as mock service for development
                self.is_initialized = True
                self.model = "mock"
                return
            
            # Configure Gemini
            genai.configure(api_key=api_key)
            
            # Initialize the model
            self.model = genai.GenerativeModel('gemini-pro')
            self.is_initialized = True
            
            log_info("✅ Google Gemini Pro initialized successfully")
            
        except Exception as e:
            log_error(f"❌ Failed to initialize Gemini: {e}")
            # Fallback to mock service
            self.is_initialized = True
            self.model = "mock"
    
    async def generate_interview_question(
        self,
        question_type: str,
        candidate_context: Dict[str, Any],
        job_context: Dict[str, Any],
        previous_questions: List[str] = None,
        question_number: int = 1
    ) -> str:
        """Generate personalized interview question using Gemini Pro"""
        
        if not self.is_initialized:
            return self._get_fallback_question(question_type, question_number)
        
        try:
            # Build context for question generation
            context_prompt = self._build_question_prompt(
                question_type, candidate_context, job_context, previous_questions, question_number
            )
            
            # Generate question using Gemini
            response = await self._generate_with_gemini(context_prompt)
            
            if response and len(response.strip()) > 10:
                log_info(f"✅ Generated {question_type} question using Gemini Pro")
                return response.strip()
            else:
                log_warning("⚠️ Gemini returned empty/invalid response, using fallback")
                return self._get_fallback_question(question_type, question_number)
                
        except Exception as e:
            log_error(f"❌ Error generating question with Gemini: {e}")
            return self._get_fallback_question(question_type, question_number)
    
    def _build_question_prompt(
        self,
        question_type: str,
        candidate_context: Dict[str, Any],
        job_context: Dict[str, Any],
        previous_questions: List[str] = None,
        question_number: int = 1
    ) -> str:
        """Build comprehensive prompt for question generation"""
        
        # Extract key information
        candidate_name = candidate_context.get('name', 'Candidate')
        candidate_skills = candidate_context.get('skills', [])
        candidate_experience = candidate_context.get('experience_years', 0)
        candidate_resume = candidate_context.get('resume_text', '')
        
        job_title = job_context.get('title', 'Position')
        job_company = job_context.get('company', 'Company')
        job_description = job_context.get('description', '')
        job_skills = job_context.get('required_skills', [])
        job_level = job_context.get('experience_level', 'mid')
        
        # Build previous questions context
        prev_questions_text = ""
        if previous_questions:
            prev_questions_text = f"\nPrevious questions asked:\n" + "\n".join([f"- {q}" for q in previous_questions[-3:]])
        
        # Create comprehensive prompt
        prompt = f"""
You are an expert technical interviewer conducting a {question_type} interview. Generate a personalized, engaging question for question #{question_number}.

CANDIDATE PROFILE:
- Name: {candidate_name}
- Experience: {candidate_experience} years
- Skills: {', '.join(candidate_skills[:8]) if candidate_skills else 'Not specified'}
- Resume Summary: {candidate_resume[:500] if candidate_resume else 'Not provided'}

JOB CONTEXT:
- Position: {job_title} at {job_company}
- Level: {job_level}
- Required Skills: {', '.join(job_skills[:8]) if job_skills else 'Not specified'}
- Job Description: {job_description[:300] if job_description else 'Not provided'}

QUESTION REQUIREMENTS:
- Type: {question_type}
- Question Number: {question_number}
- Make it specific to the candidate's background and job requirements
- Avoid generic questions
- Focus on practical, real-world scenarios
- Keep it conversational and engaging
- Ensure it hasn't been asked before{prev_questions_text}

Generate a single, well-crafted interview question that:
1. Is personalized to this candidate's experience and skills
2. Relates to the specific job requirements
3. Tests relevant competencies for a {job_level} level {job_title} position
4. Encourages detailed, specific responses
5. Is appropriate for question #{question_number} in the interview flow

Return only the question text, no additional formatting or explanations.
"""
        
        return prompt.strip()
    
    async def _generate_with_gemini(self, prompt: str) -> str:
        """Generate response using Gemini Pro or mock service"""
        try:
            # If using mock service, generate intelligent mock questions
            if self.model == "mock":
                return self._generate_mock_question(prompt)
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.model.generate_content(prompt)
            )
            
            if response and response.text:
                return response.text
            else:
                return ""
                
        except Exception as e:
            log_error(f"❌ Gemini generation error: {e}")
            return ""
    
    def _generate_mock_question(self, prompt: str) -> str:
        """Generate intelligent mock questions based on context"""
        try:
            # Extract context from prompt
            candidate_name = "Candidate"
            job_title = "Position"
            skills = []
            
            # Simple parsing of the prompt to extract context
            if "Candidate Name:" in prompt:
                name_line = [line for line in prompt.split('\n') if 'Candidate Name:' in line][0]
                candidate_name = name_line.split('Candidate Name:')[1].strip()
            
            if "Job Title:" in prompt:
                job_line = [line for line in prompt.split('\n') if 'Job Title:' in line][0]
                job_title = job_line.split('Job Title:')[1].strip()
            
            if "Required Skills:" in prompt:
                skills_line = [line for line in prompt.split('\n') if 'Required Skills:' in line][0]
                skills_text = skills_line.split('Required Skills:')[1].strip()
                skills = [s.strip() for s in skills_text.split(',') if s.strip()]
            
            # Generate contextual questions based on extracted information
            mock_questions = [
                f"Hi {candidate_name}! Can you tell me about your background and what interests you about this {job_title} role?",
                f"Based on your experience, how would you approach solving a complex problem in {job_title}?",
                f"I see you have experience with {', '.join(skills[:2]) if skills else 'various technologies'}. Can you walk me through a challenging project you've worked on?",
                f"What do you think are the most important skills for success in a {job_title} position?",
                f"How do you stay updated with the latest trends and technologies in your field?",
                f"Can you describe a time when you had to learn something new quickly for a project?",
                f"What motivates you most in your work, and how does that align with this {job_title} role?",
                f"If you were to start this {job_title} position tomorrow, what would be your first priorities?"
            ]
            
            # Return a question based on the prompt content
            import random
            return random.choice(mock_questions)
            
        except Exception as e:
            log_error(f"❌ Mock question generation error: {e}")
            return "Can you tell me about your experience and what interests you about this role?"
    
    def _get_fallback_question(self, question_type: str, question_number: int) -> str:
        """Fallback question when LLM is unavailable"""
        
        fallback_questions = {
            'general': [
                "Tell me about yourself and your experience with this role.",
                "What are your key strengths for this position?",
                "Why are you interested in this role and our company?",
                "How do you approach problem-solving in your work?",
                "What motivates you most in your professional life?"
            ],
            'technical': [
                "Describe a challenging technical problem you solved recently.",
                "How do you ensure code quality in your projects?",
                "What technologies and tools are you most comfortable with?",
                "Explain your approach to debugging and troubleshooting.",
                "How do you stay updated with the latest technologies?"
            ],
            'behavioral': [
                "Tell me about a time when you had to work with a difficult team member.",
                "Describe a situation where you had to learn something new quickly.",
                "Give me an example of a project where you had to meet a tight deadline.",
                "Tell me about a time when you had to explain a complex concept to someone.",
                "Describe a situation where you had to adapt to significant changes."
            ],
            'theoretical': [
                "How would you approach designing a scalable system?",
                "What are the key principles of good software architecture?",
                "How do you balance performance and maintainability in your code?",
                "What factors do you consider when choosing a technology stack?",
                "How do you ensure security in your applications?"
            ]
        }
        
        questions = fallback_questions.get(question_type, fallback_questions['general'])
        question_index = (question_number - 1) % len(questions)
        
        log_info(f"Using fallback {question_type} question #{question_number}")
        return questions[question_index]
    
    async def analyze_response_quality(
        self,
        question: str,
        response: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze response quality using LLM"""
        
        if not self.is_initialized:
            return self._get_fallback_analysis(response)
        
        try:
            analysis_prompt = f"""
Analyze this interview response for quality and relevance.

QUESTION: {question}

RESPONSE: {response}

CANDIDATE CONTEXT:
- Experience: {context.get('experience_years', 0)} years
- Skills: {', '.join(context.get('skills', [])[:5])}

Provide analysis in JSON format with these fields:
{{
    "relevance_score": 0-10,
    "depth_score": 0-10,
    "specificity_score": 0-10,
    "communication_score": 0-10,
    "overall_score": 0-10,
    "strengths": ["strength1", "strength2"],
    "areas_for_improvement": ["area1", "area2"],
    "feedback": "constructive feedback text"
}}

Focus on:
- How well the response addresses the question
- Specificity and detail level
- Communication clarity
- Relevance to the role
- Evidence of experience and skills

Return only valid JSON, no additional text.
"""
            
            analysis_response = await self._generate_with_gemini(analysis_prompt)
            
            if analysis_response:
                try:
                    # Try to parse JSON response
                    analysis_data = json.loads(analysis_response)
                    log_info("✅ Generated LLM-based response analysis")
                    return analysis_data
                except json.JSONDecodeError:
                    log_warning("⚠️ Invalid JSON from Gemini analysis, using fallback")
                    return self._get_fallback_analysis(response)
            else:
                return self._get_fallback_analysis(response)
                
        except Exception as e:
            log_error(f"❌ Error analyzing response with Gemini: {e}")
            return self._get_fallback_analysis(response)
    
    def _get_fallback_analysis(self, response: str) -> Dict[str, Any]:
        """Fallback analysis when LLM is unavailable"""
        
        # Basic analysis based on response length and content
        response_length = len(response)
        
        # Simple scoring based on length and content indicators
        if response_length > 200:
            depth_score = min(8, response_length // 50)
            communication_score = 7
        elif response_length > 100:
            depth_score = 5
            communication_score = 6
        else:
            depth_score = 3
            communication_score = 4
        
        # Check for specific indicators
        specificity_score = 6
        if any(word in response.lower() for word in ['specifically', 'for example', 'in my experience', 'i worked on']):
            specificity_score = 8
        
        relevance_score = 7  # Default assumption
        
        overall_score = (depth_score + communication_score + specificity_score + relevance_score) // 4
        
        return {
            "relevance_score": relevance_score,
            "depth_score": depth_score,
            "specificity_score": specificity_score,
            "communication_score": communication_score,
            "overall_score": overall_score,
            "strengths": ["Provided detailed response"] if response_length > 150 else ["Participated in interview"],
            "areas_for_improvement": ["Could provide more specific examples"] if response_length < 200 else ["Continue professional development"],
            "feedback": "Response analyzed using basic metrics. Advanced LLM analysis unavailable."
        }
    
    async def generate_follow_up_question(
        self,
        original_question: str,
        response: str,
        context: Dict[str, Any]
    ) -> Optional[str]:
        """Generate follow-up question based on response"""
        
        if not self.is_initialized:
            return None
        
        try:
            follow_up_prompt = f"""
Based on this interview exchange, generate a relevant follow-up question.

ORIGINAL QUESTION: {original_question}
RESPONSE: {response}

Generate a follow-up question that:
1. Builds on the candidate's response
2. Delves deeper into their experience
3. Tests related competencies
4. Is natural and conversational

Return only the follow-up question, no additional text.
"""
            
            follow_up = await self._generate_with_gemini(follow_up_prompt)
            
            if follow_up and len(follow_up.strip()) > 10:
                log_info("✅ Generated follow-up question using Gemini Pro")
                return follow_up.strip()
            else:
                return None
                
        except Exception as e:
            log_error(f"❌ Error generating follow-up with Gemini: {e}")
            return None

# Global instance
llm_service = LLMService()
