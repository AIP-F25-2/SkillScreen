"""
LLM-Powered Coding Question Generator
Generates coding questions based on resume, job description, and difficulty level
Uses multiple LLMs with fallback mechanism
"""

import os
import sys
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add text-service to path for LLM service - MUST be first
current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_file_dir, '..', '..', '..'))
text_service_path = os.path.abspath(os.path.join(project_root, 'backend', 'text-service'))

# Normalize and add to path
text_service_path = os.path.normpath(text_service_path)
if text_service_path not in sys.path:
    sys.path.insert(0, text_service_path)

# Import from text-service (these are in text-service/services/)
from services.llm_service import EnhancedLLMService
from services.leetcode_service import LeetCodeService

# Import local services (these are in coding-interview-service/services/)
# Need to get the coding-interview-service path
coding_service_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if coding_service_dir not in sys.path:
    sys.path.insert(0, coding_service_dir)

# Import local web_scraper_service - handle both normal and importlib loading
try:
    from services.web_scraper_service import WebScraperService
except ImportError:
    # Fallback for when loaded via importlib - use direct file import
    web_scraper_path = os.path.join(coding_service_dir, 'services', 'web_scraper_service.py')
    if os.path.exists(web_scraper_path):
        import importlib.util
        spec = importlib.util.spec_from_file_location("web_scraper_service", web_scraper_path)
        web_scraper_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(web_scraper_module)
        WebScraperService = web_scraper_module.WebScraperService
    else:
        raise ImportError(f"Could not find web_scraper_service.py at {web_scraper_path}")
from utils.logger import log_info, log_error, log_warning

