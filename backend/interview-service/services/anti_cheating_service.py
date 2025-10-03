"""
Advanced anti-cheating service for SkillScreen
"""

import re
import time
import hashlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict, deque
import logging

from database.models import Interview, InterviewResponse, AuditLog
from utils.logger import log_info, log_error, log_warning

class AntiCheatingService:
    """Advanced anti-cheating detection service"""
    
    def __init__(self):
        self.response_cache = {}  # Cache for response analysis
        self.timing_patterns = {}  # Track timing patterns per interview
        self.behavior_patterns = {}  # Track behavior patterns
        
        # Thresholds for detection
        self.DUPLICATE_THRESHOLD = 0.85  # Similarity threshold for duplicates
        self.TIMING_SUSPICIOUS_THRESHOLD = 2.0  # Seconds - too fast responses
        self.TIMING_TOO_SLOW_THRESHOLD = 300.0  # 5 minutes - too slow
        self.MIN_RESPONSE_LENGTH = 10  # Minimum response length
        self.MAX_DUPLICATES = 2  # Maximum allowed duplicate responses
        
    async def analyze_response(
        self,
        response_text: str,
        interview_id: str,
        db,
        response_time_seconds: Optional[float] = None
    ) -> Dict:
        """Comprehensive anti-cheating analysis"""
        try:
            analysis_results = {
                'is_duplicate': False,
                'is_off_topic': False,
                'should_terminate': False,
                'duplicate_count': 0,
                'off_topic_count': 0,
                'flags': [],
                'confidence': 0.0
            }
            
            # Get interview and previous responses
            interview = db.query(Interview).filter(Interview.id == interview_id).first()
            if not interview:
                return analysis_results
            
            previous_responses = db.query(InterviewResponse).filter(
                InterviewResponse.interview_id == interview_id
            ).order_by(InterviewResponse.received_at).all()
            
            # 1. Duplicate response detection
            duplicate_analysis = await self._detect_duplicate_responses(
                response_text, previous_responses
            )
            analysis_results.update(duplicate_analysis)
            
            # 2. Timing analysis
            timing_analysis = await self._analyze_response_timing(
                response_time_seconds, interview_id, interview
            )
            analysis_results.update(timing_analysis)
            
            # 3. Content analysis
            content_analysis = await self._analyze_response_content(
                response_text, interview, previous_responses
            )
            analysis_results.update(content_analysis)
            
            # 4. Behavioral pattern analysis
            behavior_analysis = await self._analyze_behavioral_patterns(
                response_text, interview_id, previous_responses
            )
            analysis_results.update(behavior_analysis)
            
            # 5. Determine if interview should be terminated
            termination_decision = await self._determine_termination(
                analysis_results, previous_responses
            )
            analysis_results.update(termination_decision)
            
            # 6. Log audit trail
            await self._log_anti_cheating_analysis(
                interview_id, response_text, analysis_results, db
            )
            
            return analysis_results
            
        except Exception as e:
            log_error(f"Error in anti-cheating analysis: {e}")
            return {
                'is_duplicate': False,
                'is_off_topic': False,
                'should_terminate': False,
                'duplicate_count': 0,
                'off_topic_count': 0,
                'flags': ['Analysis error'],
                'confidence': 0.0
            }
    
    async def _detect_duplicate_responses(
        self,
        response_text: str,
        previous_responses: List[InterviewResponse]
    ) -> Dict:
        """Detect duplicate or near-duplicate responses"""
        try:
            if not previous_responses:
                return {
                    'is_duplicate': False,
                    'duplicate_count': 0,
                    'similarity_score': 0.0
                }
            
            # Normalize response text
            normalized_response = self._normalize_text(response_text)
            duplicate_count = 0
            max_similarity = 0.0
            
            for prev_response in previous_responses:
                normalized_prev = self._normalize_text(prev_response.response_text)
                similarity = self._calculate_similarity(normalized_response, normalized_prev)
                
                if similarity >= self.DUPLICATE_THRESHOLD:
                    duplicate_count += 1
                    max_similarity = max(max_similarity, similarity)
            
            # Check for exact duplicates
            response_hash = hashlib.md5(normalized_response.encode()).hexdigest()
            exact_duplicates = sum(1 for resp in previous_responses 
                                 if hashlib.md5(self._normalize_text(resp.response_text).encode()).hexdigest() == response_hash)
            
            is_duplicate = duplicate_count > 0 or exact_duplicates > 0
            
            return {
                'is_duplicate': is_duplicate,
                'duplicate_count': max(duplicate_count, exact_duplicates),
                'similarity_score': max_similarity,
                'flags': ['Duplicate response detected'] if is_duplicate else []
            }
            
        except Exception as e:
            log_warning(f"Error in duplicate detection: {e}")
            return {
                'is_duplicate': False,
                'duplicate_count': 0,
                'similarity_score': 0.0
            }
    
    async def _analyze_response_timing(
        self,
        response_time_seconds: Optional[float],
        interview_id: str,
        interview: Interview
    ) -> Dict:
        """Analyze response timing patterns"""
        try:
            if response_time_seconds is None:
                return {'timing_flags': []}
            
            # Initialize timing patterns for this interview
            if interview_id not in self.timing_patterns:
                self.timing_patterns[interview_id] = {
                    'response_times': deque(maxlen=10),
                    'average_time': 0.0,
                    'suspicious_count': 0
                }
            
            timing_data = self.timing_patterns[interview_id]
            timing_data['response_times'].append(response_time_seconds)
            
            # Calculate average response time
            if len(timing_data['response_times']) > 1:
                timing_data['average_time'] = np.mean(list(timing_data['response_times']))
            
            flags = []
            
            # Check for suspiciously fast responses
            if response_time_seconds < self.TIMING_SUSPICIOUS_THRESHOLD:
                flags.append('Response time suspiciously fast')
                timing_data['suspicious_count'] += 1
            
            # Check for responses that are too slow
            if response_time_seconds > self.TIMING_TOO_SLOW_THRESHOLD:
                flags.append('Response time unusually slow')
            
            # Check for inconsistent timing patterns
            if len(timing_data['response_times']) >= 3:
                times = list(timing_data['response_times'])
                if max(times) / min(times) > 10:  # Very inconsistent timing
                    flags.append('Inconsistent response timing patterns')
            
            # Check for copy-paste timing (very fast responses)
            if response_time_seconds < 1.0 and len(response_text) > 100:
                flags.append('Possible copy-paste behavior')
            
            return {
                'timing_flags': flags,
                'response_time': response_time_seconds,
                'average_response_time': timing_data['average_time'],
                'suspicious_timing_count': timing_data['suspicious_count']
            }
            
        except Exception as e:
            log_warning(f"Error in timing analysis: {e}")
            return {'timing_flags': []}
    
    async def _analyze_response_content(
        self,
        response_text: str,
        interview: Interview,
        previous_responses: List[InterviewResponse]
    ) -> Dict:
        """Analyze response content for suspicious patterns"""
        try:
            flags = []
            
            # Check response length
            if len(response_text.strip()) < self.MIN_RESPONSE_LENGTH:
                flags.append('Response too short')
            
            # Check for generic responses
            generic_phrases = [
                'i don\'t know', 'not sure', 'can\'t remember',
                'no idea', 'not applicable', 'n/a', 'none',
                'same as before', 'as mentioned', 'like i said'
            ]
            
            response_lower = response_text.lower()
            generic_count = sum(1 for phrase in generic_phrases if phrase in response_lower)
            if generic_count >= 2:
                flags.append('Multiple generic responses detected')
            
            # Check for repeated phrases across responses
            if len(previous_responses) >= 2:
                repeated_phrases = self._detect_repeated_phrases(response_text, previous_responses)
                if repeated_phrases:
                    flags.append(f'Repeated phrases detected: {repeated_phrases[:3]}')
            
            # Check for off-topic responses
            is_off_topic = await self._detect_off_topic_response(response_text, interview)
            if is_off_topic:
                flags.append('Response appears off-topic')
            
            # Check for AI-generated content patterns
            ai_patterns = self._detect_ai_generated_content(response_text)
            if ai_patterns:
                flags.append('Possible AI-generated content')
            
            return {
                'content_flags': flags,
                'is_off_topic': is_off_topic,
                'response_length': len(response_text),
                'generic_phrase_count': generic_count
            }
            
        except Exception as e:
            log_warning(f"Error in content analysis: {e}")
            return {'content_flags': []}
    
    async def _analyze_behavioral_patterns(
        self,
        response_text: str,
        interview_id: str,
        previous_responses: List[InterviewResponse]
    ) -> Dict:
        """Analyze behavioral patterns across responses"""
        try:
            if interview_id not in self.behavior_patterns:
                self.behavior_patterns[interview_id] = {
                    'response_lengths': [],
                    'complexity_scores': [],
                    'question_engagement': []
                }
            
            behavior_data = self.behavior_patterns[interview_id]
            flags = []
            
            # Track response length patterns
            response_length = len(response_text.split())
            behavior_data['response_lengths'].append(response_length)
            
            # Check for declining engagement
            if len(behavior_data['response_lengths']) >= 3:
                recent_lengths = behavior_data['response_lengths'][-3:]
                if all(recent_lengths[i] >= recent_lengths[i+1] for i in range(len(recent_lengths)-1)):
                    flags.append('Declining response engagement detected')
            
            # Track complexity (simple heuristic)
            complexity_score = self._calculate_complexity_score(response_text)
            behavior_data['complexity_scores'].append(complexity_score)
            
            # Check for complexity patterns
            if len(behavior_data['complexity_scores']) >= 3:
                recent_complexity = behavior_data['complexity_scores'][-3:]
                if all(recent_complexity[i] >= recent_complexity[i+1] for i in range(len(recent_complexity)-1)):
                    flags.append('Declining response complexity detected')
            
            # Check for question-specific engagement
            question_engagement = self._calculate_question_engagement(response_text, previous_responses)
            behavior_data['question_engagement'].append(question_engagement)
            
            return {
                'behavioral_flags': flags,
                'response_length': response_length,
                'complexity_score': complexity_score,
                'question_engagement': question_engagement
            }
            
        except Exception as e:
            log_warning(f"Error in behavioral analysis: {e}")
            return {'behavioral_flags': []}
    
    async def _determine_termination(
        self,
        analysis_results: Dict,
        previous_responses: List[InterviewResponse]
    ) -> Dict:
        """Determine if interview should be terminated"""
        try:
            should_terminate = False
            termination_reason = None
            
            # Check for excessive duplicates
            if analysis_results.get('duplicate_count', 0) >= self.MAX_DUPLICATES:
                should_terminate = True
                termination_reason = 'excessive_duplicate_responses'
            
            # Check for multiple suspicious flags
            all_flags = (
                analysis_results.get('flags', []) +
                analysis_results.get('timing_flags', []) +
                analysis_results.get('content_flags', []) +
                analysis_results.get('behavioral_flags', [])
            )
            
            if len(all_flags) >= 5:
                should_terminate = True
                termination_reason = 'multiple_suspicious_activities'
            
            # Check for off-topic responses
            if analysis_results.get('is_off_topic', False):
                off_topic_count = sum(1 for resp in previous_responses if resp.is_off_topic)
                if off_topic_count >= 3:
                    should_terminate = True
                    termination_reason = 'excessive_off_topic_responses'
            
            # Calculate confidence score
            confidence = min(1.0, len(all_flags) / 10.0)
            
            return {
                'should_terminate': should_terminate,
                'termination_reason': termination_reason,
                'confidence': confidence,
                'total_flags': len(all_flags)
            }
            
        except Exception as e:
            log_warning(f"Error in termination determination: {e}")
            return {
                'should_terminate': False,
                'termination_reason': None,
                'confidence': 0.0
            }
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove punctuation
        text = re.sub(r'[^\w\s]', '', text)
        
        # Remove common words
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = [word for word in text.split() if word not in common_words]
        
        return ' '.join(words)
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _detect_repeated_phrases(
        self,
        response_text: str,
        previous_responses: List[InterviewResponse]
    ) -> List[str]:
        """Detect phrases repeated across responses"""
        try:
            # Extract phrases (2-4 word combinations)
            current_phrases = self._extract_phrases(response_text)
            repeated_phrases = []
            
            for prev_response in previous_responses[-3:]:  # Check last 3 responses
                prev_phrases = self._extract_phrases(prev_response.response_text)
                
                for phrase in current_phrases:
                    if phrase in prev_phrases and len(phrase.split()) >= 3:
                        repeated_phrases.append(phrase)
            
            return list(set(repeated_phrases))
            
        except Exception as e:
            log_warning(f"Error detecting repeated phrases: {e}")
            return []
    
    def _extract_phrases(self, text: str) -> List[str]:
        """Extract phrases from text"""
        try:
            words = text.lower().split()
            phrases = []
            
            # Extract 2-4 word phrases
            for i in range(len(words) - 1):
                for length in range(2, min(5, len(words) - i + 1)):
                    phrase = ' '.join(words[i:i+length])
                    if len(phrase) > 10:  # Only meaningful phrases
                        phrases.append(phrase)
            
            return phrases
            
        except Exception as e:
            log_warning(f"Error extracting phrases: {e}")
            return []
    
    async def _detect_off_topic_response(
        self,
        response_text: str,
        interview: Interview
    ) -> bool:
        """Detect if response is off-topic"""
        try:
            # This is a simplified version - in production, you'd use NLP models
            response_lower = response_text.lower()
            
            # Check for completely irrelevant responses
            irrelevant_indicators = [
                'i don\'t understand', 'what do you mean', 'can you repeat',
                'i\'m not sure what you\'re asking', 'this doesn\'t make sense'
            ]
            
            if any(indicator in response_lower for indicator in irrelevant_indicators):
                return True
            
            # Check for responses that are too generic
            if len(response_text.split()) < 5:
                return True
            
            # Check for responses that don't contain relevant keywords
            # This would be enhanced with job-specific keywords in production
            relevant_keywords = [
                'experience', 'project', 'work', 'team', 'develop',
                'implement', 'manage', 'create', 'build', 'solve'
            ]
            
            if not any(keyword in response_lower for keyword in relevant_keywords):
                return True
            
            return False
            
        except Exception as e:
            log_warning(f"Error detecting off-topic response: {e}")
            return False
    
    def _detect_ai_generated_content(self, text: str) -> bool:
        """Detect possible AI-generated content patterns"""
        try:
            # Simple heuristics for AI-generated content
            ai_indicators = [
                'in conclusion', 'furthermore', 'moreover', 'additionally',
                'it is important to note', 'it should be noted', 'it is worth mentioning',
                'as previously mentioned', 'as stated earlier'
            ]
            
            text_lower = text.lower()
            ai_count = sum(1 for indicator in ai_indicators if indicator in text_lower)
            
            # Check for overly formal language
            formal_words = ['utilize', 'facilitate', 'implement', 'optimize', 'leverage']
            formal_count = sum(1 for word in formal_words if word in text_lower)
            
            # Check for repetitive sentence structures
            sentences = text.split('.')
            if len(sentences) >= 3:
                sentence_lengths = [len(sent.split()) for sent in sentences if sent.strip()]
                if len(set(sentence_lengths)) <= 2:  # Very similar sentence lengths
                    return True
            
            return ai_count >= 2 or formal_count >= 3
            
        except Exception as e:
            log_warning(f"Error detecting AI-generated content: {e}")
            return False
    
    def _calculate_complexity_score(self, text: str) -> float:
        """Calculate text complexity score"""
        try:
            if not text:
                return 0.0
            
            words = text.split()
            if not words:
                return 0.0
            
            # Simple complexity metrics
            avg_word_length = sum(len(word) for word in words) / len(words)
            sentence_count = len([s for s in text.split('.') if s.strip()])
            avg_sentence_length = len(words) / max(1, sentence_count)
            
            # Vocabulary diversity (simple type-token ratio)
            unique_words = len(set(word.lower() for word in words))
            vocabulary_diversity = unique_words / len(words)
            
            # Combine metrics
            complexity_score = (
                avg_word_length * 0.3 +
                avg_sentence_length * 0.3 +
                vocabulary_diversity * 10 * 0.4
            )
            
            return min(10.0, complexity_score)
            
        except Exception as e:
            log_warning(f"Error calculating complexity score: {e}")
            return 5.0
    
    def _calculate_question_engagement(self, response_text: str, previous_responses: List[InterviewResponse]) -> float:
        """Calculate how well the response engages with the question"""
        try:
            if not response_text:
                return 0.0
            
            # Check for question-specific language
            engagement_indicators = [
                'in my experience', 'for example', 'specifically',
                'when i', 'i have', 'i was', 'i did', 'i worked',
                'the project', 'the team', 'the company'
            ]
            
            response_lower = response_text.lower()
            engagement_count = sum(1 for indicator in engagement_indicators if indicator in response_lower)
            
            # Normalize to 0-10 scale
            engagement_score = min(10.0, engagement_count * 2.0)
            
            return engagement_score
            
        except Exception as e:
            log_warning(f"Error calculating question engagement: {e}")
            return 5.0
    
    async def _log_anti_cheating_analysis(
        self,
        interview_id: str,
        response_text: str,
        analysis_results: Dict,
        db
    ):
        """Log anti-cheating analysis for audit trail"""
        try:
            audit_log = AuditLog(
                action="anti_cheating_analysis",
                entity_type="interview_response",
                entity_id=interview_id,
                metadata={
                    "analysis_results": analysis_results,
                    "response_length": len(response_text),
                    "flags_detected": len(analysis_results.get('flags', []))
                },
                details=f"Anti-cheating analysis completed for interview {interview_id}"
            )
            
            db.add(audit_log)
            db.commit()
            
        except Exception as e:
            log_warning(f"Error logging anti-cheating analysis: {e}")
    
    def cleanup_old_data(self, max_age_hours: int = 24):
        """Clean up old timing and behavior patterns"""
        try:
            current_time = datetime.utcnow()
            cutoff_time = current_time - timedelta(hours=max_age_hours)
            
            # This would be implemented with proper timestamp tracking
            # For now, just clear old data periodically
            if len(self.timing_patterns) > 1000:
                self.timing_patterns.clear()
                self.behavior_patterns.clear()
                log_info("Cleaned up old anti-cheating data")
                
        except Exception as e:
            log_warning(f"Error cleaning up anti-cheating data: {e}")
