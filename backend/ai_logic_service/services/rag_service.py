"""
RAG-based explainability service for SkillScreen
Provides evidence-based explanations for all automated decisions
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import json
import re
from sentence_transformers import SentenceTransformer
import faiss
from collections import defaultdict
import logging

from database.models import (
    Interview, InterviewResponse, InterviewQuestion, 
    Candidate, Job, InterviewSummary
)
from utils.logger import log_info, log_error, log_warning

class RAGExplainabilityService:
    """RAG-based explainability service for transparent decision making"""
    
    def __init__(self):
        self.sentence_transformer = None
        self.knowledge_base = {}
        self.evidence_index = None
        self.evidence_documents = []
        self._initialize_rag_system()
    
    def _initialize_rag_system(self):
        """Initialize RAG system components"""
        try:
            log_info("Initializing RAG explainability system...")
            
            # Initialize sentence transformer for embeddings
            self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Initialize FAISS index for similarity search
            self.evidence_index = faiss.IndexFlatIP(384)  # 384 is the dimension of all-MiniLM-L6-v2
            
            # Load knowledge base
            self._load_knowledge_base()
            
            log_info("✅ RAG explainability system initialized")
            
        except Exception as e:
            log_error(f"❌ Failed to initialize RAG system: {e}")
            self._initialize_fallback_system()
    
    def _initialize_fallback_system(self):
        """Initialize fallback system without advanced components"""
        try:
            log_info("Initializing fallback RAG system...")
            self.knowledge_base = self._create_basic_knowledge_base()
            log_info("✅ Fallback RAG system initialized")
            
        except Exception as e:
            log_error(f"❌ Failed to initialize fallback system: {e}")
    
    def _load_knowledge_base(self):
        """Load knowledge base for explainability"""
        try:
            # Create comprehensive knowledge base
            self.knowledge_base = {
                'interview_best_practices': [
                    {
                        'content': 'Strong technical responses should include specific examples, technologies used, and measurable outcomes.',
                        'category': 'technical_assessment',
                        'evidence_type': 'best_practice'
                    },
                    {
                        'content': 'Effective communication involves clear structure, relevant examples, and appropriate detail level.',
                        'category': 'communication_assessment',
                        'evidence_type': 'best_practice'
                    },
                    {
                        'content': 'Job fit is demonstrated through alignment with role requirements, relevant experience, and cultural indicators.',
                        'category': 'job_fit_assessment',
                        'evidence_type': 'best_practice'
                    }
                ],
                'scoring_criteria': [
                    {
                        'content': 'Scores 8-10: Exceptional responses with specific examples, clear communication, and strong relevance.',
                        'category': 'scoring_guidelines',
                        'evidence_type': 'criteria'
                    },
                    {
                        'content': 'Scores 6-7: Good responses with adequate detail and relevance, minor areas for improvement.',
                        'category': 'scoring_guidelines',
                        'evidence_type': 'criteria'
                    },
                    {
                        'content': 'Scores 4-5: Average responses that address the question but lack depth or specificity.',
                        'category': 'scoring_guidelines',
                        'evidence_type': 'criteria'
                    },
                    {
                        'content': 'Scores 0-3: Poor responses that are off-topic, too brief, or demonstrate lack of knowledge.',
                        'category': 'scoring_guidelines',
                        'evidence_type': 'criteria'
                    }
                ],
                'anti_cheating_indicators': [
                    {
                        'content': 'Duplicate responses indicate lack of engagement or potential cheating behavior.',
                        'category': 'anti_cheating',
                        'evidence_type': 'detection_criteria'
                    },
                    {
                        'content': 'Suspiciously fast response times may indicate copy-paste behavior.',
                        'category': 'anti_cheating',
                        'evidence_type': 'detection_criteria'
                    },
                    {
                        'content': 'Off-topic responses suggest misunderstanding or lack of preparation.',
                        'category': 'anti_cheating',
                        'evidence_type': 'detection_criteria'
                    }
                ],
                'improvement_guidelines': [
                    {
                        'content': 'Use the STAR method (Situation, Task, Action, Result) for behavioral questions.',
                        'category': 'improvement_tips',
                        'evidence_type': 'guidance'
                    },
                    {
                        'content': 'Provide specific examples with quantifiable outcomes and technologies used.',
                        'category': 'improvement_tips',
                        'evidence_type': 'guidance'
                    },
                    {
                        'content': 'Structure responses with clear introduction, detailed explanation, and conclusion.',
                        'category': 'improvement_tips',
                        'evidence_type': 'guidance'
                    }
                ]
            }
            
            # Index knowledge base for retrieval
            self._index_knowledge_base()
            
        except Exception as e:
            log_error(f"Error loading knowledge base: {e}")
            self.knowledge_base = self._create_basic_knowledge_base()
    
    def _create_basic_knowledge_base(self):
        """Create basic knowledge base for fallback"""
        return {
            'basic_criteria': [
                'Responses should be relevant to the question asked',
                'Technical answers should include specific examples',
                'Communication should be clear and professional',
                'Responses should demonstrate job fit and experience'
            ]
        }
    
    def _index_knowledge_base(self):
        """Index knowledge base for efficient retrieval"""
        try:
            if not self.sentence_transformer:
                return
            
            all_documents = []
            for category, items in self.knowledge_base.items():
                for item in items:
                    document = {
                        'content': item['content'],
                        'category': item['category'],
                        'evidence_type': item['evidence_type'],
                        'source': category
                    }
                    all_documents.append(document)
            
            if all_documents:
                # Create embeddings
                texts = [doc['content'] for doc in all_documents]
                embeddings = self.sentence_transformer.encode(texts)
                
                # Normalize embeddings for cosine similarity
                faiss.normalize_L2(embeddings)
                
                # Add to FAISS index
                self.evidence_index.add(embeddings.astype('float32'))
                self.evidence_documents = all_documents
                
                log_info(f"Indexed {len(all_documents)} knowledge base documents")
            
        except Exception as e:
            log_error(f"Error indexing knowledge base: {e}")
    
    async def explain_response_evaluation(
        self,
        question: str,
        response: str,
        evaluation_scores: Dict[str, float],
        interview_id: str,
        db
    ) -> Dict:
        """Provide evidence-based explanation for response evaluation"""
        try:
            explanation = {
                'overall_explanation': '',
                'score_breakdown': {},
                'evidence_sources': [],
                'improvement_suggestions': [],
                'confidence_level': 0.0,
                'explanation_timestamp': datetime.utcnow().isoformat()
            }
            
            # Get relevant evidence for each score
            for score_name, score_value in evaluation_scores.items():
                score_explanation = await self._explain_score(
                    score_name, score_value, question, response, interview_id, db
                )
                explanation['score_breakdown'][score_name] = score_explanation
                explanation['evidence_sources'].extend(score_explanation.get('evidence', []))
            
            # Generate overall explanation
            explanation['overall_explanation'] = await self._generate_overall_explanation(
                evaluation_scores, explanation['score_breakdown']
            )
            
            # Generate improvement suggestions
            explanation['improvement_suggestions'] = await self._generate_improvement_suggestions(
                evaluation_scores, response, interview_id, db
            )
            
            # Calculate confidence level
            explanation['confidence_level'] = await self._calculate_explanation_confidence(
                evaluation_scores, explanation['evidence_sources']
            )
            
            return explanation
            
        except Exception as e:
            log_error(f"Error in response evaluation explanation: {e}")
            return self._fallback_explanation(evaluation_scores)
    
    async def _explain_score(
        self,
        score_name: str,
        score_value: float,
        question: str,
        response: str,
        interview_id: str,
        db
    ) -> Dict:
        """Explain a specific score with evidence"""
        try:
            # Retrieve relevant evidence
            evidence = await self._retrieve_evidence(
                f"{score_name} scoring criteria for {score_value}",
                score_name
            )
            
            # Analyze response characteristics
            response_analysis = await self._analyze_response_characteristics(
                response, score_name
            )
            
            # Generate explanation
            explanation = {
                'score': score_value,
                'explanation': '',
                'evidence': evidence,
                'response_analysis': response_analysis,
                'reasoning': ''
            }
            
            # Generate specific explanation based on score
            if score_value >= 8:
                explanation['explanation'] = f"Excellent {score_name.replace('_', ' ')} demonstrated through {response_analysis.get('strengths', [])}"
                explanation['reasoning'] = "Response meets or exceeds expectations for this criterion"
            elif score_value >= 6:
                explanation['explanation'] = f"Good {score_name.replace('_', ' ')} with room for improvement in {response_analysis.get('areas_for_improvement', [])}"
                explanation['reasoning'] = "Response meets basic expectations but could be enhanced"
            elif score_value >= 4:
                explanation['explanation'] = f"Average {score_name.replace('_', ' ')} that addresses the question but lacks depth"
                explanation['reasoning'] = "Response partially meets expectations but needs significant improvement"
            else:
                explanation['explanation'] = f"Below average {score_name.replace('_', ' ')} that requires substantial improvement"
                explanation['reasoning'] = "Response does not meet expectations for this criterion"
            
            return explanation
            
        except Exception as e:
            log_warning(f"Error explaining score {score_name}: {e}")
            return {
                'score': score_value,
                'explanation': f"Score of {score_value} for {score_name.replace('_', ' ')}",
                'evidence': [],
                'response_analysis': {},
                'reasoning': 'Basic scoring applied'
            }
    
    async def _retrieve_evidence(self, query: str, category: str) -> List[Dict]:
        """Retrieve relevant evidence for explanation"""
        try:
            if not self.sentence_transformer or not self.evidence_index:
                return self._get_fallback_evidence(category)
            
            # Create query embedding
            query_embedding = self.sentence_transformer.encode([query])
            faiss.normalize_L2(query_embedding)
            
            # Search for relevant evidence
            scores, indices = self.evidence_index.search(query_embedding.astype('float32'), k=3)
            
            evidence = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.evidence_documents):
                    doc = self.evidence_documents[idx]
                    evidence.append({
                        'content': doc['content'],
                        'category': doc['category'],
                        'evidence_type': doc['evidence_type'],
                        'relevance_score': float(score),
                        'source': doc['source']
                    })
            
            return evidence
            
        except Exception as e:
            log_warning(f"Error retrieving evidence: {e}")
            return self._get_fallback_evidence(category)
    
    def _get_fallback_evidence(self, category: str) -> List[Dict]:
        """Get fallback evidence when advanced retrieval fails"""
        fallback_evidence = {
            'technical_assessment': [
                {
                    'content': 'Technical responses should demonstrate specific knowledge and experience',
                    'category': 'technical_assessment',
                    'evidence_type': 'basic_criteria',
                    'relevance_score': 0.8,
                    'source': 'fallback'
                }
            ],
            'communication_assessment': [
                {
                    'content': 'Clear and professional communication is essential for effective responses',
                    'category': 'communication_assessment',
                    'evidence_type': 'basic_criteria',
                    'relevance_score': 0.8,
                    'source': 'fallback'
                }
            ],
            'relevance_score': [
                {
                    'content': 'Responses should directly address the question asked',
                    'category': 'relevance_assessment',
                    'evidence_type': 'basic_criteria',
                    'relevance_score': 0.8,
                    'source': 'fallback'
                }
            ]
        }
        
        return fallback_evidence.get(category, [
            {
                'content': 'Response evaluated based on standard criteria',
                'category': category,
                'evidence_type': 'basic_criteria',
                'relevance_score': 0.5,
                'source': 'fallback'
            }
        ])
    
    async def _analyze_response_characteristics(
        self,
        response: str,
        score_name: str
    ) -> Dict:
        """Analyze response characteristics for specific score"""
        try:
            analysis = {
                'strengths': [],
                'weaknesses': [],
                'characteristics': {}
            }
            
            response_lower = response.lower()
            word_count = len(response.split())
            
            # Analyze based on score type
            if 'technical' in score_name.lower():
                technical_indicators = ['experience', 'project', 'implemented', 'developed', 'technology']
                technical_count = sum(1 for indicator in technical_indicators if indicator in response_lower)
                
                if technical_count >= 3:
                    analysis['strengths'].append('Demonstrates technical experience')
                elif technical_count >= 1:
                    analysis['characteristics']['technical_depth'] = 'moderate'
                else:
                    analysis['weaknesses'].append('Lacks technical specificity')
            
            elif 'communication' in score_name.lower():
                if 50 <= word_count <= 200:
                    analysis['strengths'].append('Appropriate response length')
                elif word_count < 20:
                    analysis['weaknesses'].append('Response too brief')
                elif word_count > 300:
                    analysis['weaknesses'].append('Response too verbose')
                
                # Check for structure
                if any(indicator in response_lower for indicator in ['first', 'second', 'then', 'finally']):
                    analysis['strengths'].append('Well-structured response')
                else:
                    analysis['characteristics']['structure'] = 'basic'
            
            elif 'relevance' in score_name.lower():
                question_words = set(response_lower.split())
                response_words = set(response_lower.split())
                overlap = len(question_words.intersection(response_words))
                
                if overlap >= 3:
                    analysis['strengths'].append('Addresses question directly')
                elif overlap >= 1:
                    analysis['characteristics']['relevance'] = 'moderate'
                else:
                    analysis['weaknesses'].append('May not address question directly')
            
            return analysis
            
        except Exception as e:
            log_warning(f"Error analyzing response characteristics: {e}")
            return {'strengths': [], 'weaknesses': [], 'characteristics': {}}
    
    async def _generate_overall_explanation(
        self,
        evaluation_scores: Dict[str, float],
        score_breakdown: Dict[str, Dict]
    ) -> str:
        """Generate overall explanation for the evaluation"""
        try:
            overall_score = sum(evaluation_scores.values()) / len(evaluation_scores)
            
            # Identify strongest and weakest areas
            strongest_area = max(evaluation_scores.items(), key=lambda x: x[1])
            weakest_area = min(evaluation_scores.items(), key=lambda x: x[1])
            
            explanation_parts = []
            
            # Overall performance
            if overall_score >= 8:
                explanation_parts.append("The candidate demonstrated exceptional performance across all evaluation criteria.")
            elif overall_score >= 6:
                explanation_parts.append("The candidate showed good performance with solid responses in most areas.")
            elif overall_score >= 4:
                explanation_parts.append("The candidate provided adequate responses but showed room for improvement.")
            else:
                explanation_parts.append("The candidate's responses need significant improvement across multiple areas.")
            
            # Strongest area
            explanation_parts.append(
                f"The strongest area was {strongest_area[0].replace('_', ' ')} "
                f"with a score of {strongest_area[1]:.1f}, indicating {score_breakdown[strongest_area[0]].get('explanation', 'good performance')}."
            )
            
            # Weakest area
            if weakest_area[1] < strongest_area[1] - 2:  # Significant difference
                explanation_parts.append(
                    f"The area needing most improvement is {weakest_area[0].replace('_', ' ')} "
                    f"with a score of {weakest_area[1]:.1f}, suggesting {score_breakdown[weakest_area[0]].get('explanation', 'room for development')}."
                )
            
            return " ".join(explanation_parts)
            
        except Exception as e:
            log_warning(f"Error generating overall explanation: {e}")
            return "Response evaluated based on standard criteria with room for improvement."
    
    async def _generate_improvement_suggestions(
        self,
        evaluation_scores: Dict[str, float],
        response: str,
        interview_id: str,
        db
    ) -> List[str]:
        """Generate specific improvement suggestions"""
        try:
            suggestions = []
            
            # Get interview context
            interview = db.query(Interview).filter(Interview.id == interview_id).first()
            if interview:
                job = db.query(Job).filter(Job.id == interview.job_id).first()
                if job:
                    job_skills = job.skills_required or []
                else:
                    job_skills = []
            else:
                job_skills = []
            
            # Generate suggestions based on low scores
            for score_name, score_value in evaluation_scores.items():
                if score_value < 6:
                    if 'technical' in score_name.lower():
                        suggestions.append("Include specific technical examples and technologies used in your experience")
                        if job_skills:
                            suggestions.append(f"Highlight experience with: {', '.join(job_skills[:3])}")
                    
                    elif 'communication' in score_name.lower():
                        suggestions.append("Structure responses with clear introduction, detailed explanation, and conclusion")
                        suggestions.append("Use specific examples to illustrate your points")
                    
                    elif 'relevance' in score_name.lower():
                        suggestions.append("Listen carefully to questions and address them directly")
                        suggestions.append("Avoid generic responses and provide question-specific answers")
                    
                    elif 'depth' in score_name.lower():
                        suggestions.append("Provide more detailed explanations with quantifiable outcomes")
                        suggestions.append("Use the STAR method (Situation, Task, Action, Result) for behavioral questions")
            
            # General suggestions
            if len(response.split()) < 50:
                suggestions.append("Provide more detailed responses with specific examples")
            
            if not any(word in response.lower() for word in ['experience', 'project', 'work', 'team']):
                suggestions.append("Include relevant work experience and project examples")
            
            # Remove duplicates and limit to 5 suggestions
            unique_suggestions = list(dict.fromkeys(suggestions))
            return unique_suggestions[:5]
            
        except Exception as e:
            log_warning(f"Error generating improvement suggestions: {e}")
            return [
                "Provide more specific examples from your experience",
                "Structure responses more clearly",
                "Address questions more directly"
            ]
    
    async def _calculate_explanation_confidence(
        self,
        evaluation_scores: Dict[str, float],
        evidence_sources: List[Dict]
    ) -> float:
        """Calculate confidence level for the explanation"""
        try:
            # Base confidence on evidence quality and score consistency
            evidence_confidence = 0.0
            if evidence_sources:
                avg_relevance = sum(source.get('relevance_score', 0.5) for source in evidence_sources) / len(evidence_sources)
                evidence_confidence = avg_relevance
            
            # Score consistency (lower variance = higher confidence)
            score_values = list(evaluation_scores.values())
            if len(score_values) > 1:
                score_variance = np.var(score_values)
                consistency_confidence = max(0, 1 - (score_variance / 10))  # Normalize variance
            else:
                consistency_confidence = 0.8
            
            # Combine confidence factors
            total_confidence = (evidence_confidence * 0.6 + consistency_confidence * 0.4)
            
            return round(min(1.0, max(0.0, total_confidence)), 2)
            
        except Exception as e:
            log_warning(f"Error calculating explanation confidence: {e}")
            return 0.7  # Default confidence
    
    def _fallback_explanation(self, evaluation_scores: Dict[str, float]) -> Dict:
        """Provide fallback explanation when advanced analysis fails"""
        return {
            'overall_explanation': f"Response evaluated with overall score of {sum(evaluation_scores.values()) / len(evaluation_scores):.1f}/10",
            'score_breakdown': {
                score_name: {
                    'score': score_value,
                    'explanation': f"Score of {score_value} for {score_name.replace('_', ' ')}",
                    'evidence': [],
                    'response_analysis': {},
                    'reasoning': 'Basic evaluation applied'
                }
                for score_name, score_value in evaluation_scores.items()
            },
            'evidence_sources': [],
            'improvement_suggestions': [
                "Provide more specific examples",
                "Structure responses clearly",
                "Address questions directly"
            ],
            'confidence_level': 0.6,
            'explanation_timestamp': datetime.utcnow().isoformat()
        }
    
    async def explain_interview_summary(
        self,
        interview_summary: Dict,
        interview_id: str,
        db
    ) -> Dict:
        """Provide evidence-based explanation for interview summary"""
        try:
            explanation = {
                'summary_explanation': '',
                'recommendation_rationale': '',
                'key_factors': [],
                'evidence_links': [],
                'confidence_assessment': 0.0
            }
            
            # Get interview data
            interview = db.query(Interview).filter(Interview.id == interview_id).first()
            if not interview:
                return explanation
            
            responses = db.query(InterviewResponse).filter(
                InterviewResponse.interview_id == interview_id
            ).all()
            
            # Explain recommendation
            recommendation = interview_summary.get('recommendation', 'Consider')
            explanation['recommendation_rationale'] = await self._explain_recommendation(
                recommendation, interview_summary, responses
            )
            
            # Identify key factors
            explanation['key_factors'] = await self._identify_key_factors(
                interview_summary, responses
            )
            
            # Create evidence links
            explanation['evidence_links'] = await self._create_evidence_links(
                interview_summary, responses, interview_id
            )
            
            # Calculate confidence
            explanation['confidence_assessment'] = await self._assess_summary_confidence(
                interview_summary, responses
            )
            
            return explanation
            
        except Exception as e:
            log_error(f"Error explaining interview summary: {e}")
            return {
                'summary_explanation': 'Interview summary generated based on response analysis',
                'recommendation_rationale': 'Recommendation based on overall performance',
                'key_factors': ['Response quality', 'Technical knowledge', 'Communication'],
                'evidence_links': [],
                'confidence_assessment': 0.7
            }
    
    async def _explain_recommendation(
        self,
        recommendation: str,
        interview_summary: Dict,
        responses: List[InterviewResponse]
    ) -> str:
        """Explain the rationale behind the recommendation"""
        try:
            overall_score = interview_summary.get('overall_score', 0)
            strengths = interview_summary.get('strengths', [])
            weaknesses = interview_summary.get('areas_for_improvement', [])
            
            rationale_parts = []
            
            if recommendation == 'Hire':
                rationale_parts.append(f"Strong recommendation based on overall score of {overall_score:.1f}/10")
                if strengths:
                    rationale_parts.append(f"Key strengths include: {', '.join(strengths[:3])}")
            
            elif recommendation == 'Strong Consider':
                rationale_parts.append(f"Positive recommendation with score of {overall_score:.1f}/10")
                if strengths:
                    rationale_parts.append(f"Demonstrated strengths in: {', '.join(strengths[:2])}")
                if weaknesses:
                    rationale_parts.append(f"Areas for development: {', '.join(weaknesses[:2])}")
            
            elif recommendation == 'Consider':
                rationale_parts.append(f"Mixed recommendation with score of {overall_score:.1f}/10")
                if weaknesses:
                    rationale_parts.append(f"Significant areas for improvement: {', '.join(weaknesses[:2])}")
            
            else:  # Do Not Hire
                rationale_parts.append(f"Not recommended due to score of {overall_score:.1f}/10")
                if weaknesses:
                    rationale_parts.append(f"Critical issues identified: {', '.join(weaknesses[:3])}")
            
            return ". ".join(rationale_parts) + "."
            
        except Exception as e:
            log_warning(f"Error explaining recommendation: {e}")
            return f"Recommendation of {recommendation} based on overall interview performance."
    
    async def _identify_key_factors(
        self,
        interview_summary: Dict,
        responses: List[InterviewResponse]
    ) -> List[Dict]:
        """Identify key factors that influenced the evaluation"""
        try:
            key_factors = []
            
            # Overall score factor
            overall_score = interview_summary.get('overall_score', 0)
            key_factors.append({
                'factor': 'Overall Performance',
                'value': f"{overall_score:.1f}/10",
                'impact': 'high' if overall_score >= 7 else 'medium' if overall_score >= 5 else 'low',
                'description': 'Combined score across all evaluation criteria'
            })
            
            # Response count factor
            response_count = len(responses)
            if response_count < 10:
                key_factors.append({
                    'factor': 'Response Completeness',
                    'value': f"{response_count} responses",
                    'impact': 'medium',
                    'description': 'Limited responses may affect evaluation accuracy'
                })
            
            # Score consistency factor
            if responses:
                scores = [r.overall_score for r in responses if r.overall_score is not None]
                if scores:
                    score_variance = np.var(scores)
                    consistency = 'high' if score_variance < 2 else 'medium' if score_variance < 5 else 'low'
                    key_factors.append({
                        'factor': 'Response Consistency',
                        'value': consistency,
                        'impact': 'medium',
                        'description': f'Score variance of {score_variance:.2f} indicates {consistency} consistency'
                    })
            
            # Anti-cheating factors
            duplicate_responses = sum(1 for r in responses if r.is_duplicate)
            off_topic_responses = sum(1 for r in responses if r.is_off_topic)
            
            if duplicate_responses > 0:
                key_factors.append({
                    'factor': 'Duplicate Responses',
                    'value': f"{duplicate_responses} instances",
                    'impact': 'high',
                    'description': 'Repeated responses may indicate lack of engagement'
                })
            
            if off_topic_responses > 0:
                key_factors.append({
                    'factor': 'Off-topic Responses',
                    'value': f"{off_topic_responses} instances",
                    'impact': 'medium',
                    'description': 'Responses that don\'t address the questions asked'
                })
            
            return key_factors
            
        except Exception as e:
            log_warning(f"Error identifying key factors: {e}")
            return [
                {
                    'factor': 'Overall Performance',
                    'value': f"{interview_summary.get('overall_score', 0):.1f}/10",
                    'impact': 'medium',
                    'description': 'Combined evaluation score'
                }
            ]
    
    async def _create_evidence_links(
        self,
        interview_summary: Dict,
        responses: List[InterviewResponse],
        interview_id: str
    ) -> List[Dict]:
        """Create links to specific evidence supporting the evaluation"""
        try:
            evidence_links = []
            
            # Link to specific responses
            for i, response in enumerate(responses[:5]):  # Limit to first 5 responses
                evidence_links.append({
                    'type': 'response',
                    'title': f'Response {i+1}',
                    'score': response.overall_score,
                    'evidence': response.response_text[:100] + "..." if len(response.response_text) > 100 else response.response_text,
                    'timestamp': response.received_at.isoformat(),
                    'url': f'/api/interviews/{interview_id}/responses/{response.id}'
                })
            
            # Link to summary data
            evidence_links.append({
                'type': 'summary',
                'title': 'Interview Summary',
                'score': interview_summary.get('overall_score', 0),
                'evidence': interview_summary.get('executive_summary', '')[:100] + "...",
                'timestamp': datetime.utcnow().isoformat(),
                'url': f'/api/interviews/{interview_id}/summary'
            })
            
            return evidence_links
            
        except Exception as e:
            log_warning(f"Error creating evidence links: {e}")
            return []
    
    async def _assess_summary_confidence(
        self,
        interview_summary: Dict,
        responses: List[InterviewResponse]
    ) -> float:
        """Assess confidence level for the interview summary"""
        try:
            confidence_factors = []
            
            # Response count factor
            response_count = len(responses)
            if response_count >= 10:
                confidence_factors.append(0.9)
            elif response_count >= 5:
                confidence_factors.append(0.7)
            else:
                confidence_factors.append(0.5)
            
            # Score consistency factor
            if responses:
                scores = [r.overall_score for r in responses if r.overall_score is not None]
                if scores:
                    score_variance = np.var(scores)
                    if score_variance < 2:
                        confidence_factors.append(0.9)
                    elif score_variance < 5:
                        confidence_factors.append(0.7)
                    else:
                        confidence_factors.append(0.5)
            
            # Anti-cheating factor
            duplicate_count = sum(1 for r in responses if r.is_duplicate)
            off_topic_count = sum(1 for r in responses if r.is_off_topic)
            
            if duplicate_count == 0 and off_topic_count == 0:
                confidence_factors.append(0.9)
            elif duplicate_count <= 1 and off_topic_count <= 1:
                confidence_factors.append(0.7)
            else:
                confidence_factors.append(0.5)
            
            # Calculate overall confidence
            overall_confidence = sum(confidence_factors) / len(confidence_factors)
            return round(overall_confidence, 2)
            
        except Exception as e:
            log_warning(f"Error assessing summary confidence: {e}")
            return 0.7
