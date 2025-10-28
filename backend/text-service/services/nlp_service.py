"""
Advanced NLP service for SkillScreen using Hugging Face Transformers and sentence-transformers
"""

import torch
from sentence_transformers import SentenceTransformer
from transformers import (
    AutoTokenizer, AutoModelForSequenceClassification,
    pipeline, AutoModel
)
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json

from database.models import Candidate, Job, InterviewResponse
from utils.logger import log_info, log_error, log_warning

class NLPService:
    """Advanced NLP service for interview response evaluation"""
    
    def __init__(self):
        self.models = {}
        self.tokenizers = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize all NLP models"""
        try:
            log_info("Initializing NLP models...")
            
            # Sentence transformer for semantic similarity
            self.models['sentence_transformer'] = SentenceTransformer(
                'all-MiniLM-L6-v2',  # Lightweight but effective
                device='cuda' if torch.cuda.is_available() else 'cpu'
            )
            
            # Sentiment analysis model
            self.models['sentiment'] = pipeline(
                'sentiment-analysis',
                model='cardiffnlp/twitter-roberta-base-sentiment-latest',
                device=0 if torch.cuda.is_available() else -1
            )
            
            # Text classification for relevance
            self.models['relevance_classifier'] = pipeline(
                'text-classification',
                model='microsoft/DialoGPT-medium',
                device=0 if torch.cuda.is_available() else -1
            )
            
            # Question-answering model for context understanding
            self.models['qa_model'] = pipeline(
                'question-answering',
                model='distilbert-base-cased-distilled-squad',
                device=0 if torch.cuda.is_available() else -1
            )
            
            # Text summarization for concise feedback
            self.models['summarizer'] = pipeline(
                'summarization',
                model='facebook/bart-large-cnn',
                device=0 if torch.cuda.is_available() else -1
            )
            
            log_info("✅ NLP models initialized successfully")
            
        except Exception as e:
            log_error(f"❌ Failed to initialize NLP models: {e}")
            # Fallback to basic models
            self._initialize_fallback_models()
    
    def _initialize_fallback_models(self):
        """Initialize fallback models if advanced ones fail"""
        try:
            log_info("Initializing fallback NLP models...")
            
            # Basic sentence transformer
            self.models['sentence_transformer'] = SentenceTransformer(
                'paraphrase-MiniLM-L3-v2'
            )
            
            # Basic sentiment analysis
            self.models['sentiment'] = pipeline(
                'sentiment-analysis',
                model='distilbert-base-uncased-finetuned-sst-2-english'
            )
            
            log_info("✅ Fallback NLP models initialized")
            
        except Exception as e:
            log_error(f"❌ Failed to initialize fallback models: {e}")
            self.models = {}
    
    async def evaluate_response(
        self,
        question: str,
        response: str,
        candidate_id: str,
        job_id: str,
        db
    ) -> Dict:
        """Comprehensive response evaluation using multiple NLP models"""
        try:
            if not self.models:
                return self._fallback_evaluation(question, response)
            
            # Run evaluations in parallel
            tasks = [
                self._evaluate_relevance(question, response),
                self._evaluate_sentiment(response),
                self._evaluate_technical_accuracy(question, response, job_id, db),
                self._evaluate_communication_quality(response),
                self._evaluate_depth_and_completeness(response),
                self._evaluate_job_fit(response, candidate_id, job_id, db)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Extract scores
            relevance_score = results[0] if not isinstance(results[0], Exception) else 5.0
            sentiment_score = results[1] if not isinstance(results[1], Exception) else 5.0
            technical_score = results[2] if not isinstance(results[2], Exception) else 5.0
            communication_score = results[3] if not isinstance(results[3], Exception) else 5.0
            depth_score = results[4] if not isinstance(results[4], Exception) else 5.0
            job_fit_score = results[5] if not isinstance(results[5], Exception) else 5.0
            
            # Calculate overall score with weighted average
            weights = {
                'relevance': 0.25,
                'technical': 0.20,
                'communication': 0.20,
                'depth': 0.15,
                'job_fit': 0.20
            }
            
            overall_score = (
                relevance_score * weights['relevance'] +
                technical_score * weights['technical'] +
                communication_score * weights['communication'] +
                depth_score * weights['depth'] +
                job_fit_score * weights['job_fit']
            )
            
            # Generate feedback
            feedback = await self._generate_feedback(
                question, response, {
                    'relevance': relevance_score,
                    'technical': technical_score,
                    'communication': communication_score,
                    'depth': depth_score,
                    'job_fit': job_fit_score
                }
            )
            
            # Extract strengths and weaknesses
            strengths, weaknesses = await self._extract_strengths_weaknesses(
                response, {
                    'relevance': relevance_score,
                    'technical': technical_score,
                    'communication': communication_score,
                    'depth': depth_score,
                    'job_fit': job_fit_score
                }
            )
            
            return {
                'overall_score': round(overall_score, 1),
                'relevance_score': round(relevance_score, 1),
                'technical_accuracy_score': round(technical_score, 1),
                'communication_score': round(communication_score, 1),
                'depth_score': round(depth_score, 1),
                'job_fit_score': round(job_fit_score, 1),
                'feedback': feedback,
                'strengths': strengths,
                'weaknesses': weaknesses,
                'improvement_tips': await self._generate_improvement_tips(strengths, weaknesses),
                'sentiment_analysis': sentiment_score,
                'evaluation_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            log_error(f"Error in NLP evaluation: {e}")
            return self._fallback_evaluation(question, response)
    
    async def _evaluate_relevance(self, question: str, response: str) -> float:
        """Evaluate how relevant the response is to the question"""
        try:
            if 'sentence_transformer' not in self.models:
                return self._basic_relevance_check(question, response)
            
            # Get embeddings
            embeddings = self.models['sentence_transformer'].encode([question, response])
            
            # Calculate cosine similarity
            similarity = np.dot(embeddings[0], embeddings[1]) / (
                np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
            )
            
            # Convert to 0-10 scale
            score = max(0, min(10, similarity * 10))
            
            # Additional relevance checks
            question_keywords = set(question.lower().split())
            response_words = set(response.lower().split())
            
            # Check for question-specific keywords
            keyword_overlap = len(question_keywords.intersection(response_words))
            keyword_score = min(10, keyword_overlap * 2)
            
            # Combine semantic similarity with keyword overlap
            final_score = (score * 0.7) + (keyword_score * 0.3)
            
            return round(final_score, 1)
            
        except Exception as e:
            log_warning(f"Error in relevance evaluation: {e}")
            return self._basic_relevance_check(question, response)
    
    async def _evaluate_sentiment(self, response: str) -> float:
        """Evaluate sentiment and tone of the response"""
        try:
            if 'sentiment' not in self.models:
                return 5.0
            
            result = self.models['sentiment'](response)
            
            # Convert sentiment to score
            if result[0]['label'] == 'POSITIVE':
                score = 7.0 + (result[0]['score'] * 3.0)  # 7-10 range
            elif result[0]['label'] == 'NEUTRAL':
                score = 5.0 + (result[0]['score'] * 2.0)  # 5-7 range
            else:  # NEGATIVE
                score = max(0, 5.0 - (result[0]['score'] * 5.0))  # 0-5 range
            
            return round(score, 1)
            
        except Exception as e:
            log_warning(f"Error in sentiment evaluation: {e}")
            return 5.0
    
    async def _evaluate_technical_accuracy(
        self, 
        question: str, 
        response: str, 
        job_id: str, 
        db
    ) -> float:
        """Evaluate technical accuracy based on job requirements"""
        try:
            # Get job requirements
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                return 5.0
            
            required_skills = job.skills_required or []
            if not required_skills:
                return 5.0
            
            # Check for technical keywords in response
            response_lower = response.lower()
            technical_score = 0
            
            for skill in required_skills:
                if skill.lower() in response_lower:
                    technical_score += 2
            
            # Normalize score
            max_possible = len(required_skills) * 2
            if max_possible > 0:
                score = min(10, (technical_score / max_possible) * 10)
            else:
                score = 5.0
            
            # Additional technical depth analysis
            technical_indicators = [
                'experience', 'project', 'implemented', 'developed',
                'architecture', 'algorithm', 'optimization', 'performance',
                'scalability', 'security', 'testing', 'debugging'
            ]
            
            technical_depth = sum(1 for indicator in technical_indicators 
                                if indicator in response_lower)
            depth_bonus = min(2, technical_depth * 0.5)
            
            return round(min(10, score + depth_bonus), 1)
            
        except Exception as e:
            log_warning(f"Error in technical evaluation: {e}")
            return 5.0
    
    async def _evaluate_communication_quality(self, response: str) -> float:
        """Evaluate communication clarity and professionalism"""
        try:
            # Basic metrics
            word_count = len(response.split())
            sentence_count = len([s for s in response.split('.') if s.strip()])
            
            # Length appropriateness (not too short, not too long)
            if word_count < 10:
                length_score = 2.0
            elif word_count < 50:
                length_score = 5.0
            elif word_count < 200:
                length_score = 8.0
            else:
                length_score = 6.0  # Too long can be negative
            
            # Sentence structure
            avg_sentence_length = word_count / max(1, sentence_count)
            if 10 <= avg_sentence_length <= 20:
                structure_score = 8.0
            elif 5 <= avg_sentence_length <= 30:
                structure_score = 6.0
            else:
                structure_score = 4.0
            
            # Professional language indicators
            professional_words = [
                'collaborate', 'implement', 'optimize', 'analyze',
                'strategize', 'facilitate', 'coordinate', 'manage'
            ]
            
            professional_score = min(2, sum(1 for word in professional_words 
                                          if word in response.lower()) * 0.5)
            
            # Grammar and spelling (basic check)
            grammar_score = 6.0  # Default, could be enhanced with grammar checking
            
            total_score = (length_score * 0.3 + structure_score * 0.3 + 
                          professional_score * 0.2 + grammar_score * 0.2)
            
            return round(min(10, total_score), 1)
            
        except Exception as e:
            log_warning(f"Error in communication evaluation: {e}")
            return 5.0
    
    async def _evaluate_depth_and_completeness(self, response: str) -> float:
        """Evaluate depth and completeness of the response"""
        try:
            # Check for specific examples
            example_indicators = [
                'for example', 'specifically', 'in my experience',
                'one time', 'recently', 'last year', 'at my previous job'
            ]
            
            has_examples = any(indicator in response.lower() 
                             for indicator in example_indicators)
            example_score = 8.0 if has_examples else 4.0
            
            # Check for quantifiable information
            numbers = sum(1 for word in response.split() if word.isdigit())
            quantifiable_score = min(8.0, 5.0 + numbers * 0.5)
            
            # Check for detailed explanations
            detail_indicators = [
                'because', 'therefore', 'as a result', 'due to',
                'in order to', 'the reason', 'this allowed'
            ]
            
            has_details = any(indicator in response.lower() 
                            for indicator in detail_indicators)
            detail_score = 7.0 if has_details else 4.0
            
            # Response completeness
            word_count = len(response.split())
            if word_count < 20:
                completeness_score = 3.0
            elif word_count < 100:
                completeness_score = 6.0
            else:
                completeness_score = 8.0
            
            total_score = (example_score * 0.3 + quantifiable_score * 0.2 + 
                          detail_score * 0.3 + completeness_score * 0.2)
            
            return round(min(10, total_score), 1)
            
        except Exception as e:
            log_warning(f"Error in depth evaluation: {e}")
            return 5.0
    
    async def _evaluate_job_fit(
        self, 
        response: str, 
        candidate_id: str, 
        job_id: str, 
        db
    ) -> float:
        """Evaluate how well the response demonstrates job fit"""
        try:
            # Get candidate and job information
            candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            job = db.query(Job).filter(Job.id == job_id).first()
            
            if not candidate or not job:
                return 5.0
            
            # Check alignment with job requirements
            job_skills = job.skills_required or []
            candidate_skills = candidate.skills or []
            
            # Skill alignment
            skill_overlap = len(set(job_skills).intersection(set(candidate_skills)))
            skill_score = min(8.0, skill_overlap * 2.0) if job_skills else 5.0
            
            # Experience level alignment
            experience_score = 5.0
            if candidate.experience_years:
                if job.experience_level == 'Junior' and candidate.experience_years <= 2:
                    experience_score = 8.0
                elif job.experience_level == 'Mid-level' and 2 <= candidate.experience_years <= 5:
                    experience_score = 8.0
                elif job.experience_level == 'Senior' and candidate.experience_years >= 5:
                    experience_score = 8.0
            
            # Response mentions relevant experience
            response_lower = response.lower()
            relevance_indicators = [
                'relevant', 'applicable', 'transferable', 'similar',
                'related experience', 'background in', 'expertise in'
            ]
            
            relevance_score = min(7.0, 5.0 + sum(1 for indicator in relevance_indicators 
                                                if indicator in response_lower) * 0.5)
            
            total_score = (skill_score * 0.4 + experience_score * 0.3 + relevance_score * 0.3)
            
            return round(min(10, total_score), 1)
            
        except Exception as e:
            log_warning(f"Error in job fit evaluation: {e}")
            return 5.0
    
    async def _generate_feedback(
        self, 
        question: str, 
        response: str, 
        scores: Dict[str, float]
    ) -> str:
        """Generate constructive feedback based on scores"""
        try:
            feedback_parts = []
            
            # Overall feedback
            overall_score = sum(scores.values()) / len(scores)
            if overall_score >= 8:
                feedback_parts.append("Excellent response with strong demonstration of relevant skills and experience.")
            elif overall_score >= 6:
                feedback_parts.append("Good response showing solid understanding and relevant experience.")
            elif overall_score >= 4:
                feedback_parts.append("Adequate response that addresses the question but could be more detailed.")
            else:
                feedback_parts.append("Response needs improvement in addressing the question and providing relevant details.")
            
            # Specific feedback based on scores
            if scores['relevance'] < 6:
                feedback_parts.append("Consider focusing more directly on the specific question asked.")
            
            if scores['technical'] < 6:
                feedback_parts.append("Include more specific technical details and examples from your experience.")
            
            if scores['communication'] < 6:
                feedback_parts.append("Work on structuring your response more clearly and professionally.")
            
            if scores['depth'] < 6:
                feedback_parts.append("Provide more detailed examples and explanations to strengthen your response.")
            
            return " ".join(feedback_parts)
            
        except Exception as e:
            log_warning(f"Error generating feedback: {e}")
            return "Response received and evaluated."
    
    async def _extract_strengths_weaknesses(
        self, 
        response: str, 
        scores: Dict[str, float]
    ) -> Tuple[List[str], List[str]]:
        """Extract strengths and weaknesses from the response"""
        try:
            strengths = []
            weaknesses = []
            
            # Analyze scores to determine strengths and weaknesses
            if scores['relevance'] >= 7:
                strengths.append("Directly addresses the question asked")
            elif scores['relevance'] <= 4:
                weaknesses.append("Could better focus on the specific question")
            
            if scores['technical'] >= 7:
                strengths.append("Demonstrates strong technical knowledge")
            elif scores['technical'] <= 4:
                weaknesses.append("Needs more technical depth and specific examples")
            
            if scores['communication'] >= 7:
                strengths.append("Clear and professional communication")
            elif scores['communication'] <= 4:
                weaknesses.append("Communication could be more structured and clear")
            
            if scores['depth'] >= 7:
                strengths.append("Provides detailed and comprehensive answers")
            elif scores['depth'] <= 4:
                weaknesses.append("Responses could be more detailed and specific")
            
            if scores['job_fit'] >= 7:
                strengths.append("Shows strong alignment with role requirements")
            elif scores['job_fit'] <= 4:
                weaknesses.append("Could better demonstrate fit for the specific role")
            
            # Default if no specific strengths/weaknesses identified
            if not strengths:
                strengths.append("Participated actively in the interview")
            if not weaknesses:
                weaknesses.append("Continue developing interview skills")
            
            return strengths, weaknesses
            
        except Exception as e:
            log_warning(f"Error extracting strengths/weaknesses: {e}")
            return ["Response evaluated"], ["Continue professional development"]
    
    async def _generate_improvement_tips(
        self, 
        strengths: List[str], 
        weaknesses: List[str]
    ) -> List[str]:
        """Generate improvement tips based on strengths and weaknesses"""
        try:
            tips = []
            
            # Tips based on weaknesses
            if any("technical" in w.lower() for w in weaknesses):
                tips.append("Prepare specific technical examples from your experience")
            
            if any("communication" in w.lower() for w in weaknesses):
                tips.append("Practice structuring responses with clear examples and explanations")
            
            if any("relevance" in w.lower() for w in weaknesses):
                tips.append("Listen carefully to questions and address them directly")
            
            if any("depth" in w.lower() for w in weaknesses):
                tips.append("Provide more detailed examples and quantify your achievements")
            
            # General tips
            tips.extend([
                "Use the STAR method (Situation, Task, Action, Result) for behavioral questions",
                "Prepare specific examples that demonstrate your skills and experience",
                "Practice explaining technical concepts in simple terms"
            ])
            
            return tips[:5]  # Limit to 5 tips
            
        except Exception as e:
            log_warning(f"Error generating improvement tips: {e}")
            return ["Continue professional development"]
    
    def _basic_relevance_check(self, question: str, response: str) -> float:
        """Basic relevance check without advanced models"""
        try:
            question_words = set(question.lower().split())
            response_words = set(response.lower().split())
            
            # Simple word overlap
            overlap = len(question_words.intersection(response_words))
            total_question_words = len(question_words)
            
            if total_question_words == 0:
                return 5.0
            
            relevance_ratio = overlap / total_question_words
            score = min(10, relevance_ratio * 10)
            
            return round(score, 1)
            
        except Exception as e:
            log_warning(f"Error in basic relevance check: {e}")
            return 5.0
    
    def _fallback_evaluation(self, question: str, response: str) -> Dict:
        """Fallback evaluation when advanced models are unavailable"""
        try:
            # Basic scoring based on response characteristics
            word_count = len(response.split())
            
            # Length-based scoring
            if word_count < 10:
                base_score = 2.0
            elif word_count < 50:
                base_score = 5.0
            elif word_count < 200:
                base_score = 7.0
            else:
                base_score = 6.0
            
            # Relevance check
            relevance_score = self._basic_relevance_check(question, response)
            
            # Overall score
            overall_score = (base_score + relevance_score) / 2
            
            return {
                'overall_score': round(overall_score, 1),
                'relevance_score': round(relevance_score, 1),
                'technical_accuracy_score': round(base_score, 1),
                'communication_score': round(base_score, 1),
                'depth_score': round(base_score, 1),
                'job_fit_score': round(base_score, 1),
                'feedback': "Response evaluated using basic analysis. Advanced NLP models unavailable.",
                'strengths': ["Participated in interview"],
                'weaknesses': ["Advanced analysis unavailable"],
                'improvement_tips': ["Continue professional development"],
                'evaluation_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            log_error(f"Error in fallback evaluation: {e}")
            return {
                'overall_score': 5.0,
                'relevance_score': 5.0,
                'technical_accuracy_score': 5.0,
                'communication_score': 5.0,
                'depth_score': 5.0,
                'job_fit_score': 5.0,
                'feedback': "Evaluation completed with basic scoring.",
                'strengths': ["Completed interview"],
                'weaknesses': ["Analysis limited"],
                'improvement_tips': ["Continue professional development"],
                'evaluation_timestamp': datetime.utcnow().isoformat()
            }
