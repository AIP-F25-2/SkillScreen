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
        Generate final hiring recommendation using rule-based decision + LLM explanation
        
        Process:
        1. Apply hard threshold rules to determine recommendation
        2. Use LLM to generate summary and reasoning based on the rule-based decision
        
        Returns:
            {
                "recommendation": "Hire|No Hire|Maybe|Needs Review",
                "summary": "Executive summary...",
                "reasoning": "Detailed reasoning..."
            }
        """
        
        # STEP 1: Rule-based decision (deterministic, auditable)
        rule_based_decision = self._apply_decision_rules(
            overall_score=overall_score,
            proctoring_risk_score=proctoring_risk_score
        )
        
        logger.info(
            "rule_based_decision_applied",
            interview_id=interview_id,
            overall_score=overall_score,
            proctoring_risk_score=proctoring_risk_score,
            decision=rule_based_decision["recommendation"],
            reason=rule_based_decision["rule_reason"]
        )
        
        # STEP 2: Use LLM to explain WHY this decision was made
        llm_explanation = self._generate_llm_explanation(
            rule_based_recommendation=rule_based_decision["recommendation"],
            rule_reason=rule_based_decision["rule_reason"],
            overall_score=overall_score,
            soft_skills_score=soft_skills_score,
            communication_score=communication_score,
            technical_score=technical_score,
            proctoring_risk_score=proctoring_risk_score,
            audio_highlights=audio_highlights,
            video_highlights=video_highlights,
            text_highlights=text_highlights,
            coding_highlights=coding_highlights
        )
        
        # Combine rule-based decision with LLM explanation
        return {
            "recommendation": rule_based_decision["recommendation"],
            "summary": llm_explanation.get("summary", rule_based_decision["default_summary"]),
            "reasoning": llm_explanation.get("reasoning", rule_based_decision["default_reasoning"])
        }
    
    def _apply_decision_rules(
        self,
        overall_score: float,
        proctoring_risk_score: float
    ) -> Dict[str, str]:
        """
        Apply hard threshold rules to determine recommendation
        
        Rules (in priority order):
        1. Proctoring Risk > 50 → "Needs Review" (security concern)
        2. Overall Score >= 80 → "Hire" (strong candidate)
        3. Overall Score >= 70 → "Maybe" (borderline, needs discussion)
        4. Overall Score < 70 → "No Hire" (below threshold)
        
        Returns:
            {
                "recommendation": str,
                "rule_reason": str,  # Why this rule was triggered
                "default_summary": str,  # Fallback if LLM fails
                "default_reasoning": str  # Fallback if LLM fails
            }
        """
        
        # Rule 1: Proctoring concerns override everything
        if proctoring_risk_score > 50:
            return {
                "recommendation": "Needs Review",
                "rule_reason": f"Proctoring risk score ({proctoring_risk_score:.1f}) exceeds threshold of 50",
                "default_summary": f"Candidate scored {overall_score:.1f}/100 overall, but high proctoring risk ({proctoring_risk_score:.1f}/100) requires manual review before proceeding.",
                "default_reasoning": "Proctoring concerns detected (cheating probability, environment issues, or behavioral anomalies). Human verification required to validate assessment integrity."
            }
        
        # Rule 2: Strong performer
        if overall_score >= 80:
            return {
                "recommendation": "Hire",
                "rule_reason": f"Overall score ({overall_score:.1f}) meets 'Hire' threshold (>= 80)",
                "default_summary": f"Strong candidate with overall score of {overall_score:.1f}/100. Demonstrated solid performance across technical and soft skills assessments.",
                "default_reasoning": "High overall score indicates strong fit for the role. Candidate exceeded the hiring threshold with consistent performance."
            }
        
        # Rule 3: Borderline candidate
        if overall_score >= 70:
            return {
                "recommendation": "Maybe",
                "rule_reason": f"Overall score ({overall_score:.1f}) falls in 'Maybe' range (70-79)",
                "default_summary": f"Borderline candidate with overall score of {overall_score:.1f}/100. Mixed performance across assessments warrants team discussion.",
                "default_reasoning": "Score falls in the borderline range (70-79). Recommend reviewing detailed evidence and discussing with hiring team before making final decision."
            }
        
        # Rule 4: Below threshold
        return {
            "recommendation": "No Hire",
            "rule_reason": f"Overall score ({overall_score:.1f}) below 'No Hire' threshold (< 70)",
            "default_summary": f"Candidate scored {overall_score:.1f}/100 overall. Performance did not meet minimum requirements for this role.",
            "default_reasoning": "Below-threshold performance across multiple assessment areas. Candidate does not demonstrate the required competencies at this time."
        }
    
    def _generate_llm_explanation(
        self,
        rule_based_recommendation: str,
        rule_reason: str,
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
        Use LLM to generate human-readable summary and reasoning for the rule-based decision
        
        The LLM does NOT make the decision - it only explains WHY the decision was made
        based on the evidence.
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
You are an expert interview assessor writing a report for a hiring manager.

A candidate has been assessed and the **DECISION HAS ALREADY BEEN MADE** using our scoring thresholds:

**FINAL DECISION (ALREADY DETERMINED):** {rule_based_recommendation}
**REASON FOR DECISION:** {rule_reason}

Your task is to write a compelling summary and reasoning that explains WHY this decision makes sense based on the evidence below. Do NOT change the decision - only explain it.

---

**Assessment Results:**

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

---

**Your Task:**

Write a professional assessment report explaining why "{rule_based_recommendation}" is the appropriate decision. Focus on:
1. **Summary**: 2-3 sentences for the hiring manager highlighting key strengths and concerns
2. **Reasoning**: 2-3 sentences providing evidence-based justification for the "{rule_based_recommendation}" decision

Be objective, factual, and reference specific scores/evidence. Match the tone to the decision:
- "Hire": Positive and confident
- "Maybe": Balanced, noting both strengths and concerns
- "No Hire": Professional but clear about gaps
- "Needs Review": Emphasize the need for human verification

Return ONLY valid JSON in this exact format:
{{
    "summary": "Your executive summary here (2-3 sentences)",
    "reasoning": "Your detailed reasoning here (2-3 sentences)"
}}

DO NOT include the recommendation field - it has already been determined as "{rule_based_recommendation}".
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
            if result and "summary" in result and "reasoning" in result:
                log_llm_call(
                    operation="generate_explanation",
                    model=self.model,
                    success=True,
                    tokens_used=response.usage.total_tokens if hasattr(response, 'usage') else None
                )
                logger.info(
                    "llm_explanation_generated",
                    recommendation=rule_based_recommendation,
                    summary_length=len(result["summary"]),
                    reasoning_length=len(result["reasoning"])
                )
                return result
            else:
                logger.warning("llm_explanation_invalid_structure", result=result)
                return {}
        
        except Exception as e:
            logger.error("llm_explanation_failed", error=str(e))
            return {}
    
    def _extract_json(self, text: str) -> Optional[Dict]:
        """Extract JSON from LLM response"""
        try:
            # Try direct parse first
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON in markdown code blocks
        if "```json" in text:
            try:
                json_str = text.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            except (json.JSONDecodeError, IndexError):
                pass

        # Try to find JSON between curly braces
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            json_str = text[start:end]
            return json.loads(json_str)
        except json.JSONDecodeError:
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