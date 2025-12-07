"""
Enhanced LLM Service for SkillScreen using Multiple APIs
Integrates Groq (Llama 3), Mistral, and Google Gemini with fallback mechanisms
Addresses AI bias and hallucination through multi-LLM consensus
"""

import os
import json
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Tuple
import google.generativeai as genai
from datetime import datetime
import logging

from utils.logger import log_info, log_error, log_warning

class EnhancedLLMService:
    """Enhanced service for LLM-powered question generation using multiple APIs with fallback and bias mitigation"""
    
    # LLM Provider Constants
    LLM_GEMINI = 'gemini'
    LLM_GROQ = 'groq'
    LLM_MISTRAL = 'mistral'

    def __init__(self):
        # Primary LLM: Gemini
        self.gemini_model = None
        
        # Fallback LLMs
        self.groq_api_key = None
        self.groq_base_url = "https://api.groq.com/openai/v1"
        
        self.mistral_api_key = None
        self.mistral_base_url = "https://api.mistral.ai/v1"
        
        # SerpApi for industry trends
        self.serpapi_key = None
        
        # LLM Priority Order: Gemini (primary) -> Groq -> Mistral
        self.llm_priority = [self.LLM_GEMINI, self.LLM_GROQ, self.LLM_MISTRAL]
        self.available_llms = []
        
        self.is_initialized = False
        self._initialize_apis()
    
    def _get_gemini_model_name(self) -> str:
        """Get Gemini model name from config.json, environment, or use fallback"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    model_name = config.get('llm', {}).get('model_name', '')
                    if model_name:
                        model_name = model_name.replace('models/', '').strip()
                        if model_name:
                            return model_name
        except Exception:
            pass
        
        model_name = os.getenv('GEMINI_MODEL_NAME', 'gemini-2.5-flash')
        if model_name.startswith('models/'):
            model_name = model_name.replace('models/', '')
        
        return model_name.strip() if model_name.strip() else 'gemini-2.5-flash'
    
    def _initialize_apis(self):
        """Initialize all available APIs"""
        try:
            # Try loading from .config file first, then environment variables
            gemini_key = None
            groq_key = None
            mistral_key = None
            serpapi_key = None
            
            # Try reading from .config file
            try:
                from utils.config_loader import get_config
                gemini_key = get_config('GEMINI_API_KEY') or os.getenv('GEMINI_API_KEY')
                groq_key = get_config('GROQ_API_KEY') or os.getenv('GROQ_API_KEY')
                mistral_key = get_config('MISTRAL_API_KEY') or os.getenv('MISTRAL_API_KEY')
                serpapi_key = get_config('SERPAPI_KEY') or os.getenv('SERPAPI_KEY')
            except Exception as e:
                log_warning(f"[WARNING] Could not load from .config file: {e}. Using environment variables only.")
                gemini_key = os.getenv('GEMINI_API_KEY')
                groq_key = os.getenv('GROQ_API_KEY')
                mistral_key = os.getenv('MISTRAL_API_KEY')
                serpapi_key = os.getenv('SERPAPI_KEY')
            
            # Initialize Gemini (Primary LLM)
            if gemini_key:
                genai.configure(api_key=gemini_key)
                
                models_to_try = [
                    'gemini-2.5-flash',
                    'gemini-2.0-flash',
                    'gemini-2.5-pro',
                    'gemini-2.0-flash-001',
                    'gemini-pro',
                    'gemini-1.5-pro',
                ]
                
                model_name = self._get_gemini_model_name()
                if model_name and model_name not in models_to_try:
                    models_to_try.insert(0, model_name)
                
                for model in models_to_try:
                    try:
                        log_info(f"[INIT] Attempting to initialize Gemini model: {model}")
                        self.gemini_model = genai.GenerativeModel(model)
                        log_info(f"[OK] Google Gemini initialized successfully as PRIMARY LLM with model: {model}")
                        self.available_llms.append(self.LLM_GEMINI)
                        break
                    except Exception as e:
                        error_msg = str(e)
                        if '404' in error_msg or 'not found' in error_msg.lower():
                            continue
                        continue
                
                if not self.gemini_model:
                    log_warning("[WARNING] Could not initialize any Gemini model")
            else:
                log_warning("[WARNING] GEMINI_API_KEY not found - Gemini will not be available")
            
            # Initialize Groq (Fallback LLM - Llama 3)
            self.groq_api_key = groq_key
            if self.groq_api_key:
                log_info("[OK] Groq API (Llama 3) configured as FALLBACK LLM")
                self.available_llms.append(self.LLM_GROQ)
            else:
                log_warning("[WARNING] GROQ_API_KEY not found - Groq will not be available")
            
            # Initialize Mistral (Fallback LLM)
            self.mistral_api_key = mistral_key
            if self.mistral_api_key:
                log_info("[OK] Mistral API configured as FALLBACK LLM")
                self.available_llms.append(self.LLM_MISTRAL)
            else:
                log_warning("[WARNING] MISTRAL_API_KEY not found - Mistral will not be available")
            
            # Initialize SerpApi
            self.serpapi_key = serpapi_key
            if self.serpapi_key:
                log_info(f"[OK] SerpApi configured (Key: {self.serpapi_key[:20]}...)")
            else:
                log_warning("[WARNING] SERPAPI_KEY not found")
            
            self.is_initialized = True
            log_info(f"[INIT] Enhanced LLM Service initialized with {len(self.available_llms)} LLM(s): {', '.join(self.available_llms)}")
            
        except Exception as e:
            log_error(f"[ERROR] Failed to initialize APIs: {e}")
            self.is_initialized = True  # Still allow fallback operation
    
    async def generate_interview_question(
        self,
        question_type: str,
        candidate_context: Dict[str, Any],
        job_context: Dict[str, Any],
        previous_questions: List[str] = None,
        previous_responses: List[str] = None,
        question_number: int = 1
    ) -> str:
        """Generate personalized interview question using multiple LLMs with fallback and bias mitigation"""
        
        if not self.is_initialized:
            return self._get_fallback_question(question_type, question_number)
        
        try:
            # Build comprehensive context
            context_prompt = await self._build_enhanced_prompt(
                question_type, candidate_context, job_context, previous_questions, previous_responses, question_number
            )
            
            # Try LLMs in priority order with fallback
            response = await self._try_llm_generation(context_prompt, question_number, question_type, previous_questions)
            if response:
                return response
            
            # Fallback to enhanced mock or rule-based
            return await self._handle_generation_fallback(
                question_type, candidate_context, job_context, question_number, previous_questions, previous_responses
            )
                
        except Exception as e:
            log_error(f"[ERROR] Error generating question: {e}")
            return self._get_fallback_question(question_type, question_number)

    async def _try_llm_generation(
        self, prompt: str, question_number: int, question_type: str,
        previous_questions: List[str]
    ) -> Optional[str]:
        responses = []
        used_llms = []
        
        for llm_name in self.llm_priority:
            if llm_name not in self.available_llms:
                continue
            
            try:
                log_info(f"[LLM API CALL] Question #{question_number} - Attempting {llm_name.upper()} API call...")
                response = await self._generate_with_llm(llm_name, prompt)
                
                if response and len(response.strip()) > 10:
                    responses.append((llm_name, response.strip()))
                    used_llms.append(llm_name)
                    
                    # If primary LLM (Gemini) succeeds, use it directly
                    if llm_name == self.LLM_GEMINI and len(response.strip()) > 20:
                        validated_response = await self._validate_response(response.strip(), responses, question_type)
                        log_info(f"[LLM FINAL] Using {llm_name.upper()} response for question #{question_number}")
                        return validated_response
                    
                    # If we have at least one good response, continue to bias mitigation
                    if len(response.strip()) > 20:
                        break
                        
            except Exception as e:
                log_error(f"[LLM API ERROR] {llm_name.upper()} failed for question #{question_number}: {str(e)}")
                continue
        
        # Bias and hallucination mitigation
        if len(responses) > 1:
            log_info(f"[BIAS_MITIGATION] Comparing {len(responses)} responses from {', '.join(used_llms)}")
            final_response = self._mitigate_bias_and_hallucination(responses)
            if final_response:
                return final_response
        
        # Use best available response
        if responses:
            best_response = max(responses, key=lambda x: len(x[1]))
            return best_response[1]
            
        return None

    async def _handle_generation_fallback(
        self, question_type: str, candidate_context: Dict[str, Any],
        job_context: Dict[str, Any], question_number: int,
        previous_questions: List[str], previous_responses: List[str]
    ) -> str:
        log_warning(f"[LLM FALLBACK] All LLM APIs failed. Using rule-based fallback for question #{question_number}")
        
        enhanced_question = await self._generate_enhanced_mock_question(
            question_type, candidate_context, job_context, question_number, previous_questions, previous_responses
        )
        
        if enhanced_question:
            if previous_questions and enhanced_question in previous_questions:
                log_warning("[LLM FALLBACK] Generated duplicate question, regenerating...")
                enhanced_question = await self._generate_enhanced_mock_question(
                    question_type, candidate_context, job_context, question_number + 1, previous_questions, previous_responses
                )
            return enhanced_question
        
        log_error(f"[LLM ERROR] All question generation methods failed for question #{question_number}")
        return self._get_fallback_question(question_type, question_number)
    
    async def _generate_with_llm(self, llm_name: str, prompt: str) -> Optional[str]:
        """Generate response using specified LLM"""
        try:
            if llm_name == self.LLM_GROQ:
                return await self._generate_with_groq(prompt)
            elif llm_name == self.LLM_MISTRAL:
                return await self._generate_with_mistral(prompt)
            elif llm_name == self.LLM_GEMINI:
                return await self._generate_with_gemini(prompt)
            else:
                return None
        except Exception as e:
            log_error(f"[ERROR] Error generating with {llm_name}: {e}")
            return None
    
    async def _generate_with_groq(self, prompt: str) -> Optional[str]:
        """Generate response using Groq API (Llama 3)"""
        if not self.groq_api_key:
            return None
        
        return await self._make_llm_request(
            url=f"{self.groq_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            },
            data={
                "model": "llama-3.1-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You are a senior technical interviewer. Generate natural, conversational interview questions."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 200
            },
            provider_name="Groq"
        )
    
    async def _generate_with_mistral(self, prompt: str) -> Optional[str]:
        """Generate response using Mistral API"""
        if not self.mistral_api_key:
            return None
        
        return await self._make_llm_request(
            url=f"{self.mistral_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.mistral_api_key}",
                "Content-Type": "application/json"
            },
            data={
                "model": "mistral-medium",
                "messages": [
                    {"role": "system", "content": "You are a senior technical interviewer. Generate natural, conversational interview questions."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 200
            },
            provider_name="Mistral"
        )

    async def _make_llm_request(self, url: str, headers: Dict, data: Dict, provider_name: str) -> Optional[str]:
        """Generic helper for making LLM API requests"""
        try:
            log_info(f"[API CALL] Calling {provider_name} API for question generation...")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        result = await response.json()
                        if 'choices' in result and len(result['choices']) > 0:
                            content = result['choices'][0].get('message', {}).get('content', '')
                            if content:
                                log_info(f"[API SUCCESS] {provider_name} API returned response (length: {len(content)})")
                                return content
                    else:
                        error_text = await response.text()
                        log_warning(f"[WARNING] {provider_name} API returned status {response.status}: {error_text}")
            
            return None
        except Exception as e:
            log_warning(f"[WARNING] {provider_name} API call failed: {e}")
            return None
    
    async def _generate_with_gemini(self, prompt: str) -> Optional[str]:
        """Generate response using Gemini model"""
        try:
            if not self.gemini_model:
                return None
            
            log_info("[API CALL] Calling Google Gemini API for question generation...")
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.gemini_model.generate_content(prompt)
            )
            
            if response and response.text:
                log_info(f"[API SUCCESS] Gemini API returned response (length: {len(response.text)})")
                return response.text
            else:
                log_warning("[API WARNING] Gemini API returned empty response")
                return None
                
        except Exception as e:
            error_msg = str(e)
            log_warning(f"[WARNING] Gemini API call failed: {error_msg}")
            return None
    
    async def _validate_response(self, response: str, all_responses: List[Tuple[str, str]], question_type: str) -> str:
        """Validate response quality and check for common issues"""
        # Basic validation: length, content quality
        if len(response) < 20:
            return response
        
        # Check for common AI artifacts
        ai_indicators = [
            "as an AI", "I'm an AI", "I cannot", "I don't have",
            "I'm not able", "I'm a language model"
        ]
        
        response_lower = response.lower()
        for indicator in ai_indicators:
            if indicator in response_lower:
                log_warning(f"[VALIDATION] Response contains AI indicator: {indicator}")
                # If we have other responses, use them
                if len(all_responses) > 1:
                    for llm_name, alt_response in all_responses:
                        if llm_name != self.LLM_GROQ and len(alt_response) > 20:
                            return alt_response
        
        return response
    
    def _mitigate_bias_and_hallucination(
        self, 
        responses: List[Tuple[str, str]]
    ) -> Optional[str]:
        """Compare responses from multiple LLMs to mitigate bias and hallucination"""
        if len(responses) < 2:
            return responses[0][1] if responses else None
        
        # Extract response texts
        # response_texts = [r[1] for r in responses]
        
        # Simple consensus: find the most common key phrases
        # For now, use the longest, most detailed response that doesn't contradict others
        # In a production system, you'd use more sophisticated NLP techniques
        
        # Prefer responses from primary LLMs (Gemini, Groq)
        primary_responses = [r for r in responses if r[0] in [self.LLM_GEMINI, self.LLM_GROQ]]
        if primary_responses:
            # Use the longest primary response
            best = max(primary_responses, key=lambda x: len(x[1]))
            log_info(f"[BIAS_MITIGATION] Selected response from {best[0]} (primary LLM, length: {len(best[1])})")
            return best[1]
        
        # Fallback: use longest response
        best = max(responses, key=lambda x: len(x[1]))
        log_info(f"[BIAS_MITIGATION] Selected longest response from {best[0]} (length: {len(best[1])})")
        return best[1]
    
    async def _build_enhanced_prompt(
        self,
        question_type: str,
        candidate_context: Dict[str, Any],
        job_context: Dict[str, Any],
        previous_questions: List[str] = None,
        previous_responses: List[str] = None,
        question_number: int = 1
    ) -> str:
        """Build enhanced prompt with real-time data integration and SerpApi trends"""
        
        # Build context sections
        candidate_section = self._build_candidate_section(candidate_context)
        
        # Fetch industry trends if needed
        industry_trends = ""
        if question_type == 'advanced':
            job_title = job_context.get('title', 'Position')
            job_skills = job_context.get('required_skills', [])
            log_info(f"[SERPAPI] Fetching industry trends for {job_title} (question #{question_number})")
            industry_trends = await self._get_industry_trends(job_title, job_skills)
            
        job_section = self._build_job_section(job_context, industry_trends)
        
        interview_section = self._build_interview_section(
            question_number, question_type, previous_questions, previous_responses
        )
        
        type_instruction = self._get_type_instruction(
            question_type, candidate_context, job_context, industry_trends
        )
        
        # Create comprehensive prompt
        prompt = f"""
