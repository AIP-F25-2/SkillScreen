"""
Enhanced LLM Service for SkillScreen using Multiple APIs
Integrates Google Gemini Pro, Wolfram Alpha, and SerpApi for comprehensive question generation
"""

import os
import json
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
import google.generativeai as genai
from datetime import datetime
import logging

from utils.logger import log_info, log_error, log_warning

class EnhancedLLMService:
    """Enhanced service for LLM-powered question generation using multiple APIs"""
    
    def __init__(self):
        self.gemini_model = None
        self.wolfram_app_id = None
        self.serpapi_key = None
        self.is_initialized = False
        self._initialize_apis()
    
    def _get_gemini_model_name(self) -> str:
        """Get Gemini model name from config.json, environment, or use fallback"""
        # Try reading from config.json first
        try:
            import json
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    model_name = config.get('llm', {}).get('model_name', '')
                    if model_name:
                        # Remove 'models/' prefix if present
                        model_name = model_name.replace('models/', '').strip()
                        if model_name:
                            return model_name
        except Exception:
            pass
        
        # Try environment variable
        model_name = os.getenv('GEMINI_MODEL_NAME', 'gemini-1.5-flash')
        return model_name
    
    def _initialize_apis(self):
        """Initialize all available APIs"""
        try:
            # Initialize Gemini
            gemini_key = os.getenv('GEMINI_API_KEY')
            if gemini_key:
                genai.configure(api_key=gemini_key)
                model_name = self._get_gemini_model_name()
                try:
                    self.gemini_model = genai.GenerativeModel(model_name)
                    log_info(f"[OK] Google Gemini initialized with model: {model_name}")
                except Exception as e:
                    log_warning(f"[WARNING] Failed to initialize Gemini model '{model_name}': {e}")
                    # Try fallback models
                    fallback_models = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
                    for fallback in fallback_models:
                        try:
                            self.gemini_model = genai.GenerativeModel(fallback)
                            log_info(f"[OK] Google Gemini initialized with fallback model: {fallback}")
                            break
                        except Exception:
                            continue
                    if not self.gemini_model:
                        log_warning("[WARNING] Could not initialize any Gemini model, will use fallback questions")
            else:
                log_warning("[WARNING] GEMINI_API_KEY not found")
            
            # Initialize Wolfram Alpha
            self.wolfram_app_id = os.getenv('WOLFRAM_APP_ID')
            if self.wolfram_app_id:
                log_info("[OK] Wolfram Alpha API configured")
            
            # Initialize SerpApi
            self.serpapi_key = os.getenv('SERPAPI_KEY')
            if self.serpapi_key:
                log_info("[OK] SerpApi configured")
            
            self.is_initialized = True
            log_info("[INIT] Enhanced LLM Service initialized with multiple APIs")
            
        except Exception as e:
            log_error(f"[ERROR] Failed to initialize APIs: {e}")
            self.is_initialized = True  # Still allow fallback operation
    
    async def generate_interview_question(
        self,
        question_type: str,
        candidate_context: Dict[str, Any],
        job_context: Dict[str, Any],
        previous_questions: List[str] = None,
        previous_responses: List[str] = None,  # Add previous_responses parameter
        question_number: int = 1
    ) -> str:
        """Generate personalized interview question using multiple APIs"""
        
        if not self.is_initialized:
            return self._get_fallback_question(question_type, question_number)
        
        try:
            # Build comprehensive context with previous responses
            context_prompt = self._build_enhanced_prompt(
                question_type, candidate_context, job_context, previous_questions, previous_responses, question_number
            )
            
            # Try Gemini first
            if self.gemini_model:
                response = await self._generate_with_gemini(context_prompt)
                if response and len(response.strip()) > 10:
                    log_info("[OK] Generated question using Gemini Pro")
                    return response.strip()
            
            # Fallback to enhanced mock with real-time data
            enhanced_question = await self._generate_enhanced_mock_question(
                question_type, candidate_context, job_context, question_number
            )
            if enhanced_question:
                log_info("[OK] Generated enhanced question with real-time data")
                return enhanced_question
            
            # Final fallback
            return self._get_fallback_question(question_type, question_number)
                
        except Exception as e:
            log_error(f"[ERROR] Error generating question: {e}")
            return self._get_fallback_question(question_type, question_number)
    
    def _build_enhanced_prompt(
        self,
        question_type: str,
        candidate_context: Dict[str, Any],
        job_context: Dict[str, Any],
        previous_questions: List[str] = None,
        previous_responses: List[str] = None,  # Add previous_responses parameter
        question_number: int = 1
    ) -> str:
        """Build enhanced prompt with real-time data integration and previous responses"""
        
        # Extract key information
        candidate_name = candidate_context.get('name', 'Candidate')
        candidate_skills = candidate_context.get('skills', [])
        candidate_experience = candidate_context.get('experience_years', 0)
        resume_text = candidate_context.get('resume_text', '')[:500]  # First 500 chars of resume
        
        job_title = job_context.get('title', 'Position')
        job_company = job_context.get('company', 'Company')
        job_description = job_context.get('description', '')
        job_skills = job_context.get('required_skills', [])
        job_level = job_context.get('experience_level', 'mid')
        
        # Build previous questions context
        prev_questions_text = ""
        if previous_questions:
            prev_questions_text = f"\nPrevious questions asked:\n" + "\n".join([f"- {q}" for q in previous_questions[-3:]])
        
        # Build previous responses context (CRITICAL for dynamic question generation)
        prev_responses_text = ""
        if previous_responses:
            prev_responses_text = f"\nPrevious responses given:\n" + "\n".join([f"- {r[:100]}..." if len(r) > 100 else f"- {r}" for r in previous_responses[-3:]])
        
        # Create comprehensive prompt with real-time context including previous responses
        prompt = f"""
You are a senior {job_title} professional conducting a natural, conversational interview. Generate a realistic question that a human interviewer would ask based on the candidate's previous responses.

CANDIDATE BACKGROUND:
- Name: {candidate_name}
- Experience: {candidate_experience} years in the field
- Skills: {', '.join(candidate_skills[:6]) if candidate_skills else 'Various technical skills'}
- Resume Summary: {resume_text if resume_text else 'Technical professional'}
- Current Date: {datetime.now().strftime('%B %Y')}

POSITION DETAILS:
- Role: {job_title} at {job_company}
- Level: {job_level} level position
- Key Requirements: {', '.join(job_skills[:6]) if job_skills else 'Technical expertise'}
- Job Description: {job_description[:300] if job_description else 'Technical development role'}

INTERVIEW CONTEXT:
- Question #{question_number} of the interview
- Question Type: {question_type}
{prev_questions_text if prev_questions_text else ''}
{prev_responses_text if prev_responses_text else ''}

CRITICAL INSTRUCTIONS:
- DO NOT repeat the same question that was already asked
- Build on the candidate's previous responses - ask follow-up questions or explore new areas
- If they mentioned specific projects or technologies, ask for more details
- If they gave brief answers, ask for elaboration
- Write as a natural, human interviewer would speak
- Make it conversational and relatable
- Reference their specific experience level ({candidate_experience} years)
- Connect to their skills: {', '.join(candidate_skills[:4]) if candidate_skills else 'their background'}
- Avoid overly formal or AI-sounding language
- Focus on practical scenarios they would encounter
- Keep it specific to the {job_title} role
- Use information from their resume and previous responses to personalize the question

Generate ONE natural interview question that:
1. Is personalized to this candidate's experience and skills
2. Relates to the specific job requirements
3. Tests relevant competencies for a {job_level} level {job_title} position
4. Encourages detailed, specific responses
5. Is appropriate for question #{question_number} in the interview flow
6. Builds on previous responses (if any) or explores new areas
7. Does NOT repeat previous questions
8. Incorporates current industry trends and best practices

Return only the question text, no additional formatting or explanations.
"""
        
        return prompt.strip()
    
    async def _generate_with_gemini(self, prompt: str) -> str:
        """Generate response using Gemini model with improved error handling"""
        try:
            if not self.gemini_model:
                return ""
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.gemini_model.generate_content(prompt)
            )
            
            if response and response.text:
                return response.text
            else:
                return ""
                
        except Exception as e:
            error_msg = str(e)
            # Check for 404 model not found error
            if '404' in error_msg or 'not found' in error_msg.lower() or 'not supported' in error_msg.lower():
                log_warning(f"[WARNING] Gemini model not available: {error_msg}")
                log_warning("[WARNING] Will use fallback question generation")
            else:
                log_error(f"❌ Gemini generation error: {e}")
            return ""
    
    async def _generate_enhanced_mock_question(
        self,
        question_type: str,
        candidate_context: Dict[str, Any],
        job_context: Dict[str, Any],
        question_number: int
    ) -> str:
        """Generate enhanced mock questions with real-time data"""
        try:
            # Extract context
            candidate_name = candidate_context.get('name', 'Candidate')
            candidate_skills = candidate_context.get('skills', [])
            candidate_experience = candidate_context.get('experience_years', 0)
            
            job_title = job_context.get('title', 'Position')
            job_skills = job_context.get('required_skills', [])
            job_level = job_context.get('experience_level', 'mid')
            
            # Get current industry trends if possible
            industry_trends = await self._get_industry_trends(job_title, job_skills)
            
            # Generate contextual questions based on extracted information
            enhanced_questions = []
            
            if question_type == 'technical':
                enhanced_questions = [
                    f"Hi {candidate_name}! With your {candidate_experience} years of experience, how would you approach architecting a scalable {job_title} solution?",
                    f"I see you have experience with {', '.join(candidate_skills[:3]) if candidate_skills else 'various technologies'}. Can you walk me through how you'd implement a microservices architecture?",
                    f"Given the current trends in {industry_trends}, how do you stay updated with the latest {job_title} technologies?",
                    f"Describe a challenging technical problem you solved recently and the approach you took.",
                    f"How would you ensure code quality and maintainability in a {job_level}-level {job_title} project?"
                ]
            elif question_type == 'behavioral':
                enhanced_questions = [
                    f"Tell me about a time when you had to learn a new technology quickly for a {job_title} project.",
                    f"Describe a situation where you had to work with a difficult team member on a technical project.",
                    f"How do you approach mentoring junior developers in your {job_title} role?",
                    f"Give me an example of a project where you had to meet a tight deadline while maintaining quality.",
                    f"Tell me about a time when you had to explain a complex technical concept to non-technical stakeholders."
                ]
            else:  # general
                enhanced_questions = [
                    f"Hi {candidate_name}! What interests you most about this {job_title} role?",
                    f"Based on your {candidate_experience} years of experience, what do you think are the key challenges in {job_title}?",
                    f"How do you see the future of {industry_trends} evolving in the next few years?",
                    f"What motivates you most in your work, and how does that align with this {job_title} position?",
                    f"If you were to start this {job_title} position tomorrow, what would be your first priorities?"
                ]
            
            # Return a question based on question number
            question_index = (question_number - 1) % len(enhanced_questions)
            return enhanced_questions[question_index]
            
        except Exception as e:
            log_error(f"❌ Enhanced mock question generation error: {e}")
            return self._get_fallback_question(question_type, question_number)
    
    async def _get_industry_trends(self, job_title: str, job_skills: List[str]) -> str:
        """Get current industry trends using SerpApi"""
        try:
            if not self.serpapi_key:
                return "technology"
            
            # Create search query for industry trends
            search_query = f"{job_title} trends 2024"
            if job_skills:
                search_query += f" {' '.join(job_skills[:2])}"
            
            async with aiohttp.ClientSession() as session:
                params = {
                    'q': search_query,
                    'api_key': self.serpapi_key,
                    'num': 3
                }
                
                async with session.get('https://serpapi.com/search', params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'organic_results' in data and data['organic_results']:
                            # Extract relevant trend information
                            trends = []
                            for result in data['organic_results'][:2]:
                                title = result.get('title', '')
                                snippet = result.get('snippet', '')
                                if any(word in title.lower() for word in ['trend', 'future', '2024', 'latest']):
                                    trends.append(title.split(' - ')[0])
                            
                            if trends:
                                return ', '.join(trends[:2])
            
            return "technology"
            
        except Exception as e:
            log_warning(f"[WARNING] Could not fetch industry trends: {e}")
            return "technology"
    
    def _get_fallback_question(self, question_type: str, question_number: int) -> str:
        """Fallback question when all APIs are unavailable"""
        
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

# Global instance
llm_service = EnhancedLLMService()