class CodingQuestionGenerator:
    """Generates coding questions using LLM with inspiration from coding platforms"""
    
    def __init__(self):
        self.llm_service = EnhancedLLMService()
        self.leetcode_service = LeetCodeService()
        self.web_scraper = WebScraperService()
        
        # Question sources for inspiration
        self.question_sources = [
            "LeetCode",
            "GeeksforGeeks",
            "HackerRank",
            "CodeSignal",
            "Stack Overflow",
            "Kaggle"
        ]
        
        log_info("[OK] Coding Question Generator initialized")
    
    async def generate_question(
        self,
        resume_data: Dict[str, Any],
        job_description: Dict[str, Any],
        difficulty: str,
        question_number: int,
        previous_questions: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a coding question using LLM
        
        Args:
            resume_data: Parsed resume information
            job_description: Job description and requirements
            difficulty: Difficulty level (easy, medium, hard)
            question_number: Current question number
            previous_questions: List of previous question titles to avoid repetition
        
        Returns:
            Generated question with title, description, test cases, etc.
        """
        try:
            previous_questions = previous_questions or []
            
            # Extract key information
            skills = resume_data.get("skills", [])
            experience_years = resume_data.get("experience_years", 0)
            job_skills = job_description.get("required_skills", [])
            job_title = job_description.get("job_title", "Software Engineer")
            
            # Get question inspiration from web sources
            inspiration = await self.web_scraper.get_question_inspiration(
                difficulty=difficulty,
                topics=skills[:3] if skills else [],
                skills=skills
            )
            
            # Build context for LLM
            context = self._build_context(
                skills=skills,
                experience_years=experience_years,
                job_skills=job_skills,
                job_title=job_title,
                difficulty=difficulty,
                question_number=question_number,
                previous_questions=previous_questions,
                inspiration=inspiration
            )
            
            # Generate question using LLM
            question_prompt = self._create_question_prompt(context)
            
            log_info(f"[QUESTION GEN] Generating question {question_number} (difficulty: {difficulty})")
            
            # Create prompt for question generation
            question_prompt = self._create_question_prompt(context)
            
            # Use LLM to generate question
            llm_response = await self.llm_service._generate_with_gemini(question_prompt)
            
            # If Gemini fails, try fallback
            if not llm_response or len(llm_response.strip()) < 50:
                llm_response = await self.llm_service._generate_with_groq(question_prompt)
            
            if not llm_response or len(llm_response.strip()) < 50:
                llm_response = await self.llm_service._generate_with_mistral(question_prompt)
            
            # Parse LLM response and structure question
            question = self._parse_llm_response(llm_response, difficulty, skills)
            
            # Enhance with test cases if not provided
            if not question.get("test_cases"):
                question["test_cases"] = self._generate_test_cases(question, difficulty)
            
            # Add code templates for different languages
            question["code_templates"] = self._generate_code_templates(question, skills)
            
            log_info(f"[QUESTION GEN] Question generated: {question.get('title', 'Untitled')}")
            
            return question
            
        except Exception as e:
            log_error(f"Error generating question: {e}")
            # Fallback to a default question
            return self._get_fallback_question(difficulty, skills)
    
    def _build_context(
        self,
        skills: List[str],
        experience_years: int,
        job_skills: List[str],
        job_title: str,
        difficulty: str,
        question_number: int,
        previous_questions: List[str],
        inspiration: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Build context for question generation"""
        return {
            "candidate_skills": skills,
            "experience_years": experience_years,
            "job_skills": job_skills,
            "job_title": job_title,
            "difficulty": difficulty,
            "question_number": question_number,
            "previous_questions": previous_questions,
            "sources": self.question_sources,
            "inspiration": inspiration or {}
        }
    
    def _create_question_prompt(self, context: Dict[str, Any]) -> str:
        """Create prompt for LLM to generate question"""
        skills_str = ", ".join(context["candidate_skills"][:10])
        job_skills_str = ", ".join(context["job_skills"][:10])
        prev_questions_str = "\n".join([f"- {q}" for q in context["previous_questions"]]) if context["previous_questions"] else "None"
        
        # Add inspiration examples
        inspiration_text = ""
        if context.get("inspiration"):
            leetcode_qs = context["inspiration"].get("leetcode", [])[:2]
            if leetcode_qs:
                inspiration_text = "\n\nInspiration from LeetCode:\n"
                for q in leetcode_qs:
                    inspiration_text += f"- {q.get('title', '')} ({q.get('difficulty', '')})\n"
        
        prompt = f"""Generate a {context["difficulty"]} difficulty coding interview question for a {context["job_title"]} position.

Candidate Profile:
- Skills: {skills_str}
- Experience: {context["experience_years"]} years
- Job Required Skills: {job_skills_str}

Previous Questions (avoid similar topics):
{prev_questions_str}
{inspiration_text}

Question Requirements:
1. Should test programming fundamentals relevant to {context["job_title"]}
2. Difficulty: {context["difficulty"]}
3. Should be inspired by problems from: {", ".join(context["sources"])}
4. IMPORTANT: The question must be LANGUAGE-AGNOSTIC. It should be solvable in Python, Java, JavaScript, C++, C#, or any programming language.
5. Must include:
   - Clear problem statement (language-independent)
   - Input/output examples (at least 2) with clear data types
   - Constraints
   - Expected time/space complexity hints

Generate the question in JSON format:
{{
    "title": "Question Title",
    "description": "Detailed problem description",
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
    "topics": ["topic1", "topic2"],
    "difficulty": "{context["difficulty"]}"
}}"""
        
        return prompt
    
    def _parse_llm_response(self, llm_response: str, difficulty: str, skills: List[str]) -> Dict[str, Any]:
        """Parse LLM response into structured question format"""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                question_data = json.loads(json_match.group())
            else:
                # If no JSON, create structure from text
                question_data = {
                    "title": self._extract_title(llm_response),
                    "description": llm_response,
                    "difficulty": difficulty
                }
        except Exception as e:
            log_warning(f"Could not parse LLM response as JSON: {e}")
            question_data = {
                "title": f"Coding Challenge ({difficulty})",
                "description": llm_response,
                "difficulty": difficulty
            }
        
        # Process examples - convert complex types to JSON strings if needed, or keep as-is
        examples = question_data.get("examples", [])
        processed_examples = []
        for ex in examples:
            if isinstance(ex, dict):
                # Convert input/output to JSON string if they're complex types
                input_val = ex.get("input", "")
                output_val = ex.get("output", "")
                
                # If input/output are dicts or lists, convert to JSON string
                if isinstance(input_val, (dict, list)):
                    input_val = json.dumps(input_val)
                if isinstance(output_val, (dict, list)):
                    output_val = json.dumps(output_val)
                
                processed_examples.append({
                    "input": input_val,
                    "output": output_val,
                    "explanation": ex.get("explanation", "")
                })
            else:
                processed_examples.append(ex)
        
        # Process test cases - convert complex types to JSON strings if needed
        test_cases = question_data.get("test_cases", [])
        processed_test_cases = []
        processed_expected_outputs = []
        
        for tc in test_cases:
            if isinstance(tc, dict):
                input_val = tc.get("input", "")
                expected_output = tc.get("expected_output", "")
                
                # Convert to JSON string if complex type
                if isinstance(input_val, (dict, list)):
                    input_val = json.dumps(input_val)
                if isinstance(expected_output, (dict, list)):
                    expected_output = json.dumps(expected_output)
                
                processed_test_cases.append({
                    "input": input_val,
                    "expected_output": expected_output
                })
                processed_expected_outputs.append(expected_output)
            else:
                processed_test_cases.append(tc)
                processed_expected_outputs.append("")
        
        # Ensure required fields
        question = {
            "title": question_data.get("title", f"Coding Question ({difficulty})"),
            "description": question_data.get("description", llm_response),
            "difficulty": question_data.get("difficulty", difficulty),
            "examples": processed_examples,
            "constraints": question_data.get("constraints", []),
            "test_cases": processed_test_cases,
            "expected_outputs": processed_expected_outputs,
            "hints": question_data.get("hints", []),
            "topics": question_data.get("topics", skills[:3] if skills else []),
            "time_limit_minutes": self._get_time_limit(difficulty)
        }
        
        return question
    
    def _extract_title(self, text: str) -> str:
        """Extract title from text response"""
        lines = text.split("\n")
        for line in lines[:5]:
            if line.strip() and len(line.strip()) < 100:
                return line.strip()
        return "Coding Challenge"
    
    def _generate_test_cases(self, question: Dict[str, Any], difficulty: str) -> List[Dict[str, Any]]:
        """Generate test cases if not provided by LLM"""
        # Default test cases based on difficulty
        if difficulty == "easy":
            return [
                {"input": "simple case", "expected_output": "expected result"},
                {"input": "edge case", "expected_output": "edge result"}
            ]
        elif difficulty == "medium":
            return [
                {"input": "standard case", "expected_output": "standard result"},
                {"input": "edge case 1", "expected_output": "edge result 1"},
                {"input": "edge case 2", "expected_output": "edge result 2"}
            ]
        else:  # hard
            return [
                {"input": "complex case", "expected_output": "complex result"},
                {"input": "edge case 1", "expected_output": "edge result 1"},
                {"input": "edge case 2", "expected_output": "edge result 2"},
                {"input": "performance case", "expected_output": "performance result"}
            ]
    
    def _generate_code_templates(self, question: Dict[str, Any], skills: List[str]) -> Dict[str, str]:
        """Generate code templates for different languages"""
        templates = {}
        
        # Determine preferred language from skills
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
        
        # Default languages if none found - include all supported languages
        if not preferred_languages:
            preferred_languages = ["python", "java", "javascript", "cpp", "csharp"]
        
        # Always include all supported languages for flexibility
        all_supported = ["python", "java", "javascript", "cpp", "csharp"]
        preferred_languages = list(set(preferred_languages + all_supported))  # Union, no duplicates
        
        # Generate templates
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
        """Get time limit in minutes based on difficulty"""
        limits = {
            "easy": 15,
            "medium": 30,
            "hard": 45
        }
        return limits.get(difficulty, 30)
    
    def _get_fallback_question(self, difficulty: str, skills: List[str]) -> Dict[str, Any]:
        """Get a fallback question if LLM generation fails"""
        return {
            "title": f"Array Problem ({difficulty.title()})",
            "description": f"Solve a {difficulty} difficulty array manipulation problem.",
            "difficulty": difficulty,
            "examples": [
                {"input": "[1, 2, 3]", "output": "6", "explanation": "Sum of array"}
            ],
            "constraints": ["1 <= n <= 100"],
            "test_cases": [
                {"input": "[1, 2, 3]", "expected_output": "6"}
            ],
            "expected_outputs": ["6"],
            "hints": ["Think about array traversal", "Consider edge cases"],
            "topics": ["arrays", "algorithms"],
            "time_limit_minutes": self._get_time_limit(difficulty),
            "code_templates": {
                "python": "def solution(arr):\n    # Write your solution here\n    pass",
                "java": "public class Solution {\n    public void solution(int[] arr) {\n        // Write your solution here\n    }\n}",
                "javascript": "function solution(arr) {\n    // Write your solution here\n}",
                "cpp": "#include <iostream>\n#include <vector>\nusing namespace std;\n\nclass Solution {\npublic:\n    void solution(vector<int>& arr) {\n        // Write your solution here\n    }\n};",
                "csharp": "using System;\n\npublic class Solution {\n    public void solution(int[] arr) {\n        // Write your solution here\n    }\n}"
            }
        }