You are a senior {job_context.get('title', 'Position')} professional conducting a natural, conversational interview. Generate a realistic question that a human interviewer would ask based on the candidate's previous responses.

{candidate_section}

{job_section}

{interview_section}

QUESTION TYPE INSTRUCTIONS:
{type_instruction}

CRITICAL INSTRUCTIONS:
- DO NOT repeat ANY of the previous questions listed above
- Build on the candidate's previous responses - ask follow-up questions or explore new areas
- If they mentioned specific projects or technologies, ask for more details about challenges, decisions, or outcomes
- If they gave brief answers, ask for elaboration with specific examples
- Write as a natural, human interviewer would speak
- Make it conversational and relatable
- Reference their specific experience level ({candidate_context.get('experience_years', 0)} years)
- Connect to their skills: {', '.join(candidate_context.get('skills', [])[:4]) if candidate_context.get('skills') else 'their background'}
- For technical questions, reference specific projects or technologies from their resume
- Avoid overly formal or AI-sounding language
- Focus on practical scenarios they would encounter in a {job_context.get('experience_level', 'mid')} level {job_context.get('title', 'Position')} role
- Keep it specific to the {job_context.get('title', 'Position')} role and job requirements
- Use information from their resume, projects, and previous responses to personalize the question

Generate ONE natural interview question that:
1. Is personalized to this candidate's experience, skills, and projects
2. Relates to the specific job requirements: {', '.join(job_context.get('required_skills', [])[:4]) if job_context.get('required_skills') else 'role requirements'}
3. Tests relevant competencies for a {job_context.get('experience_level', 'mid')} level {job_context.get('title', 'Position')} position
4. Encourages detailed, specific responses with examples
5. Is appropriate for question #{question_number} in the interview flow
6. Builds on previous responses (if any) or explores new areas NOT yet covered
7. Does NOT repeat ANY previous questions
8. Incorporates current industry trends and best practices for {job_context.get('title', 'Position')} roles

