"""
LLM-Powered Coding Question Generator
Ported from temp-code-service and adapted to run inside coding-service.
"""
import os
import sys
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

# Try to import EnhancedLLMService from text-service (if available)
# In Docker, text-service code is mounted at /app/text-service via docker-compose volumes
# In local dev, it's at ../text-service relative to coding-service
try:
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_file_dir, '..', '..', '..'))
    
    # Try Docker path first (/app/text-service), then local dev path
    docker_text_service_path = os.path.abspath('/app/text-service')
    local_text_service_path = os.path.abspath(os.path.join(project_root, 'backend', 'text-service'))
    
    if os.path.exists(docker_text_service_path):
        text_service_path = docker_text_service_path
    elif os.path.exists(local_text_service_path):
        text_service_path = local_text_service_path
    else:
        text_service_path = local_text_service_path  # Default to local path for error messages
    
    text_service_path = os.path.normpath(text_service_path)
    if text_service_path not in sys.path:
        sys.path.insert(0, text_service_path)
except Exception as path_err:
    # If path calculation fails, use defaults - don't crash module import
    text_service_path = '/app/text-service'  # Default Docker path
    print(f"[WARN] Failed to calculate text-service path: {path_err}. Using default: {text_service_path}", file=sys.stderr)

# Set up temporary logger for import-time logging
# CRITICAL: This must not fail or the entire module won't load
_temp_logger_initialized = False
def _setup_temp_logger():
    global _temp_logger_initialized
    if _temp_logger_initialized:
        return
    try:
        # Try to use the same logger as controller
        from utilities.logger import init_logger
        _temp_logger = init_logger("coding-service")
        def _temp_log_info(msg):
            _temp_logger.info(msg)
        def _temp_log_warning(msg):
            _temp_logger.warning(msg)
        def _temp_log_error(msg):
            _temp_logger.error(msg)
        globals()['_temp_log_info'] = _temp_log_info
        globals()['_temp_log_warning'] = _temp_log_warning
        globals()['_temp_log_error'] = _temp_log_error
    except Exception as logger_err:
        # Fallback logger for import-time errors - must not fail
        def _temp_log_info(msg):
            print(f"[INFO] {msg}", file=sys.stderr)
        def _temp_log_warning(msg):
            print(f"[WARN] {msg}", file=sys.stderr)
        def _temp_log_error(msg):
            print(f"[ERROR] {msg}", file=sys.stderr)
        globals()['_temp_log_info'] = _temp_log_info
        globals()['_temp_log_warning'] = _temp_log_warning
        globals()['_temp_log_error'] = _temp_log_error
        # Log that we're using fallback logger
        _temp_log_warning(f"Using fallback logger (utilities.logger not available: {logger_err})")
    _temp_logger_initialized = True

# Initialize logger - must not raise exceptions
try:
    _setup_temp_logger()
except Exception as e:
    # Absolute fallback - just use print
    def _temp_log_info(msg):
        print(f"[INFO] {msg}", file=sys.stderr)
    def _temp_log_warning(msg):
        print(f"[WARN] {msg}", file=sys.stderr)
    def _temp_log_error(msg):
        print(f"[ERROR] {msg}", file=sys.stderr)
    globals()['_temp_log_info'] = _temp_log_info
    globals()['_temp_log_warning'] = _temp_log_warning
    globals()['_temp_log_error'] = _temp_log_error
    print(f"[CRITICAL] Logger setup failed: {e}. Using print fallback.", file=sys.stderr)

# Initialize EnhancedLLMService
# CRITICAL: This entire block must not raise exceptions that prevent module import
EnhancedLLMService = None
services_path = None

# Use a safe wrapper that won't fail even if logger isn't set up
def _safe_log(level, msg):
    """Safe logging that never raises exceptions"""
    try:
        if level == 'info':
            _temp_log_info(msg)
        elif level == 'warning':
            _temp_log_warning(msg)
        elif level == 'error':
            _temp_log_error(msg)
    except NameError:
        # Logger functions not defined yet - use print
        print(f"[{level.upper()}] {msg}", file=sys.stderr)
    except Exception:
        # Any other error - use print
        print(f"[{level.upper()}] {msg}", file=sys.stderr)

