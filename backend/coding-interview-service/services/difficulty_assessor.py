"""
Difficulty Assessment Service
Assesses question difficulty based on candidate experience and job requirements
"""

import sys
import os
from typing import Dict, List, Optional, Any

# Add text-service to path
current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_file_dir, '..', '..', '..'))
text_service_path = os.path.abspath(os.path.join(project_root, 'backend', 'text-service'))
coding_service_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
coding_service_dir = os.path.normpath(os.path.abspath(coding_service_dir))

# Add paths - coding_service_dir first so local utils can be found
if coding_service_dir not in sys.path:
    sys.path.insert(0, coding_service_dir)
if text_service_path not in sys.path:
    sys.path.insert(0, text_service_path)

from services.llm_service import EnhancedLLMService
from utils.logger import log_info, log_error

class DifficultyAssessor:
    """Assesses appropriate difficulty level for coding questions"""
    
    def __init__(self):
        self.llm_service = EnhancedLLMService()
        
        # Difficulty mapping
        self.difficulty_levels = ["easy", "medium", "hard"]
        
        log_info("[OK] Difficulty Assessor initialized")
    
    async def assess_difficulty(
        self,
        resume_data: Dict[str, Any],
        job_description: Dict[str, Any]
    ) -> str:
        """
        Assess appropriate difficulty level
        
        Args:
            resume_data: Parsed resume information
            job_description: Job description and requirements
        
        Returns:
            Difficulty level: "easy", "medium", or "hard"
        """
        try:
            # Extract key factors
            experience_years = resume_data.get("experience_years", 0)
            skills = resume_data.get("skills", [])
            job_level = job_description.get("level", "").lower()
            job_skills = job_description.get("required_skills", [])
            
            # Rule-based assessment
            base_difficulty = self._rule_based_assessment(
                experience_years=experience_years,
                job_level=job_level,
                skills=skills,
                job_skills=job_skills
            )
            
            # Use LLM to refine assessment
            llm_difficulty = await self._llm_assess_difficulty(
                resume_data=resume_data,
                job_description=job_description,
                base_difficulty=base_difficulty
            )
            
            # Combine assessments
            final_difficulty = self._combine_assessments(base_difficulty, llm_difficulty)
            
            log_info(f"[DIFFICULTY] Assessed: {final_difficulty} (base: {base_difficulty}, LLM: {llm_difficulty})")
            
            return final_difficulty
            
        except Exception as e:
            log_error(f"Error assessing difficulty: {e}")
            # Default to medium
            return "medium"
    
    def _rule_based_assessment(
        self,
        experience_years: int,
        job_level: str,
        skills: List[str],
        job_skills: List[str]
    ) -> str:
        """Rule-based difficulty assessment"""
        
        # Experience-based
        if experience_years < 2:
            base = "easy"
        elif experience_years < 5:
            base = "medium"
        else:
            base = "hard"
        
        # Job level adjustment
        if "senior" in job_level or "lead" in job_level or "principal" in job_level:
            if base == "easy":
                base = "medium"
            elif base == "medium":
                base = "hard"
        elif "junior" in job_level or "entry" in job_level or "intern" in job_level:
            if base == "hard":
                base = "medium"
            elif base == "medium":
                base = "easy"
        
        # Skills match adjustment
        skill_match_ratio = len(set(skills) & set(job_skills)) / max(len(job_skills), 1)
        if skill_match_ratio < 0.3:
            # Lower difficulty if skills don't match well
            if base == "hard":
                base = "medium"
        elif skill_match_ratio > 0.7:
            # Increase difficulty if skills match well
            if base == "easy":
                base = "medium"
        
        return base
    
    async def _llm_assess_difficulty(
        self,
        resume_data: Dict[str, Any],
        job_description: Dict[str, Any],
        base_difficulty: str
    ) -> str:
        """Use LLM to assess difficulty"""
        try:
            prompt = f"""Assess the appropriate coding interview difficulty level.

Candidate:
- Experience: {resume_data.get('experience_years', 0)} years
- Skills: {', '.join(resume_data.get('skills', [])[:10])}
- Education: {resume_data.get('education', [])}

Job:
- Title: {job_description.get('job_title', '')}
- Level: {job_description.get('level', '')}
- Required Skills: {', '.join(job_description.get('required_skills', [])[:10])}

Base Assessment: {base_difficulty}

Respond with ONLY one word: "easy", "medium", or "hard"
"""
            
            # Use LLM to get refined assessment
            response = await self.llm_service._generate_with_gemini(prompt)
            
            # Fallback if Gemini fails
            if not response or len(response.strip()) < 3:
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
        """Combine rule-based and LLM assessments"""
        # If both agree, use that
        if base == llm:
            return base
        
        # If they differ, use a weighted approach
        # Prefer LLM but consider base
        difficulty_order = ["easy", "medium", "hard"]
        base_idx = difficulty_order.index(base)
        llm_idx = difficulty_order.index(llm)
        
        # Average the indices (round to nearest)
        avg_idx = round((base_idx + llm_idx) / 2)
        
        return difficulty_order[avg_idx]

