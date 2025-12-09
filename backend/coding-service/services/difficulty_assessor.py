"""
Difficulty Assessment Service
Assesses question difficulty based on candidate experience and job requirements
"""
import sys
import os
from typing import Dict, List, Optional, Any

# Attempt to reuse EnhancedLLMService from text-service
# Try Docker path first (production/containerized), then local development path
text_service_path = None

# Docker path (when text-service is mounted at /app/text-service)
docker_path = "/app/text-service"
if os.path.exists(docker_path):
    text_service_path = docker_path
else:
    # Local development path (relative to project root)
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_file_dir, '..', '..', '..'))
    local_path = os.path.abspath(os.path.join(project_root, 'backend', 'text-service'))
    if os.path.exists(local_path):
        text_service_path = os.path.normpath(local_path)

if text_service_path and text_service_path not in sys.path:
    sys.path.insert(0, text_service_path)

try:
    from services.llm_service import EnhancedLLMService
except Exception:
    EnhancedLLMService = None

try:
    from common_service_util_logger import log_info, log_error
except Exception:
    def log_info(msg):
        print("INFO:", msg)

    def log_error(msg):
        print("ERROR:", msg)


class DifficultyAssessor:
    def __init__(self):
        self.llm_service = EnhancedLLMService() if EnhancedLLMService else None
        self.difficulty_levels = ["easy", "medium", "hard"]
        log_info("[OK] Difficulty Assessor initialized")

    async def assess_difficulty(self, resume_data: Dict[str, Any], job_description: Dict[str, Any]) -> str:
        try:
            experience_years = resume_data.get("experience_years", 0)
            skills = resume_data.get("skills", [])
            job_level = job_description.get("level", "").lower()
            job_skills = job_description.get("required_skills", [])

            base = self._rule_based_assessment(experience_years, job_level, skills, job_skills)

            llm_difficulty = await self._llm_assess_difficulty(resume_data, job_description, base)

            final = self._combine_assessments(base, llm_difficulty)

            log_info(f"[DIFFICULTY] Assessed: {final} (base: {base}, llm: {llm_difficulty})")
            return final

        except Exception as e:
            log_error(f"Error assessing difficulty: {e}")
            return "medium"

    def _rule_based_assessment(self, experience_years: int, job_level: str, skills: List[str], job_skills: List[str]) -> str:
        if experience_years < 2:
            base = "easy"
        elif experience_years < 5:
            base = "medium"
        else:
            base = "hard"

        if "senior" in job_level or "lead" in job_level:
            if base == "easy":
                base = "medium"
            elif base == "medium":
                base = "hard"
        elif "junior" in job_level or "entry" in job_level:
            if base == "hard":
                base = "medium"
            elif base == "medium":
                base = "easy"

        skill_match_ratio = len(set(skills) & set(job_skills)) / max(len(job_skills), 1)
        if skill_match_ratio < 0.3:
            if base == "hard":
                base = "medium"
        elif skill_match_ratio > 0.7:
            if base == "easy":
                base = "medium"

        return base

    async def _llm_assess_difficulty(self, resume_data: Dict[str, Any], job_description: Dict[str, Any], base_difficulty: str) -> str:
        try:
            prompt = f"Assess the appropriate coding interview difficulty level.\nCandidate: Experience: {resume_data.get('experience_years', 0)} years; Skills: {', '.join(resume_data.get('skills', [])[:10])} ; Job: Title: {job_description.get('job_title', '')} ; Level: {job_description.get('level', '')} ; Required Skills: {', '.join(job_description.get('required_skills', [])[:10])} ; Base Assessment: {base_difficulty}. Respond with one word: easy, medium or hard."

            if self.llm_service:
                response = await self.llm_service._generate_with_gemini(prompt)
                if not response:
                    response = await self.llm_service._generate_with_groq(prompt)

                if response:
                    response_lower = response.lower().strip()
                    if "easy" in response_lower:
                        return "easy"
                    elif "hard" in response_lower:
                        return "hard"
                    else:
                        return "medium"

            return base_difficulty

        except Exception as e:
            log_error(f"LLM difficulty assessment failed: {e}")
            return base_difficulty

    def _combine_assessments(self, base: str, llm: str) -> str:
        if base == llm:
            return base

        order = ["easy", "medium", "hard"]
        base_idx = order.index(base)
        llm_idx = order.index(llm)
        avg_idx = round((base_idx + llm_idx) / 2)
        return order[avg_idx]