# Wrap in try-except to ensure module can always be imported
try:
    _safe_log('info', f"[INIT] Attempting to import EnhancedLLMService from text-service")
    _safe_log('info', f"[INIT] Text service path: {text_service_path}")
    _safe_log('info', f"[INIT] Text service path exists: {os.path.exists(text_service_path)}")
    _safe_log('info', f"[INIT] Current sys.path entries: {[p for p in sys.path if 'text-service' in p or 'coding-service' in p]}")
    
    # Check if text-service directory exists and get file paths
    services_path = None
    services_init = None
    utils_logger_path = None
    
    if os.path.exists(text_service_path):
        services_path = os.path.join(text_service_path, 'services', 'llm_service.py')
        services_init = os.path.join(text_service_path, 'services', '__init__.py')
        utils_logger_path = os.path.join(text_service_path, 'utils', 'logger.py')
        
        _safe_log('info', f"[INIT] LLM service file exists: {os.path.exists(services_path) if services_path else False}")
        _safe_log('info', f"[INIT] Services __init__.py exists: {os.path.exists(services_init) if services_init else False}")
        _safe_log('info', f"[INIT] Utils logger exists: {os.path.exists(utils_logger_path) if utils_logger_path else False}")
        
        if services_path and os.path.exists(services_path):
            _safe_log('info', f"[INIT] LLM service file path: {services_path}")
    else:
        _safe_log('warning', f"[INIT] Text service path does not exist: {text_service_path}")
        _safe_log('warning', f"[INIT] This might be normal in Docker if services are in separate containers")
    
    # Method 1: Standard import (only if path exists)
    if os.path.exists(text_service_path) and services_path and os.path.exists(services_path):
        try:
            _safe_log('info', f"[INIT] Trying standard import: from services.llm_service import EnhancedLLMService")
            # Ensure text-service is in path
            if text_service_path not in sys.path:
                sys.path.insert(0, text_service_path)
            from services.llm_service import EnhancedLLMService
            _safe_log('info', f"[INIT] Successfully imported EnhancedLLMService using standard import")
        except Exception as e1:
            _safe_log('warning', f"[INIT] Standard import failed: {type(e1).__name__}: {str(e1)}")
            
            # Method 2: Direct file import using importlib
            try:
                _safe_log('info', "[INIT] Trying direct file import using importlib")
                import importlib.util
                
                # Ensure text-service and its utils are in path for dependencies
                utils_path = os.path.join(text_service_path, 'utils')
                if text_service_path not in sys.path:
                    sys.path.insert(0, text_service_path)
                if utils_path not in sys.path:
                    sys.path.insert(0, utils_path)
                
                _safe_log('info', "[INIT] Updated sys.path with text-service paths")
                if utils_logger_path:
                    _safe_log('info', f"[INIT] Checking if utils.logger exists: {os.path.exists(utils_logger_path)}")
                else:
                    _safe_log('warning', f"[INIT] utils_logger_path not set - text-service path may not exist")
                
                # Create a mock utils.logger if it doesn't exist to satisfy the import
                # This allows llm_service to load even if utils.logger has issues
                try:
                    # Try to import utils.logger first
                    if text_service_path not in sys.path:
                        sys.path.insert(0, text_service_path)
                    from utils.logger import log_info as _utils_log_info, log_error as _utils_log_error, log_warning as _utils_log_warning
                    _safe_log('info', "[INIT] Successfully imported utils.logger from text-service")
                except Exception as utils_err:
                    _safe_log('warning', f"[INIT] Could not import utils.logger: {utils_err}")
                    _safe_log('warning', f"[INIT] Creating minimal logger stubs for llm_service")
                    # Create minimal logger stubs
                    import types
                    utils_module = types.ModuleType('utils')
                    logger_module = types.ModuleType('utils.logger')
                    def _stub_log_info(msg):
                        _safe_log('info', f"[LLM-SERVICE] {msg}")
                    def _stub_log_error(msg):
                        _safe_log('error', f"[LLM-SERVICE] {msg}")
                    def _stub_log_warning(msg):
                        _safe_log('warning', f"[LLM-SERVICE] {msg}")
                    logger_module.log_info = _stub_log_info
                    logger_module.log_error = _stub_log_error
                    logger_module.log_warning = _stub_log_warning
                    utils_module.logger = logger_module
                    sys.modules['utils'] = utils_module
                    sys.modules['utils.logger'] = logger_module
                
                spec = importlib.util.spec_from_file_location("llm_service", services_path)
                if spec and spec.loader:
                    llm_module = importlib.util.module_from_spec(spec)
                    # Set __package__ to help with relative imports
                    llm_module.__package__ = "services"
                    llm_module.__file__ = services_path
                    spec.loader.exec_module(llm_module)
                    EnhancedLLMService = llm_module.EnhancedLLMService
                    _safe_log('info', f"[INIT] Successfully imported EnhancedLLMService using importlib")
                else:
                    _safe_log('error', f"[INIT] Failed to create spec from file: {services_path}")
            except Exception as e2:
                _safe_log('error', f"[INIT] Direct file import also failed: {type(e2).__name__}: {str(e2)}")
                import traceback
                _safe_log('error', f"[INIT] Import traceback:\n{traceback.format_exc()}")
                EnhancedLLMService = None
    else:
        _safe_log('warning', f"[INIT] Cannot attempt import - text-service path or llm_service.py not found")
        _safe_log('warning', f"[INIT] In Docker, text-service might be in a separate container")
        _safe_log('warning', f"[INIT] Consider mounting text-service as volume or installing as package")
    
    if EnhancedLLMService is None:
        _safe_log('warning', f"[INIT] All import methods failed. EnhancedLLMService will not be available.")
        _safe_log('warning', f"[INIT] This means LLM-generated questions will not be available.")
        _safe_log('warning', f"[INIT] Check that text-service is accessible and all dependencies are installed.")
        _safe_log('warning', "[INIT] In Docker: ensure text-service code is available in coding-service container")
        
except Exception as e:
    # CRITICAL: Don't let import errors crash the entire service
    # The service should still start even if LLM is unavailable
    EnhancedLLMService = None
    try:
        _safe_log('error', f"[INIT] Unexpected error during import setup: {type(e).__name__}: {str(e)}")
        import traceback
        _safe_log('error', f"[INIT] Import traceback:\n{traceback.format_exc()}")
    except Exception:
        # Even logging failed, just print to stderr - this must never raise
        try:
            print(f"[CRITICAL] Failed to import EnhancedLLMService: {e}", file=sys.stderr)
            print("[CRITICAL] Service will continue without LLM support", file=sys.stderr)
        except:
            pass  # Absolute last resort - do nothing

try:
    from services.leetcode_service import LeetCodeService
except Exception:
    LeetCodeService = None

try:
    from services.web_scraper_service import WebScraperService
except Exception:
    # fallback to local module in coding-service/services
    try:
        from .web_scraper_service import WebScraperService
    except Exception:
        WebScraperService = None

# Use the same logger as the controller for consistent logging
try:
    # Try utilities.logger (same as controller)
    from utilities.logger import init_logger
    _logger = init_logger("coding-service")
    def log_info(msg):
        _logger.info(msg)
    def log_error(msg):
        _logger.error(msg)
    def log_warning(msg):
        _logger.warning(msg)
except Exception:
    # Fallback: try common-service logger
    try:
        import sys
        import os
        # Add common-service to path if needed
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_file_dir, '..', '..', '..'))
        common_service_path = os.path.abspath(os.path.join(project_root, 'backend', 'common-service'))
        if common_service_path not in sys.path:
            sys.path.insert(0, common_service_path)
        from utilities.logger import init_logger
        _logger = init_logger("coding-service")
        def log_info(msg):
            _logger.info(msg)
        def log_error(msg):
            _logger.error(msg)
        def log_warning(msg):
            _logger.warning(msg)
    except Exception:
        # Last resort: use standard logging
        import logging
        _logger = logging.getLogger("coding-service")
        _logger.setLevel(logging.INFO)
        if not _logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s | %(levelname)-7s | [%(name)-20s] | %(message)s')
            handler.setFormatter(formatter)
            _logger.addHandler(handler)
        def log_info(msg):
            _logger.info(msg)
        def log_error(msg):
            _logger.error(msg)
        def log_warning(msg):
            _logger.warning(msg)


