import json
from typing import Dict, Optional
import google.generativeai as genai
from groq import Groq
from config import logger, settings
from repositories import QuestionRepository
import uuid
from datetime import datetime, timezone


class NLPEvaluationService:
    """Service for AI-powered NLP evaluation of candidate responses"""

    def __init__(self):
        self.question_repo = QuestionRepository()

        # Initialize Gemini API
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        else:
            logger.warning("⚠️ GEMINI_API_KEY not set")
            self.model = None

        # Initialize Groq API as fallback
        if settings.GROQ_API_KEY:
            self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        else:
            logger.warning("⚠️ GROQ_API_KEY not set - Groq fallback unavailable")
            self.groq_client = None

    def evaluate_response(
        self,
        session_id: str,
        response_text: str,
        expected_answer_points: Optional[list] = None
    ) -> Dict:
        """Evaluate a candidate's response using Gemini AI and store in ai_analysis"""
        try:
            session = self.question_repo.get_session_by_id(session_id)

            if not session:
                return {
                    "success": False,
                    "error": f"Session not found: {session_id}"
                }

            if expected_answer_points is None:
                expected_answer_points = session.get("metadata", {}).get("expected_points", [])

            # Build evaluation prompt
            prompt = self._build_evaluation_prompt(
                session["question_text"],
                response_text,
                expected_answer_points
            )

            logger.info(f"🔄 Evaluating response for session {session_id}")

            # Call Gemini API first, fallback to Groq, then basic evaluation
            evaluation = None
            if self.model:
                try:
                    response = self.model.generate_content(prompt)
                    evaluation = self._parse_evaluation_response(response.text)
                except Exception as gemini_error:
                    error_msg = str(gemini_error)
                    if "quota" in error_msg.lower() or "429" in error_msg or "resource exhausted" in error_msg.lower():
                        logger.warning(f"⚠️ Gemini API quota exceeded, trying Groq fallback")
                        if self.groq_client:
                            try:
                                evaluation = self._evaluate_with_groq(prompt)
                            except Exception as groq_error:
                                logger.warning(f"⚠️ Groq evaluation failed: {str(groq_error)}, using basic evaluation")
                                evaluation = self._get_basic_evaluation(response_text, expected_answer_points)
                        else:
                            logger.warning("⚠️ Groq not available, using basic evaluation")
                            evaluation = self._get_basic_evaluation(response_text, expected_answer_points)
                    else:
                        raise
            else:
                logger.warning("⚠️ Gemini model not initialized, trying Groq")
                if self.groq_client:
                    try:
                        evaluation = self._evaluate_with_groq(prompt)
                    except Exception as groq_error:
                        logger.warning(f"⚠️ Groq evaluation failed: {str(groq_error)}, using basic evaluation")
                        evaluation = self._get_basic_evaluation(response_text, expected_answer_points)
                else:
                    evaluation = self._get_basic_evaluation(response_text, expected_answer_points)

            # Save analysis to ai_analysis table
            analysis_id = str(uuid.uuid4())
            analysis_data = {
                "id": analysis_id,
                "interview_id": session["interview_id"],
                "session_id": session_id,
                "analysis_type": "text",
                "raw_results": {
                    "response_text": response_text,
                    "evaluation_score": evaluation.get("score", 0),
                    "evaluation_feedback": evaluation.get("feedback", ""),
                    "keywords_matched": evaluation.get("keywords_matched", []),
                    "strengths": evaluation.get("strengths", []),
                    "areas_for_improvement": evaluation.get("areas_for_improvement", []),
                    "assessment": evaluation.get("assessment", "")
                },
                "service_name": "text-service",
                "confidence_score": str(evaluation.get("score", 0) / 100.0)
            }

            self.question_repo.save_analysis(analysis_data)

            # Update session with response
            self.question_repo.update_session_response(session_id, response_text)

            logger.info(f"✅ Analysis saved: {analysis_id}")

            return {
                "success": True,
                "data": {
                    "analysis_id": analysis_id,
                    "session_id": session_id,
                    "score": evaluation.get("score", 0),
                    "feedback": evaluation.get("feedback", ""),
                    "keywords_matched": evaluation.get("keywords_matched", []),
                    "strengths": evaluation.get("strengths", []),
                    "areas_for_improvement": evaluation.get("areas_for_improvement", [])
                }
            }

        except Exception as e:
            logger.error(f"❌ Error evaluating response: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def _build_evaluation_prompt(
        self,
        question: str,
        response: str,
        expected_points: list
    ) -> str:
        """Build prompt for Gemini to evaluate response"""
        prompt = f"""
        Evaluate the following interview response:

        QUESTION:
        {question}

        CANDIDATE RESPONSE:
        {response}

        EXPECTED ANSWER POINTS:
        {json.dumps(expected_points)}

        EVALUATION CRITERIA:
        - Relevance: How well does the response address the question?
        - Completeness: Does it cover the expected answer points?
        - Clarity: Is the response clear and well-structured?
        - Confidence: Does the candidate demonstrate confidence?
        - Specific Examples: Are there concrete examples or evidence?

        RESPONSE FORMAT:
        Return a JSON object with this structure:
        {{
            "score": <0-100>,
            "feedback": "Overall assessment",
            "strengths": ["strength1", "strength2"],
            "areas_for_improvement": ["area1", "area2"],
            "keywords_matched": ["keyword1", "keyword2"],
            "assessment": "brief assessment"
        }}

        Return ONLY the JSON object, no other text.
        """

        return prompt.strip()

    def _evaluate_with_groq(self, prompt: str) -> Dict:
        """Evaluate using Groq API as fallback"""
        try:
            message = self.groq_client.chat.completions.create(
                model=settings.GROQ_MODEL,
                max_tokens=settings.MAX_TOKENS_RESPONSE,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            response_text = message.choices[0].message.content
            return self._parse_evaluation_response(response_text)
        except Exception as e:
            logger.error(f"❌ Groq evaluation failed: {str(e)}")
            raise

    def _parse_evaluation_response(self, response_text: str) -> Dict:
        """Parse Gemini evaluation response"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {
                    "score": 0,
                    "feedback": "Unable to parse evaluation",
                    "keywords_matched": []
                }
        except json.JSONDecodeError:
            logger.warning("⚠️ Failed to parse evaluation response")
            return {
                "score": 0,
                "feedback": "Unable to parse evaluation",
                "keywords_matched": []
            }

    def _get_basic_evaluation(self, response_text: str, expected_points: list) -> Dict:
        """Get basic evaluation when Gemini is unavailable"""
        # Simple keyword matching
        matched_keywords = []
        response_lower = response_text.lower()

        for point in expected_points:
            if isinstance(point, str) and point.lower() in response_lower:
                matched_keywords.append(point)

        # Basic scoring
        score = min(100, (len(matched_keywords) / max(len(expected_points), 1)) * 100)

        return {
            "score": int(score),
            "feedback": f"Response covers {len(matched_keywords)} of {len(expected_points)} expected points",
            "keywords_matched": matched_keywords,
            "strengths": ["Response provided"],
            "areas_for_improvement": [f"Consider mentioning: {p}" for p in expected_points if p not in matched_keywords]
        }

    def evaluate_interview(self, interview_id: str) -> Dict:
        """Evaluate all responses for an interview and calculate overall score"""
        try:
            analyses = self.question_repo.get_interview_analyses(interview_id)

            if not analyses:
                return {
                    "success": False,
                    "error": "No analyses found for this interview"
                }

            # Calculate average score
            scores = []
            all_strengths = []
            all_improvements = []

            for analysis in analyses:
                try:
                    results = analysis.get("raw_results", {})
                    score = float(results.get("evaluation_score", 0))
                    scores.append(score)
                    all_strengths.extend(results.get("strengths", []))
                    all_improvements.extend(results.get("areas_for_improvement", []))
                except (ValueError, TypeError):
                    pass

            overall_score = sum(scores) / len(scores) if scores else 0

            return {
                "success": True,
                "data": {
                    "interview_id": interview_id,
                    "total_evaluations": len(analyses),
                    "overall_score": round(overall_score, 2),
                    "strengths": list(set(all_strengths)),
                    "areas_for_improvement": list(set(all_improvements)),
                    "analyses": analyses
                }
            }

        except Exception as e:
            logger.error(f"❌ Error evaluating interview: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