Return only the question text, no additional formatting or explanations.
"""
        return prompt.strip()

    def _build_candidate_section(self, context: Dict[str, Any]) -> str:
        name = context.get('name', 'Candidate')
        experience = context.get('experience_years', 0)
        skills = context.get('skills', [])
        resume_text = context.get('resume_text', '')[:1000]
        projects = context.get('projects', [])
        
        projects_text = ""
        if projects:
            projects_list = []
            for i, project in enumerate(projects[:5], 1):
                if isinstance(project, dict):
                    p_name = project.get('name', project.get('title', f'Project {i}'))
                    p_desc = project.get('description', project.get('details', ''))
                    projects_list.append(f"- {p_name}: {p_desc[:100]}")
                elif isinstance(project, str):
                    projects_list.append(f"- {project}")
            if projects_list:
                projects_text = f"\nCANDIDATE PROJECTS (use these for technical questions):\n" + "\n".join(projects_list)

        return f"""CANDIDATE BACKGROUND:
- Name: {name}
- Experience: {experience} years in the field
- Skills: {', '.join(skills[:8]) if skills else 'Various technical skills'}
{projects_text}
- Resume Summary: {resume_text[:800] if resume_text else 'Technical professional with relevant experience'}
- Current Date: {datetime.now().strftime('%B %Y')}"""

    def _build_job_section(self, context: Dict[str, Any], trends: str) -> str:
        title = context.get('title', 'Position')
        company = context.get('company', 'Company')
        description = context.get('description', '')
        skills = context.get('required_skills', [])
        level = context.get('experience_level', 'mid')
        
        trends_context = ""
        if trends and trends != "technology":
            trends_context = f"\nCURRENT INDUSTRY TRENDS (from SerpApi search):\n{trends}\n\nUse these trends to ask about recent developments, emerging technologies, or current industry news."

        return f"""POSITION DETAILS:
