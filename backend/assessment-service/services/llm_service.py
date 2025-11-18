from groq import Groq
from typing import Dict, Optional
from config.settings import settings
from config.logger import logger, log_llm_call
import json


class LLMService:
    """Service for LLM interactions using Groq API"""
    
    def __init__(self):
        """Initialize Groq client"""
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = settings.groq_model
        self.max_tokens = settings.llm_max_tokens
        self.temperature = settings.llm_temperature
    
    def determine_weights_from_job_description(
        self, 
        job_description: str,
        job_title: str,
        required_skills: list,
        has_coding: bool = True
    ) -> Dict[str, float]:
        """
        Use LLM to determine optimal scoring weights based on job description
        
        Args:
            job_description: Full job description text
            job_title: Job title
            required_skills: List of required skills
            has_coding: Whether coding assessment is included
        
        Returns:
            Dictionary with weights: {"coding": 0.4, "text": 0.2, "audio": 0.2, "video": 0.2}
        """
        
        if has_coding:
            prompt = f"""
You are an expert hiring manager. Based on the job description below, determine the optimal weights for scoring a candidate's interview performance.

**Job Title:** {job_title}

**Required Skills:** {', '.join(required_skills) if required_skills else 'Not specified'}

**Job Description:**
{job_description}

The assessment includes:
- **Coding**: Technical coding ability and problem-solving
- **Text**: Behavioral answers, technical knowledge communication, STAR methodology
- **Audio**: Speaking confidence, fluency, communication clarity
- **Video**: Body language, engagement, eye contact, professionalism

Determine weights that sum to 100% (1.0 total). Consider:
- For highly technical roles (SWE, Data Scientist): coding should be 40-50%
- For roles requiring communication (PM, Designer): audio/text should be higher
- For leadership roles: video (presence) and text (experience) should be higher

Return ONLY valid JSON in this exact format:
{{
    "coding": 0.40,
    "text": 0.20,
    "audio": 0.20,
    "video": 0.20
}}

Ensure weights sum to exactly 1.0.
"""
        else:
            prompt = f"""
You are an expert hiring manager. Based on the job description below, determine the optimal weights for scoring a candidate's interview performance.

**Job Title:** {job_title}

**Required Skills:** {', '.join(required_skills) if required_skills else 'Not specified'}

**Job Description:**
{job_description}

The assessment includes (NO coding assessment):
- **Text**: Behavioral answers, technical knowledge communication, STAR methodology
- **Audio**: Speaking confidence, fluency, communication clarity
- **Video**: Body language, engagement, eye contact, professionalism

Determine weights that sum to 100% (1.0 total). Consider the role requirements.

Return ONLY valid JSON in this exact format:
{{
    "text": 0.34,
    "audio": 0.33,
    "video": 0.33
}}

Ensure weights sum to exactly 1.0.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=500
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            weights = self._extract_json(response_text)
            
            # Validate weights
            if weights and self._validate_weights(weights, has_coding):
                log_llm_call(
                    operation="determine_weights",
                    model=self.model,
                    success=True,
                    tokens_used=response.usage.total_tokens if hasattr(response, 'usage') else None
                )
                logger.info("llm_determined_weights_successfully", weights=weights)
                return weights
            else:
                # Fallback to defaults
                logger.warning("llm_weights_invalid_using_defaults", llm_returned_weights=weights)
                return self._get_default_weights(has_coding)
        
        except Exception as e:
            logger.error("llm_weight_determination_failed_using_defaults", error=str(e))
            return self._get_default_weights(has_coding)
    
    def generate_final_recommendation(
        self,
        interview_id: str,
        overall_score: float,
        soft_skills_score: float,
        communication_score: float,
        technical_score: float,
        proctoring_risk_score: float,
        audio_highlights: Dict,
        video_highlights: Dict,
        text_highlights: Dict,
        coding_highlights: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Use LLM to generate final hiring recommendation and summary
        
        Returns:
            {
                "recommendation": "Hire|No Hire|Maybe|Needs Review",
                "summary": "Executive summary...",
                "reasoning": "Detailed reasoning..."
            }
        """
        
        # Build coding section
        coding_section = ""
        if coding_highlights:
            coding_section = f"""
**Coding Results:**
- Correctness: {coding_highlights.get('correctness_score', 'N/A')}/100
- Test Cases Passed: {coding_highlights.get('test_cases_passed', 0)}/{coding_highlights.get('test_cases_total', 0)}
- Time Complexity: {coding_highlights.get('time_complexity', 'N/A')}
- Code Quality: {coding_highlights.get('code_quality_score', 'N/A')}/100
"""
        
        prompt = f"""
You are an expert interview assessor. Based on the analysis results below, provide a final hiring recommendation.

**Overall Score:** {overall_score:.1f}/100
**Soft Skills:** {soft_skills_score:.1f}/100
**Communication:** {communication_score:.1f}/100
**Technical Skills:** {technical_score:.1f}/100
**Proctoring Risk:** {proctoring_risk_score:.1f}/100 (lower is better - above 50 indicates concerns)

**Audio Analysis Highlights:**
- Communication Rating: {audio_highlights.get('communication_rating', 'N/A')}
- Confidence Level: {audio_highlights.get('confidence_level', 'N/A')}
- Filler Rate: {audio_highlights.get('filler_rate', 'N/A')} per minute
- Cheating Risk: {audio_highlights.get('cheating_risk', 'N/A')}

**Video Analysis Highlights:**
- Engagement Score: {video_highlights.get('engagement_score', 'N/A')}/100
- Attention Score: {video_highlights.get('attention_score', 'N/A')}/100
- Professionalism: {video_highlights.get('professionalism', 'N/A')}/100
- Concerns: {', '.join(video_highlights.get('concerns', [])) if video_highlights.get('concerns') else 'None'}
- Cheating Probability: {video_highlights.get('cheating_probability', 'N/A')}

**Text Analysis Highlights:**
- Technical Assessment: {text_highlights.get('technical_summary', 'N/A')}
- Communication Assessment: {text_highlights.get('communication_summary', 'N/A')}
- Strengths: {', '.join(text_highlights.get('strengths', [])) if text_highlights.get('strengths') else 'None'}
- Red Flags: {', '.join(text_highlights.get('red_flags', [])) if text_highlights.get('red_flags') else 'None'}

{coding_section}

**Decision Criteria:**
- Overall Score >= 80: Strong Hire candidate
- Overall Score 70-79: Hire (with some areas for growth)
- Overall Score 60-69: Maybe (borderline, needs discussion)
- Overall Score < 60: No Hire
- Proctoring Risk > 50: Automatic "Needs Review" regardless of scores
- Any critical red flags: "Needs Review"

Provide your assessment in this EXACT JSON format:
{{
    "recommendation": "Hire|No Hire|Maybe|Needs Review",
    "summary": "2-3 sentence executive summary for hiring manager",
    "reasoning": "Brief explanation for your recommendation (2-3 sentences)"
}}

Be objective and evidence-based. Focus on facts from the data.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=800
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Extract JSON
            result = self._extract_json(response_text)
            
            # Validate result has required fields
            if result and all(k in result for k in ["recommendation", "summary", "reasoning"]):
                # Validate recommendation value
                valid_recommendations = ["Hire", "No Hire", "Maybe", "Needs Review"]
                if result["recommendation"] in valid_recommendations:
                    log_llm_call(
                        operation="generate_recommendation",
                        model=self.model,
                        success=True,
                        tokens_used=response.usage.total_tokens if hasattr(response, 'usage') else None
                    )
                    return result
            
            # Fallback
            logger.warning("llm_recommendation_invalid", result=result)
            return self._generate_fallback_recommendation(overall_score, proctoring_risk_score)
        
        except Exception as e:
            logger.error("llm_recommendation_failed", error=str(e))
            return self._generate_fallback_recommendation(overall_score, proctoring_risk_score)
    
    def _extract_json(self, text: str) -> Optional[Dict]:
        """Extract JSON from LLM response"""
        try:
            # Try direct parse first
            return json.loads(text)
        except:
            pass
        
        # Try to find JSON in markdown code blocks
        if "```json" in text:
            try:
                json_str = text.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            except:
                pass
        
        # Try to find JSON between curly braces
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            json_str = text[start:end]
            return json.loads(json_str)
        except:
            pass
        
        return None
    
    def _validate_weights(self, weights: Dict, has_coding: bool) -> bool:
        """Validate that weights are correct"""
        if has_coding:
            required_keys = {"coding", "text", "audio", "video"}
        else:
            required_keys = {"text", "audio", "video"}
        
        # Check all keys present
        if set(weights.keys()) != required_keys:
            return False
        
        # Check all values are floats between 0 and 1
        for value in weights.values():
            if not isinstance(value, (int, float)) or value < 0 or value > 1:
                return False
        
        # Check sum is approximately 1.0 (allow small floating point errors)
        total = sum(weights.values())
        if abs(total - 1.0) > 0.01:
            return False
        
        return True
    
    def _get_default_weights(self, has_coding: bool) -> Dict[str, float]:
        """Get default weights from settings"""
        if has_coding:
            return settings.default_weights_with_coding
        else:
            return settings.default_weights_without_coding
    
    def _generate_fallback_recommendation(
        self, 
        overall_score: float, 
        proctoring_risk_score: float
    ) -> Dict[str, str]:
        """Generate rule-based recommendation as fallback"""
        
        # Check proctoring risk first
        if proctoring_risk_score > 50:
            return {
                "recommendation": "Needs Review",
                "summary": f"Candidate scored {overall_score:.1f}/100 overall, but proctoring concerns require human review.",
                "reasoning": "High proctoring risk score detected. Manual review recommended before making a decision."
            }
        
        # Score-based recommendation
        if overall_score >= 80:
            recommendation = "Hire"
            summary = f"Strong candidate with overall score of {overall_score:.1f}/100. Demonstrated solid performance across all areas."
            reasoning = "High overall score indicates strong fit for the role."
        elif overall_score >= 70:
            recommendation = "Hire"
            summary = f"Good candidate with overall score of {overall_score:.1f}/100. Shows competency with some areas for growth."
            reasoning = "Above-average performance suggests good potential for the role."
        elif overall_score >= 60:
            recommendation = "Maybe"
            summary = f"Borderline candidate with overall score of {overall_score:.1f}/100. Mixed performance across assessments."
            reasoning = "Score in borderline range. Recommend team discussion before decision."
        else:
            recommendation = "No Hire"
            summary = f"Candidate scored {overall_score:.1f}/100 overall. Performance did not meet minimum requirements."
            reasoning = "Below-threshold performance across multiple assessment areas."
        
        return {
            "recommendation": recommendation,
            "summary": summary,
            "reasoning": reasoning
        }