class CodingQuestionGenerator:
    """Generates coding questions using LLM with inspiration from coding platforms"""

    def __init__(self):
        # Try to initialize LLM service
        self.llm_service = None
        if EnhancedLLMService:
            try:
                log_info("[INIT] Attempting to initialize EnhancedLLMService...")
                self.llm_service = EnhancedLLMService()
                log_info("[INIT] EnhancedLLMService initialized successfully")
            except Exception as e:
                log_error(f"[INIT] Failed to initialize EnhancedLLMService: {type(e).__name__}: {str(e)}")
                import traceback
                log_error(f"[INIT] Traceback: {traceback.format_exc()}")
                self.llm_service = None
        else:
            log_warning("[INIT] EnhancedLLMService not available (import failed - check logs above for details)")
        
        self.leetcode_service = LeetCodeService() if LeetCodeService else None
        self.web_scraper = WebScraperService() if WebScraperService else None

        self.question_sources = [
            "LeetCode",
            "GeeksforGeeks",
            "HackerRank",
            "CodeSignal",
            "Stack Overflow",
            "Kaggle",
        ]

        log_info(f"[OK] Coding Question Generator initialized")
        log_info(f"[INIT] LLM Service: {'Available' if self.llm_service else 'Not Available'}")
        log_info(f"[INIT] Web Scraper: {'Available' if self.web_scraper else 'Not Available'}")
        if not self.llm_service:
            log_warning(f"[WARN] LLM Service is not available. Questions will use fallback templates.")
        if not self.web_scraper:
            log_warning(f"[WARN] WebScraperService is not available. Scraping from LeetCode/StackOverflow will not work.")

    async def generate_question(
        self,
        resume_data: Dict[str, Any],
        job_description: Dict[str, Any],
        difficulty: str,
        question_number: int,
        previous_questions: List[str] = None,
        interview_id: Optional[str] = None,
        candidate_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        previous_questions = previous_questions or []

        skills = resume_data.get("skills", [])
        experience_years = resume_data.get("experience_years", 0)
        job_skills = job_description.get("required_skills", [])
        job_title = job_description.get("job_title", "Software Engineer")

        # 1. Scrape inspiration
        inspiration = await self._scrape_inspiration(difficulty, skills)

        # 2. Build context
        context = self._build_context(
            skills=skills,
            experience_years=experience_years,
            job_skills=job_skills,
            job_title=job_title,
            difficulty=difficulty,
            question_number=question_number,
            previous_questions=previous_questions,
            inspiration=inspiration,
        )

        # 3. Try LLM generation
        question = await self._attempt_llm_generation(context, difficulty, skills)
        
        if question:
            return question

        # 4. Fallback if LLM fails
        return self._handle_fallback(
            difficulty, skills, resume_data, job_description, 
            question_number, previous_questions, interview_id, candidate_id
        )

    async def _scrape_inspiration(self, difficulty: str, skills: List[str]) -> Dict[str, Any]:
        if not self.web_scraper:
            log_warning(f"[SCRAPER] WebScraperService is not initialized.")
            return {}

        try:
            log_info(f"[SCRAPER] Attempting to scrape questions for difficulty={difficulty}, topics={skills[:3] if skills else []}")
            inspiration = await self.web_scraper.get_question_inspiration(
                difficulty=difficulty, topics=skills[:3] if skills else [], skills=skills
            )
            
            leetcode_count = len(inspiration.get("leetcode", []))
            stackoverflow_count = len(inspiration.get("stackoverflow", []))
            geeksforgeeks_count = len(inspiration.get("geeksforgeeks", []))
            
            log_info(f"[SCRAPER] Scraped results: LeetCode={leetcode_count}, StackOverflow={stackoverflow_count}, GeeksforGeeks={geeksforgeeks_count}")
            
            if leetcode_count == 0 and stackoverflow_count == 0 and geeksforgeeks_count == 0:
                log_warning(f"[SCRAPER] No questions scraped from any source.")
                
            return inspiration
        except Exception as e:
            log_error(f"[SCRAPER] Exception during scraping: {type(e).__name__}: {str(e)}")
            return {}

    async def _attempt_llm_generation(self, context: Dict[str, Any], difficulty: str, skills: List[str]) -> Optional[Dict[str, Any]]:
        if not self.llm_service:
            log_warning("[LLM] LLM service is not initialized/available.")
            return None

        question_prompt = self._create_question_prompt(context)
        llm_response = None
        llm_provider_used = None
        llm_error = None

        # Try LLM providers in order
        providers = [
            ("gemini", self.llm_service._generate_with_gemini),
            ("groq", self.llm_service._generate_with_groq)
        ]

        for provider_name, provider_func in providers:
            try:
                log_info(f"[LLM] Trying {provider_name.capitalize()} API...")
                llm_response = await provider_func(question_prompt)
                if llm_response and len(llm_response.strip()) >= 50:
                    llm_provider_used = provider_name
                    log_info(f"[LLM] SUCCESS: {provider_name.capitalize()} generated question ({len(llm_response)} chars)")
                    break
                else:
                    llm_response = None
                    log_warning(f"[LLM] {provider_name.capitalize()} response too short or empty")
            except Exception as e:
                llm_error = str(e)
                log_warning(f"[LLM] {provider_name.capitalize()} generation failed: {type(e).__name__}: {llm_error}")

        if not llm_response:
            return None

        # Parse response
        log_info(f"[LLM] Parsing LLM response from {llm_provider_used}...")
        question = self._parse_llm_response(llm_response, difficulty, skills)

        if not question.get("test_cases"):
            question["test_cases"] = self._generate_test_cases(question, difficulty)

        question["code_templates"] = self._generate_code_templates(question, skills)
        
        # Remove source field if present
        if question.get("source") in ["geeksforgeeks", "leetcode", "stackoverflow"]:
            question.pop("source", None)
        
        question["_generated_by"] = f"llm_{llm_provider_used}"
        log_info(f"[LLM] Successfully generated and parsed question: {question.get('title', 'Unknown')}")

        return question

    def _handle_fallback(
        self, difficulty: str, skills: List[str], resume_data: Dict[str, Any], 
        job_description: Dict[str, Any], question_number: int, 
        previous_questions: List[str], interview_id: Optional[str], 
        candidate_id: Optional[str]
    ) -> Dict[str, Any]:
        log_warning("[FALLBACK] Using personalized fallback question.")
        
        fallback_question = self._get_fallback_question(
            difficulty, skills, resume_data, job_description, 
            question_number, previous_questions, interview_id, candidate_id
        )
        
        if not fallback_question.get("code_templates"):
            fallback_question["code_templates"] = self._generate_code_templates(fallback_question, skills)
            
        if fallback_question.get("source") == "geeksforgeeks":
            fallback_question.pop("source", None)
            
        fallback_question["_generated_by"] = "fallback"
        log_info(f"[FALLBACK] Generated fallback question: {fallback_question.get('title', 'Unknown')}")
        
        return fallback_question

    def _build_context(self, **kwargs) -> Dict[str, Any]:
        return kwargs

    def _build_question_from_scraped_data(self, inspiration: Dict[str, List[Dict]], difficulty: str, skills: List[str]) -> Optional[Dict[str, Any]]:
        """
        DEPRECATED: This method is no longer used. Scraped data is only used as inspiration for LLM.
        Always returns None to prevent using scraped data directly.
        """
        log_warning("[DEPRECATED] _build_question_from_scraped_data called but is disabled. Scraped data should only be used as LLM inspiration.")
        return None
        # OLD CODE BELOW - DISABLED
        try:
            # Try LeetCode first (usually has structured data)
            leetcode_qs = inspiration.get("leetcode", [])
            if leetcode_qs:
                leetcode_q = leetcode_qs[0]
                return {
                    "title": leetcode_q.get("title", f"{difficulty} Coding Problem"),
                    "description": f"""LeetCode Problem: {leetcode_q.get('title', 'Problem')}
                    
Difficulty: {leetcode_q.get('difficulty', difficulty)}
Topics: {', '.join(t.get('name', '') for t in leetcode_q.get('topicTags', [])[:3]) or 'General'}

This is a real problem from LeetCode. Solve it using any programming language.
Your solution should be optimal in terms of time and space complexity.""",
                    "difficulty": leetcode_q.get("difficulty", difficulty),
                    "examples": [
                        {
                            "input": "LeetCode problem - check platform for examples",
                            "output": "See LeetCode platform",
                            "explanation": f"From LeetCode: {leetcode_q.get('title', '')}"
                        }
                    ],
                    "constraints": [
                        "See the actual problem on LeetCode for constraints",
                        "Acceptance Rate: " + str(leetcode_q.get("acRate", "N/A")) + "%"
                    ],
                    "test_cases": [
                        {"input": "test_case_1", "expected_output": "result_1"},
                        {"input": "test_case_2", "expected_output": "result_2"}
                    ],
                    "hints": [
                        f"This is based on '{leetcode_q.get('title', '')}' from LeetCode",
                        "Think about optimal approach first before coding",
                        f"Problem ID: {leetcode_q.get('frontendQuestionId', 'N/A')}"
                    ],
                    "topics": skills[:3] if skills else [t.get("name", "") for t in leetcode_q.get("topicTags", [])[:3]],
                    "time_limit_minutes": self._get_time_limit(difficulty),
                    "source": "leetcode"
                }
            
            # Try StackOverflow before GeeksforGeeks (since GeeksforGeeks is just a stub)
            so_qs = inspiration.get("stackoverflow", [])
            if so_qs:
                so_q = so_qs[0]
                return {
                    "title": so_q.get("title", f"{difficulty} Coding Problem"),
                    "description": f"""Problem from Stack Overflow (Score: {so_q.get('score', 0)} votes)

Title: {so_q.get('title', 'Problem')}
Tags: {', '.join(so_q.get('tags', [])[:3]) or 'General'}

This problem comes from real Stack Overflow questions.""",
                    "difficulty": difficulty,
                    "examples": [{"input": "Varies", "output": "Varies", "explanation": "See SO post"}],
                    "constraints": ["Based on real StackOverflow questions"],
                    "test_cases": [
                        {"input": "var_1", "expected_output": "expected_1"},
                        {"input": "var_2", "expected_output": "expected_2"}
                    ],
                    "hints": ["Review similar SO answers", "Focus on practical solutions"],
                    "topics": so_q.get("tags", [])[:3] if so_q.get("tags") else skills[:3],
                    "time_limit_minutes": self._get_time_limit(difficulty),
                    "source": "stackoverflow"
                }
            
            # Last resort: GeeksforGeeks (but only if it's not a hardcoded sample)
            geeks_qs = inspiration.get("geeksforgeeks", [])
            if geeks_qs:
                geeks_q = geeks_qs[0]
                # Skip if it's the hardcoded sample (title starts with "Sample")
                if geeks_q.get("title", "").startswith("Sample"):
                    log_warning("[SCRAPER] Skipping hardcoded GeeksforGeeks sample. LeetCode and StackOverflow scraping failed.")
                    return None
                
                return {
                    "title": geeks_q.get("title", f"{difficulty} Coding Problem"),
                    "description": f"""GeeksforGeeks Problem: {geeks_q.get('title', 'Problem')}
                    
Difficulty: {geeks_q.get('difficulty', difficulty)}
Topic: {geeks_q.get('topic', 'General')}

Solve this problem using any programming language.""",
                    "difficulty": geeks_q.get("difficulty", difficulty),
                    "examples": [{"input": "See GeeksforGeeks", "output": "See GeeksforGeeks", "explanation": "Check platform"}],
                    "constraints": ["Consult GeeksforGeeks platform for full details"],
                    "test_cases": [
                        {"input": "test_1", "expected_output": "output_1"},
                        {"input": "test_2", "expected_output": "output_2"}
                    ],
                    "hints": ["Use common data structures", "Think about edge cases"],
                    "topics": [geeks_q.get("topic", "General")] + (skills[:2] if skills else []),
                    "time_limit_minutes": self._get_time_limit(difficulty),
                    "source": "geeksforgeeks"
                }
            
            return None
        except Exception as e:
            log_error(f"Error building question from scraped data: {e}")
            return None
        # END OF OLD CODE

    def _create_question_prompt(self, context: Dict[str, Any]) -> str:
        skills_str = ", ".join(context.get("skills", [])[:10])
        job_skills_str = ", ".join(context.get("job_skills", [])[:10])
        prev_questions_str = (
            "\n".join([f"- {q}" for q in context.get("previous_questions", [])]) or "None"
        )

        inspiration_text = ""
        if context.get("inspiration"):
            # Include LeetCode inspiration
            leetcode_qs = context["inspiration"].get("leetcode", [])[:3]
            if leetcode_qs:
                inspiration_text += "\n\nInspiration from LeetCode:\n"
                for q in leetcode_qs:
                    tags = ", ".join([t.get('name', '') for t in q.get('topicTags', [])[:3]])
                    inspiration_text += f"- {q.get('title', '')} ({q.get('difficulty', '')}) - Topics: {tags}\n"
                    if q.get('acRate'):
                        inspiration_text += f"  Acceptance Rate: {q.get('acRate')}%\n"
            
            # Include StackOverflow inspiration
            so_qs = context["inspiration"].get("stackoverflow", [])[:3]
            if so_qs:
                inspiration_text += "\n\nInspiration from StackOverflow:\n"
                for q in so_qs:
                    tags = ", ".join(q.get('tags', [])[:3])
                    score = q.get('score', 0)
                    inspiration_text += f"- {q.get('title', '')} (Score: {score} votes) - Tags: {tags}\n"
            
            # Include GeeksforGeeks if available (but note it's limited)
            geeks_qs = context["inspiration"].get("geeksforgeeks", [])[:2]
            if geeks_qs and not any(q.get('title', '').startswith('Sample') for q in geeks_qs):
                inspiration_text += "\n\nInspiration from GeeksforGeeks:\n"
                for q in geeks_qs:
                    inspiration_text += f"- {q.get('title', '')} ({q.get('difficulty', '')}) - Topic: {q.get('topic', '')}\n"

        prompt = f"""Generate a {context.get('difficulty')} difficulty coding interview question for a {context.get('job_title')} position.

CANDIDATE PROFILE:
- Skills: {skills_str}
- Experience: {context.get('experience_years')} years
- Job Required Skills: {job_skills_str}

PREVIOUS QUESTIONS (avoid similar topics):
{prev_questions_str}
{inspiration_text}

QUESTION REQUIREMENTS:
1. Should test programming fundamentals relevant to {context.get('job_title')}
2. Difficulty: {context.get('difficulty')}
3. Should be inspired by problems from: LeetCode, GeeksforGeeks, Stack Overflow, HackerRank, CodeSignal, Kaggle
4. IMPORTANT: The question must be LANGUAGE-AGNOSTIC. It should be solvable in Python, Java, JavaScript, C++, C#, or any programming language.
5. Must include:
   - Clear problem statement (language-independent)
   - Input/output examples (at least 2) with clear data types
   - Constraints
   - Expected time/space complexity hints
6. If inspiration questions are provided above, use them as reference but create a NEW, unique problem inspired by their style and difficulty

REQUIRED JSON FORMAT:
{{
    "title": "Question Title",
    "description": "Detailed problem description",
    "difficulty": "{context.get('difficulty')}",
    "examples": [
        {{"input": "...", "output": "...", "explanation": "..."}},
        {{"input": "...", "output": "...", "explanation": "..."}}
    ],
    "constraints": ["constraint1", "constraint2"],
    "test_cases": [
        {{"input": "...", "expected_output": "..."}},
        {{"input": "...", "expected_output": "..."}}
    ],
    "hints": ["hint1", "hint2"],
    "topics": ["topic1", "topic2"]
}}

Return ONLY valid JSON, no additional text or markdown formatting."""

        return prompt

    def _parse_llm_response(self, llm_response: str, difficulty: str, skills: List[str]) -> Dict[str, Any]:
        import re

        try:
            json_match = re.search(r"\{.*\}", llm_response, re.DOTALL)
            if json_match:
                question_data = json.loads(json_match.group())
            else:
                question_data = {"title": self._extract_title(llm_response), "description": llm_response, "difficulty": difficulty}
        except Exception:
            question_data = {"title": f"Coding Challenge ({difficulty})", "description": llm_response, "difficulty": difficulty}

        examples = self._serialize_json_fields(question_data.get("examples", []), ["input", "output"])
        test_cases = self._serialize_json_fields(question_data.get("test_cases", []), ["input", "expected_output"])

        question = {
            "title": question_data.get("title", f"Coding Question ({difficulty})"),
            "description": question_data.get("description", llm_response),
            "difficulty": question_data.get("difficulty", difficulty),
            "examples": examples,
            "constraints": question_data.get("constraints", []),
            "test_cases": test_cases,
            "hints": question_data.get("hints", []),
            "topics": question_data.get("topics", skills[:3] if skills else []),
            "time_limit_minutes": question_data.get("time_limit_minutes", self._get_time_limit(difficulty)),
        }

        return question

    def _serialize_json_fields(self, items: List[Any], keys: List[str]) -> List[Any]:
        """Helper to serialize dict/list fields in a list of dictionaries"""
        processed_items = []
        for item in items:
            if isinstance(item, dict):
                processed_item = item.copy()
                for key in keys:
                    val = processed_item.get(key, "")
                    if isinstance(val, (dict, list)):
                        processed_item[key] = json.dumps(val)
                processed_items.append(processed_item)
            else:
                processed_items.append(item)
        return processed_items

    def _extract_title(self, text: str) -> str:
        lines = text.split("\n")
        for line in lines[:5]:
            if line.strip() and len(line.strip()) < 100:
                return line.strip()
        return "Coding Challenge"

    def _generate_test_cases(self, question: Dict[str, Any], difficulty: str) -> List[Dict[str, Any]]:
        if difficulty == "easy":
            return [{"input": "simple case", "expected_output": "expected result"}, {"input": "edge case", "expected_output": "edge result"}]
        elif difficulty == "medium":
            return [
                {"input": "standard case", "expected_output": "standard result"},
                {"input": "edge case 1", "expected_output": "edge result 1"},
                {"input": "edge case 2", "expected_output": "edge result 2"},
            ]
        else:
            return [
                {"input": "complex case", "expected_output": "complex result"},
                {"input": "edge case 1", "expected_output": "edge result 1"},
                {"input": "edge case 2", "expected_output": "edge result 2"},
                {"input": "performance case", "expected_output": "performance result"},
            ]

    def _generate_code_templates(self, question: Dict[str, Any], skills: List[str]) -> Dict[str, str]:
        templates = {}
        preferred_languages = []
        if any("python" in s.lower() for s in skills):
            preferred_languages.append("python")
        if any("java" in s.lower() for s in skills):
            preferred_languages.append("java")
        if any("javascript" in s.lower() or "js" in s.lower() for s in skills):
            preferred_languages.append("javascript")
        if any("c++" in s.lower() or "cpp" in s.lower() or "cplusplus" in s.lower() for s in skills):
            preferred_languages.append("cpp")
        if any("c#" in s.lower() or "csharp" in s.lower() or ".net" in s.lower() for s in skills):
            preferred_languages.append("csharp")

        if not preferred_languages:
            preferred_languages = ["python", "java", "javascript", "cpp", "csharp"]

        all_supported = ["python", "java", "javascript", "cpp", "csharp"]
        preferred_languages = list(set(preferred_languages + all_supported))

        for lang in preferred_languages:
            if lang == "python":
                templates["python"] = f"""def solution():\n    # {question.get('title', 'Solution')}\n    # Write your solution here\n    pass"""
            elif lang == "java":
                templates["java"] = f"""public class Solution {{\n    public void solution() {{\n        // {question.get('title', 'Solution')}\n        // Write your solution here\n    }}\n}}"""
            elif lang == "javascript":
                templates["javascript"] = f"""function solution() {{\n    // {question.get('title', 'Solution')}\n    // Write your solution here\n}}"""
            elif lang == "cpp":
                templates["cpp"] = f"""#include <iostream>\n#include <vector>\nusing namespace std;\n\nclass Solution {{\npublic:\n    void solution() {{\n        // {question.get('title', 'Solution')}\n        // Write your solution here\n    }}\n}};\n\nint main() {{\n    Solution sol;\n    sol.solution();\n    return 0;\n}}"""
            elif lang == "csharp":
                templates["csharp"] = f"""using System;\n\npublic class Solution {{\n    public void solution() {{\n        // {question.get('title', 'Solution')}\n        // Write your solution here\n    }}\n}}\n\nclass Program {{\n    static void Main() {{\n        Solution sol = new Solution();\n        sol.solution();\n    }}\n}}"""

        return templates

    def _get_time_limit(self, difficulty: str) -> int:
        limits = {"easy": 15, "medium": 30, "hard": 45}
        return limits.get(difficulty, 30)

    def _get_fallback_question(self, difficulty: str, skills: List[str] = None, resume_data: Dict[str, Any] = None, job_description: Dict[str, Any] = None, question_number: int = 1, previous_questions: List[str] = None, interview_id: Optional[str] = None, candidate_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a personalized fallback question when LLM is unavailable.
        Uses resume data to create more relevant questions with actual problem statements.
        """
        skills = skills or []
        resume_data = resume_data or {}
        job_description = job_description or {}
        previous_questions = previous_questions or []
        
        # Extract additional context
        experience_years = resume_data.get("experience_years", 0)
        job_skills = job_description.get("required_skills", [])
        
        # Determine primary skill/topic
        primary_skill = None
        if skills:
            primary_skill = skills[0]
        elif job_skills:
            primary_skill = job_skills[0]
        
        # Get a concrete problem based on difficulty, with variation based on interview/candidate
        problem_template = self._get_problem_template(
            difficulty, primary_skill, experience_years, question_number, 
            previous_questions, interview_id, candidate_id, resume_data
        )
        
        return self._enrich_problem_template(
            problem_template, difficulty, skills, job_skills, experience_years
        )

    def _enrich_problem_template( # nosonar
        self, problem_template: Dict[str, Any], difficulty: str, 
        skills: List[str], job_skills: List[str], experience_years: float
    ) -> Dict[str, Any]:
        title = problem_template["title"]
        description = problem_template["description"]
        test_cases = problem_template["test_cases"]
        
        # Add relevant constraints
        constraints = problem_template.get("constraints", [])
        if difficulty in ["medium", "hard"]:
            if "Time complexity should be optimal" not in constraints:
                constraints.append("Time complexity should be optimal")
        if experience_years >= 5:
            if "Consider edge cases and error handling" not in constraints:
                constraints.append("Consider edge cases and error handling")
        
        # Generate hints based on difficulty
        hints = problem_template.get("hints", [])
        if not hints:
            if difficulty == "easy":
                hints.append("Start with a brute-force approach, then optimize")
            elif difficulty == "medium":
                hints.append("Consider using common data structures (arrays, hash maps, etc.)")
            else:
                hints.append("Think about the problem space and optimal algorithms")
        
        # Generate examples if provided
        examples = problem_template.get("examples", [])
        
        # Generate code templates for the fallback question
        question_dict = {
            "title": title,
            "description": description,
            "difficulty": difficulty,
            "examples": examples if examples else [],
            "constraints": constraints if constraints else [],
            "test_cases": test_cases if test_cases else [],
            "hints": hints if hints else [],
            "topics": skills[:3] if skills else (job_skills[:3] if job_skills else []),
            "time_limit_minutes": self._get_time_limit(difficulty),
        }
        
        # Add code templates
        question_dict["code_templates"] = self._generate_code_templates(question_dict, skills)
        
        return question_dict
    
    CONSTRAINT_NUMBER_RANGE = "-10^9 <= each number <= 10^9"

    def _get_problem_template(self, difficulty: str, primary_skill: str = None, experience_years: float = 0, question_number: int = 1, previous_questions: List[str] = None, interview_id: Optional[str] = None, candidate_id: Optional[str] = None, resume_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get a concrete coding problem template based on difficulty and context.
        """
        previous_questions = previous_questions or []
        resume_data = resume_data or {}
        
        # Normalize primary skill for problem selection
        skill_category = self._determine_skill_category(primary_skill)
        
        # Calculate variation seed
        variation_seed = self._calculate_variation_seed(
            interview_id, candidate_id, resume_data, question_number, 
            primary_skill, experience_years, previous_questions
        )
        
        if difficulty == "easy":
            return self._get_easy_problem(variation_seed)
        elif difficulty == "medium":
            return self._get_medium_problem(variation_seed, skill_category, experience_years)
        else:
            return self._get_hard_problem(variation_seed)

    def _determine_skill_category(self, primary_skill: Optional[str]) -> Optional[str]:
        if not primary_skill:
            return None
        skill_lower = primary_skill.lower()
        if any(lang in skill_lower for lang in ["python", "java", "javascript", "go", "c#", "c++"]):
            return "general"
        elif any(term in skill_lower for term in ["data", "sql", "database"]):
            return "data"
        elif any(term in skill_lower for term in ["api", "rest", "web", "flask", "spring"]):
            return "api"
        elif any(term in skill_lower for term in ["machine", "ai", "ml"]):
            return "algorithm"
        return None

    def _calculate_variation_seed(
        self, interview_id, candidate_id, resume_data, question_number, 
        primary_skill, experience_years, previous_questions
    ) -> int:
        if interview_id:
            return abs(hash(interview_id)) % 10000
        elif candidate_id:
            return abs(hash(f"{candidate_id}_{question_number}")) % 10000
        else:
            resume_name = resume_data.get("name", "")
            resume_email = resume_data.get("email", "")
            all_skills_str = ",".join(sorted(resume_data.get("skills", [])[:5])) if resume_data.get("skills") else "general"
            
            seed_components = [
                str(question_number),
                primary_skill or "general",
                str(experience_years),
                all_skills_str,
                resume_name or "",
                resume_email or "",
                str(hash(tuple(previous_questions)) if previous_questions else 0)
            ]
            
            seed_string = "_".join(filter(None, seed_components))
            return abs(hash(seed_string)) % 10000

    def _get_easy_problem(self, variation_seed: int) -> Dict[str, Any]:
        easy_problems = [
            {
                "title": "Array Sum Problem",
                "description": """Given an array of integers, write a function that returns the sum of all elements in the array.

Example:
- Input: [1, 2, 3, 4, 5]
- Output: 15

Edge Cases:
- Empty array should return 0
- Array with negative numbers should handle them correctly
- Array with a single element should return that element""",
                "test_cases": [
                    {"input": "[1, 2, 3, 4, 5]", "expected_output": "15"},
                    {"input": "[]", "expected_output": "0"},
                    {"input": "[10, 20, 30]", "expected_output": "60"},
                    {"input": "[-5, 0, 5]", "expected_output": "0"}
                ],
                "constraints": [
                    "Array can contain positive and negative integers",
                    "Array can be empty",
                    "Array can have up to 10^5 elements"
                ],
                "hints": [
                    "Iterate through the array and accumulate the sum",
                    "Handle the empty array case explicitly"
                ],
                "examples": [
                    {
                        "input": "[1, 2, 3]",
                        "output": "6",
                        "explanation": "Sum of all elements: 1 + 2 + 3 = 6"
                    }
                ]
            },
            {
                "title": "Find Maximum in Array",
                "description": """Given an array of integers, write a function that returns the maximum value in the array.

Example:
- Input: [3, 7, 2, 9, 1]
- Output: 9

Edge Cases:
- Array with negative numbers should work correctly
- Array with a single element should return that element
- All elements being the same should return that value""",
                "test_cases": [
                    {"input": "[3, 7, 2, 9, 1]", "expected_output": "9"},
                    {"input": "[-5, -2, -8, -1]", "expected_output": "-1"},
                    {"input": "[5]", "expected_output": "5"},
                    {"input": "[10, 10, 10]", "expected_output": "10"}
                ],
                "constraints": [
                    "Array can contain positive and negative integers",
                    "Array is not empty",
                    "Array can have up to 10^5 elements"
                ],
                "hints": [
                    "Iterate through the array and keep track of the maximum seen so far",
                    "Initialize with the first element"
                ],
                "examples": [
                    {
                        "input": "[3, 7, 2, 9, 1]",
                        "output": "9",
                        "explanation": "The maximum value in the array is 9"
                    }
                ]
            },
            {
                "title": "Count Even Numbers",
                "description": """Given an array of integers, write a function that returns the count of even numbers in the array.

Example:
- Input: [1, 2, 3, 4, 5, 6]
- Output: 3

Edge Cases:
- Array with no even numbers should return 0
- Array with all even numbers should return the array length
- Empty array should return 0""",
                "test_cases": [
                    {"input": "[1, 2, 3, 4, 5, 6]", "expected_output": "3"},
                    {"input": "[1, 3, 5, 7]", "expected_output": "0"},
                    {"input": "[2, 4, 6, 8]", "expected_output": "4"},
                    {"input": "[]", "expected_output": "0"}
                ],
                "constraints": [
                    "Array can contain positive and negative integers",
                    "Array can be empty",
                    "Array can have up to 10^5 elements"
                ],
                "hints": [
                    "Use modulo operator (%) to check if a number is even",
                    "Increment a counter for each even number found"
                ],
                "examples": [
                    {
                        "input": "[1, 2, 3, 4, 5, 6]",
                        "output": "3",
                        "explanation": "There are 3 even numbers: 2, 4, and 6"
                    }
                ]
            }
        ]
        return easy_problems[variation_seed % len(easy_problems)]

    def _get_medium_problem(self, variation_seed: int, skill_category: Optional[str], experience_years: float) -> Dict[str, Any]:
        medium_problems = [
            {
                "title": "Find Two Numbers Sum to Target",
                "description": """Given an array of integers and a target sum, find the indices of two numbers that add up to the target.

You may assume that each input has exactly one solution, and you may not use the same element twice. You can return the answer in any order.

Example:
- Input: nums = [2, 7, 11, 15], target = 9
- Output: [0, 1]
- Explanation: nums[0] + nums[1] = 2 + 7 = 9""",
                "test_cases": [
                    {"input": "[2, 7, 11, 15], 9", "expected_output": "[0, 1]"}, # nosonar
                    {"input": "[3, 2, 4], 6", "expected_output": "[1, 2]"},
                    {"input": "[3, 3], 6", "expected_output": "[0, 1]"},
                    {"input": "[1, 5, 3, 2], 4", "expected_output": "[0, 3]"}
                ],
                "constraints": [
                    "2 <= array length <= 10^4",
                    self.CONSTRAINT_NUMBER_RANGE,
                    "-10^9 <= target <= 10^9",
                    "Only one valid answer exists",
                    "Time complexity should be optimal"
                ],
                "hints": [
                    "Consider using a hash map to store seen numbers",
                    "For each number, check if its complement (target - number) exists in the map",
                    "This allows O(n) time complexity instead of O(n²)"
                ],
                "examples": [
                    {
                        "input": "nums = [2, 7, 11, 15], target = 9",
                        "output": "[0, 1]",
                        "explanation": "Because nums[0] + nums[1] == 9, we return [0, 1]"
                    },
                    {
                        "input": "nums = [3, 2, 4], target = 6",
                        "output": "[1, 2]",
                        "explanation": "nums[1] + nums[2] = 2 + 4 = 6"
                    }
                ]
            },
            {
                "title": "Valid Parentheses",
                "description": """Given a string containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid.

An input string is valid if:
1. Open brackets must be closed by the same type of brackets
2. Open brackets must be closed in the correct order
3. Every close bracket has a corresponding open bracket of the same type

Example:
- Input: "()[]{}"
- Output: true

- Input: "(]"
- Output: false""",
                "test_cases": [
                    {"input": '"()"', "expected_output": "true"},
                    {"input": '"()[]{}"', "expected_output": "true"},
                    {"input": '"(]"', "expected_output": "false"},
                    {"input": '"([)]"', "expected_output": "false"},
                    {"input": '"{[]}"', "expected_output": "true"}
                ],
                "constraints": [
                    "1 <= string length <= 10^4",
                    "String consists of parentheses only: '()[]{}'"
                ],
                "hints": [
                    "Use a stack data structure",
                    "Push opening brackets, pop when encountering matching closing brackets",
                    "Check if stack is empty at the end"
                ],
                "examples": [
                    {
                        "input": '"()"',
                        "output": "true",
                        "explanation": "Open bracket '(' is closed by ')' in correct order"
                    },
                    {
                        "input": '"(]"',
                        "output": "false",
                        "explanation": "Open bracket '(' is closed by ']' which is incorrect"
                    }
                ]
            },
            {
                "title": "Reverse String",
                "description": """Given a string, write a function that returns the string reversed.

Example:
- Input: "hello"
- Output: "olleh"

Requirements:
- Reverse the characters in the string
- Handle empty strings
- Preserve character case""",
                "test_cases": [
                    {"input": '"hello"', "expected_output": '"olleh"'},
                    {"input": '"world"', "expected_output": '"dlrow"'},
                    {"input": '""', "expected_output": '""'},
                    {"input": '"A"', "expected_output": '"A"'}
                ],
                "constraints": [
                    "0 <= string length <= 10^5",
                    "String contains only printable ASCII characters"
                ],
                "hints": [
                    "Use two pointers starting from both ends",
                    "Swap characters until pointers meet",
                    "Or use built-in reverse if allowed"
                ],
                "examples": [
                    {
                        "input": '"hello"',
                        "output": '"olleh"',
                        "explanation": "Characters reversed: h-e-l-l-o becomes o-l-l-e-h"
                    }
                ]
            },
            {
                "title": "Contains Duplicate",
                "description": """Given an array of integers, determine if any value appears at least twice in the array.

Return true if any value appears at least twice, and false if every element is distinct.

Example:
- Input: [1, 2, 3, 1]
- Output: true

- Input: [1, 2, 3, 4]
- Output: false""",
                "test_cases": [
                    {"input": "[1, 2, 3, 1]", "expected_output": "true"},
                    {"input": "[1, 2, 3, 4]", "expected_output": "false"},
                    {"input": "[1, 1, 1, 3, 3, 4, 3, 2, 4, 2]", "expected_output": "true"},
                    {"input": "[1]", "expected_output": "false"}
                ],
                "constraints": [
                    "1 <= array length <= 10^5",
                    self.CONSTRAINT_NUMBER_RANGE
                ],
                "hints": [
                    "Use a hash set to track seen numbers",
                    "If a number is already in the set, return true",
                    "Time complexity O(n), space complexity O(n)"
                ],
                "examples": [
                    {
                        "input": "[1, 2, 3, 1]",
                        "output": "true",
                        "explanation": "The number 1 appears twice in the array"
                    }
                ]
            }
        ]
        
        if skill_category == "data" or experience_years >= 5:
            preferred_problems = [0, 3]
            selected_index = preferred_problems[variation_seed % 2]
        else:
            selected_index = variation_seed % len(medium_problems)
        
        return medium_problems[selected_index]

    def _get_hard_problem(self, variation_seed: int) -> Dict[str, Any]:
        hard_problems = [
            {
                "title": "Longest Substring Without Repeating Characters",
                "description": """Given a string, find the length of the longest substring without repeating characters.

Example:
- Input: "abcabcbb"
- Output: 3
- Explanation: The answer is "abc", with the length of 3

- Input: "bbbbb"
- Output: 1
- Explanation: The answer is "b", with the length of 1""",
                "test_cases": [
                    {"input": '"abcabcbb"', "expected_output": "3"},
                    {"input": '"bbbbb"', "expected_output": "1"},
                    {"input": '"pwwkew"', "expected_output": "3"},
                    {"input": '""', "expected_output": "0"},
                    {"input": '"dvdf"', "expected_output": "3"}
                ],
                "constraints": [
                    "0 <= string length <= 5 * 10^4",
                    "String consists of English letters, digits, symbols and spaces",
                    "Time complexity should be optimal (O(n) expected)"
                ],
                "hints": [
                    "Use sliding window technique with two pointers",
                    "Use a hash set or hash map to track characters in current window",
                    "Move left pointer when duplicate is found, expand right pointer otherwise"
                ],
                "examples": [
                    {
                        "input": '"abcabcbb"',
                        "output": "3",
                        "explanation": "Longest substring without repeating characters is 'abc'"
                    },
                    {
                        "input": '"pwwkew"',
                        "output": "3",
                        "explanation": "The answer is 'wke', not 'pwke' because 'w' repeats"
                    }
                ]
            },
            {
                "title": "Two Sum - All Pairs",
                "description": """Given an array of integers and a target sum, find ALL unique pairs of numbers that add up to the target.

Note: This is different from the classic Two Sum problem. You need to find all pairs, not just one.

Example:
- Input: nums = [2, 7, 11, 15, 3, 6], target = 9
- Output: [[2, 7], [3, 6]]

Requirements:
- Return all unique pairs
- Each pair should be sorted [smaller, larger]
- No duplicate pairs
- Pairs should be sorted lexicographically""",
                "test_cases": [
                    {"input": "[2, 7, 11, 15, 3, 6], 9", "expected_output": "[[2, 7], [3, 6]]"},
                    {"input": "[1, 4, 2, 3, 0, 5], 7", "expected_output": "[[2, 5], [3, 4]]"},
                    {"input": "[1, 1, 1], 2", "expected_output": "[[1, 1]]"},
                    {"input": "[1, 2, 3], 10", "expected_output": "[]"}
                ],
                "constraints": [
                    "1 <= array length <= 10^4",
                    self.CONSTRAINT_NUMBER_RANGE,
                    "-10^9 <= target <= 10^9"
                ],
                "hints": [
                    "Use a hash map to store complements",
                    "Be careful about duplicate pairs",
                    "Sort the result to ensure consistency"
                ],
                "examples": [
                    {
                        "input": "nums = [2, 7, 11, 15, 3, 6], target = 9",
                        "output": "[[2, 7], [3, 6]]",
                        "explanation": "Pairs that sum to 9: (2,7) and (3,6)"
                    }
                ]
            },
            {
                "title": "Group Anagrams",
                "description": """Given an array of strings, group the anagrams together. An anagram is a word formed by rearranging the letters of another word.

Example:
- Input: ["eat", "tea", "tan", "ate", "nat", "bat"]
- Output: [["eat", "tea", "ate"], ["tan", "nat"], ["bat"]]

Note: All inputs are lowercase. The order of output does not matter.""",
                "test_cases": [
                    {"input": '["eat", "tea", "tan", "ate", "nat", "bat"]', "expected_output": '[["eat", "tea", "ate"], ["tan", "nat"], ["bat"]]'},
                    {"input": '[""]', "expected_output": '[[""]]'},
                    {"input": '["a"]', "expected_output": '[["a"]]'}
                ],
                "constraints": [
                    "1 <= array length <= 10^4",
                    "0 <= string length <= 100",
                    "Strings contain only lowercase English letters"
                ],
                "hints": [
                    "Use sorted string as key for grouping",
                    "Use a hash map where key is sorted string, value is list of anagrams",
                    "Time complexity O(n*k*log(k)) where k is average string length"
                ],
                "examples": [
                    {
                        "input": '["eat", "tea", "tan"]',
                        "output": '[["eat", "tea"], ["tan"]]',
                        "explanation": "eat and tea are anagrams, tan is separate"
                    }
                ]
            }
        ]
        
        return hard_problems[variation_seed % len(hard_problems)]
    
    def _generate_personalized_test_cases(self, difficulty: str, primary_skill: str = None, experience_years: float = 0) -> List[Dict[str, Any]]:
        """
        Generate more realistic test cases based on difficulty and context.
        """
        if difficulty == "easy":
            return [
                {"input": "5", "expected_output": "15"},  # Example: sum of first n numbers
                {"input": "0", "expected_output": "0"},   # Edge case
                {"input": "10", "expected_output": "55"}
            ]
        elif difficulty == "medium":
            # More complex test cases
            test_cases = [
                {"input": "[1, 2, 3, 4, 5]", "expected_output": "15"},  # Example: array sum
                {"input": "[]", "expected_output": "0"},  # Empty case
                {"input": "[10, 20, 30]", "expected_output": "60"}
            ]
            if experience_years >= 3:
                test_cases.append({"input": "[-5, 0, 5]", "expected_output": "0"})  # Negative numbers
            return test_cases
        else:  # hard
            test_cases = [
                {"input": "1000", "expected_output": "500500"},  # Large input
                {"input": "1", "expected_output": "1"},  # Base case
                {"input": "100", "expected_output": "5050"},  # Medium case
            ]
            if experience_years >= 5:
                test_cases.append({"input": "1000000", "expected_output": "500000500000"})  # Performance test
            return test_cases