- Role: {title} at {company}
- Level: {level} level position
- Key Requirements: {', '.join(skills[:8]) if skills else 'Technical expertise'}
- Job Description: {description[:500] if description else 'Technical development role'}
{trends_context}"""

    def _build_interview_section(self, q_num: int, q_type: str, prev_qs: List[str], prev_resps: List[str]) -> str:
        prev_questions_text = ""
        if prev_qs:
            prev_questions_text = f"\nALL Previous questions asked (DO NOT REPEAT ANY OF THESE):\n" + "\n".join([f"{i+1}. {q}" for i, q in enumerate(prev_qs)])
        
        prev_responses_text = ""
        if prev_resps:
            prev_responses_text = f"\nPrevious responses given (use these to build follow-up questions):\n" + "\n".join([f"Q{i+1}: {r[:150]}..." if len(r) > 150 else f"Q{i+1}: {r}" for i, r in enumerate(prev_resps)])

        return f"""INTERVIEW CONTEXT:
- Question #{q_num} of the interview
- Question Type: {q_type}
{prev_questions_text}
{prev_responses_text}"""

    def _get_type_instruction(self, q_type: str, candidate_ctx: Dict[str, Any], job_ctx: Dict[str, Any], trends: str) -> str:
        skills = candidate_ctx.get('skills', [])
        job_title = job_ctx.get('title', 'Position')
        
        instructions = {
            'general': "This is the FIRST question. Ask a simple, welcoming introductory question like 'Tell me about yourself and your professional background' or 'Can you introduce yourself?'. Keep it friendly and open-ended.",
            'behavioral': "Focus on soft skills, teamwork, communication, problem-solving approaches, and past experiences. Ask about specific situations and how they handled them. Reference their resume and job requirements.",
            'theoretical': "Focus on conceptual understanding, best practices, design patterns, system design principles, and theoretical knowledge. Ask about trade-offs, scalability, performance, and architectural decisions. Connect to job requirements.",
            'personal': "Ask about their motivation, career goals, why they're interested in this role/company, what drives them, and how this position aligns with their aspirations. Make it personal and engaging.",
            'practical': f"Focus on hands-on experience, real-world projects from their resume, practical applications of {', '.join(skills[:5]) if skills else 'their skills'}, and how they've solved actual problems. Reference specific technologies and tools.",
            'advanced': f"Ask about NEW technologies, recent industry trends, latest developments in {job_title} field, emerging tools or frameworks, recent news or innovations. Use SerpApi trends if available. Make it challenging and forward-thinking.",
            'coding': "This should be a coding challenge. Generate a problem statement relevant to the job requirements and candidate's skills."
        }
        return instructions.get(q_type, "Ask a relevant question based on the candidate's background and job requirements.")
    
    async def _get_industry_trends(self, job_title: str, job_skills: List[str]) -> str:
        """Get current industry trends using SerpApi"""
        try:
            if not self.serpapi_key:
                log_warning("[WARNING] SerpApi key not configured, skipping industry trends")
                return "technology"
            
            log_info(f"[API CALL] Calling SerpApi for industry trends: {job_title}")
            
            search_query = f"latest trends {job_title} 2025"
            if job_skills:
                search_query += f" {' '.join(job_skills[:2])}"
            
            async with aiohttp.ClientSession() as session:
                params = {
                    'q': search_query,
                    'api_key': self.serpapi_key,
                    'num': 5,
                    'engine': 'google'
                }
                
                async with session.get('https://serpapi.com/search', params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        log_info(f"[API SUCCESS] SerpApi returned {len(data.get('organic_results', []))} results")
                        
                        if 'organic_results' in data and data['organic_results']:
                            trends = []
                            for result in data['organic_results'][:3]:
                                title = result.get('title', '')
                                snippet = result.get('snippet', '')
                                if any(word in (title + ' ' + snippet).lower() for word in ['trend', 'future', '2025', '2024', 'latest', 'new', 'emerging', 'innovation']):
                                    trend_text = title.split(' - ')[0] if ' - ' in title else title
                                    if trend_text:
                                        trends.append(trend_text[:100])
                            
                            if trends:
                                result = ', '.join(trends[:2])
                                log_info(f"[OK] Extracted industry trends: {result[:100]}...")
                                return result
            
            log_warning("[WARNING] No trends found in SerpApi results")
            return "technology"
            
        except Exception as e:
            log_warning(f"[WARNING] Could not fetch industry trends from SerpApi: {e}")
            return "technology"
    
    async def _generate_enhanced_mock_question(
        self,
        question_type: str,
        candidate_context: Dict[str, Any],
        job_context: Dict[str, Any],
        question_number: int,
        previous_questions: List[str] = None,
        previous_responses: List[str] = None
    ) -> str:
        """Generate enhanced mock questions with real-time data, avoiding duplicates"""
        try:
            previous_questions = previous_questions or []
            previous_responses = previous_responses or []
            
            candidate_name = candidate_context.get('name', 'Candidate')
            job_title = job_context.get('title', 'Position')
            job_skills = job_context.get('required_skills', [])
            
            industry_trends = await self._get_industry_trends(job_title, job_skills)
            
            enhanced_questions = self._get_mock_questions_for_type(
                question_type, candidate_context, job_context, industry_trends
            )
            
            # Filter out duplicates
            filtered_questions = []
            for q in enhanced_questions:
                is_duplicate = False
                for prev_q in previous_questions:
                    q_words = set(q.lower().split())
                    prev_q_words = set(prev_q.lower().split())
                    if len(q_words) > 0 and len(prev_q_words) > 0:
                        similarity = len(q_words & prev_q_words) / max(len(q_words), len(prev_q_words))
                        if similarity > 0.7 or q == prev_q:
                            is_duplicate = True
                            break
                if not is_duplicate:
                    filtered_questions.append(q)
            
            if not filtered_questions:
                if previous_responses and len(previous_responses) > 0:
                    last_response = previous_responses[-1]
                    if len(last_response) < 30:
                        filtered_questions = [f"Could you elaborate on that? I'd like to hear more details about your experience with {job_title}."]
                    else:
                        filtered_questions = [f"Based on what you've shared, can you tell me more about your experience with {', '.join(job_skills[:2]) if job_skills else 'relevant technologies'}?"]
                else:
                    filtered_questions = [f"Can you tell me more about your experience in {job_title}?"]
            
            questions_to_use = filtered_questions if filtered_questions else enhanced_questions
            question_index = (question_number - 1) % len(questions_to_use)
            selected_question = questions_to_use[question_index]
            
            if selected_question in previous_questions:
                for q in questions_to_use:
                    if q not in previous_questions:
                        selected_question = q
                        break
            
            log_info(f"[OK] Generated enhanced {question_type} question (avoided {len(enhanced_questions) - len(filtered_questions)} duplicates)")
            return selected_question
            
        except Exception as e:
            log_error(f"[ERROR] Enhanced mock question generation error: {e}")
            return self._get_fallback_question(question_type, question_number)

    def _get_mock_questions_for_type( # nosonar
        self, question_type: str, candidate_context: Dict[str, Any], 
        job_context: Dict[str, Any], industry_trends: str
    ) -> List[str]:
        candidate_name = candidate_context.get('name', 'Candidate')
        candidate_skills = candidate_context.get('skills', [])
        candidate_experience = candidate_context.get('experience_years', 0)
        
        job_title = job_context.get('title', 'Position')
        job_skills = job_context.get('required_skills', [])
        job_level = job_context.get('experience_level', 'mid')
        
        if question_type == 'general':
            return [
                f"Hi {candidate_name}! Welcome to the interview. Let's start with a simple introduction - can you tell me about yourself and your professional background?",
                f"Hi {candidate_name}! Can you introduce yourself and tell me a bit about your experience?",
                f"Welcome, {candidate_name}! Let's begin - can you share a brief overview of your professional journey?",
                f"Hi {candidate_name}! To start, can you tell me about yourself and what brings you here today?"
            ]
        elif question_type == 'behavioral':
            return [
                f"Tell me about a time when you had to learn a new technology quickly for a {job_title} project.",
                f"Describe a situation where you had to work with a difficult team member on a technical project.",
                f"How do you approach mentoring junior developers in your {job_title} role?",
                f"Give me an example of a project where you had to meet a tight deadline while maintaining quality.",
                f"Tell me about a time when you had to explain a complex technical concept to non-technical stakeholders."
            ]
        elif question_type == 'theoretical':
            return [
                f"What are the key design principles you follow when architecting a {job_title} system?",
                f"How would you approach designing a scalable solution for {job_title}?",
                f"What trade-offs would you consider when choosing between different architectural patterns?",
                f"Explain your understanding of best practices in {job_title} development.",
                f"What are the most important factors to consider when designing a {job_title} solution?"
            ]
        elif question_type == 'personal':
            return [
                f"What interests you most about this {job_title} role at {job_context.get('company', 'our company')}?",
                f"What motivates you in your work, and how does that align with this {job_title} position?",
                f"Where do you see yourself in the next few years in your {job_title} career?",
                f"What attracted you to apply for this {job_title} position?",
                f"How do your career goals align with this {job_title} role?"
            ]
        elif question_type == 'practical':
            return [
                f"Can you walk me through a real project from your resume where you used {', '.join(candidate_skills[:2]) if candidate_skills else 'your technical skills'}?",
                "Describe a challenging technical problem you solved recently and the approach you took.",
                f"Based on your {candidate_experience} years of experience, can you share an example of how you've applied {', '.join(job_skills[:2]) if job_skills else 'relevant skills'} in a project?",
                f"Tell me about a project where you had to make a critical technical decision. What was your thought process?",
                "Can you describe a time when you had to optimize a system or process? What was the outcome?"
            ]
        elif question_type == 'advanced':
            trends_context = f"Given the current trends in {industry_trends}" if industry_trends and industry_trends != "technology" else "Given recent developments"
            return [
                f"{trends_context}, what are your thoughts on the latest innovations in {job_title}?",
                f"What emerging technologies or frameworks in {job_title} are you most excited about?",
                f"How do you stay updated with the latest trends and news in {job_title}?",
                f"What do you think are the most significant recent developments in {job_title}?",
                f"Based on current industry trends, how do you see {job_title} evolving in the next 2-3 years?",
                f"What new tools or technologies have you been exploring recently in the {job_title} space?"
            ]
        elif question_type == 'technical':
            return [
                f"Hi {candidate_name}! With your {candidate_experience} years of experience, how would you approach architecting a scalable {job_title} solution?",
                f"I see you have experience with {', '.join(candidate_skills[:3]) if candidate_skills else 'various technologies'}. Can you walk me through how you'd implement a microservices architecture?",
                f"Given the current trends in {industry_trends}, how do you stay updated with the latest {job_title} technologies?",
                f"Describe a challenging technical problem you solved recently and the approach you took.",
                f"How would you ensure code quality and maintainability in a {job_level}-level {job_title} project?"
            ]
        else:
            return [
                f"Hi {candidate_name}! What interests you most about this {job_title} role?",
                f"Based on your {candidate_experience} years of experience, what do you think are the key challenges in {job_title}?",
                f"How do you see the future of {industry_trends} evolving in the next few years?",
                f"What motivates you most in your work, and how does that align with this {job_title} position?",
                f"If you were to start this {job_title} position tomorrow, what would be your first priorities?"
            ]
    
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
        
        response_length = len(response)
        
        if response_length > 200:
            depth_score = min(8, response_length // 50)
            communication_score = 7
        elif response_length > 100:
            depth_score = 5
            communication_score = 6
        else:
            depth_score = 3
            communication_score = 4
        
        specificity_score = 6
        if any(word in response.lower() for word in ['specifically', 'for example', 'in my experience', 'i worked on']):
            specificity_score = 8
        
        relevance_score = 7
        
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
