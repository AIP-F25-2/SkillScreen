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

from database.models import Interview, Response, AuditLog
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
        self.MAX_AI_GENERATED_WARNINGS = 2  # Maximum AI-generated content warnings
        self.AI_DETECTION_CONFIDENCE_THRESHOLD = 0.4  # Minimum confidence for AI detection
        
    async def analyze_response(
        self,
        response_text: str,
        interview_id: str,
        db,
        response_time_seconds: Optional[float] = None
    ) -> Dict:
        """Comprehensive anti-cheating analysis - supports both database and in-memory storage"""
        try:
            analysis_results = {
                'is_duplicate': False,
                'is_off_topic': False,
                'should_terminate': False,
                'duplicate_count': 0,
                'off_topic_count': 0,
                'ai_generated_count': 0,
                'flags': [],
                'confidence': 0.0,
                'warnings': [],
                'termination_message': None
            }
            
            # Support both database and in-memory storage
            previous_responses = []
            
            if db:
                # Database path
                interview = db.query(Interview).filter(Interview.id == interview_id).first()
                if interview:
                    previous_responses = db.query(Response).filter(
                        Response.interview_id == interview_id
                    ).order_by(Response.created_at).all()
            else:
                # In-memory storage path
                try:
                    from in_memory_storage import get_responses
                    responses_data = get_responses(interview_id)
                    # Convert to Response-like objects
                    class MockResponse:
                        def __init__(self, data):
                            self.response_text = data.get("response_text", "")
                            self.created_at = data.get("created_at")
                    
                    previous_responses = [MockResponse(r) for r in responses_data]
                except Exception as e:
                    log_warning(f"Could not get previous responses from in-memory storage: {e}")
                    previous_responses = []
            
            # 1. Duplicate response detection
            duplicate_analysis = await self._detect_duplicate_responses(
                response_text, previous_responses
            )
            analysis_results.update(duplicate_analysis)
            
            # 2. Timing analysis (skip if no interview object for in-memory)
            if db:
                interview = db.query(Interview).filter(Interview.id == interview_id).first()
                if interview:
                    timing_analysis = await self._analyze_response_timing(
                        response_time_seconds, interview_id, interview
                    )
                    analysis_results.update(timing_analysis)
            
            # 3. Content analysis (skip if no interview object for in-memory)
            if db:
                interview = db.query(Interview).filter(Interview.id == interview_id).first()
                if interview:
                    content_analysis = await self._analyze_response_content(
                        response_text, interview, previous_responses
                    )
                    analysis_results.update(content_analysis)
            
            # 4. Behavioral pattern analysis (works with in-memory)
            behavior_analysis = await self._analyze_behavioral_patterns(
                response_text, interview_id, previous_responses
            )
            analysis_results.update(behavior_analysis)
            
            # 5. AI-generated content analysis (works with in-memory)
            ai_analysis = await self._analyze_ai_generated_content(
                response_text, interview_id, previous_responses
            )
            analysis_results.update(ai_analysis)
            
            # 6. Determine if interview should be terminated
            termination_decision = await self._determine_termination(
                analysis_results, previous_responses
            )
            analysis_results.update(termination_decision)
            
            # 7. Log audit trail (skip if no db)
            if db:
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
        previous_responses: List
    ) -> Dict:
        """Detect duplicate or near-duplicate responses using LLM for better detection - supports both database and in-memory"""
        try:
            if not previous_responses:
                return {
                    'is_duplicate': False,
                    'duplicate_count': 0,
                    'similarity_score': 0.0
                }
            
            # Use LLM for duplicate detection if available
            try:
                from services.llm_service import llm_service
                if llm_service.gemini_model:
                    # Use LLM to check for duplicates
                    prev_responses_text = "\n".join([
                        f"Response {i+1}: {r.response_text if hasattr(r, 'response_text') else r.get('response_text', '')}"
                        for i, r in enumerate(previous_responses[-5:])  # Check last 5 responses
                    ])
                    
                    duplicate_check_prompt = f"""Check if the following new response is a duplicate or very similar to any of the previous responses.

Previous Responses:
{prev_responses_text}

New Response:
{response_text}

Analyze if the new response:
1. Is identical or nearly identical to any previous response
2. Contains the same key points or information
3. Is a copy-paste or minimal variation

Respond with JSON format:
{{
    "is_duplicate": true/false,
    "similarity_score": 0.0-1.0,
    "duplicate_count": number of similar responses found,
    "reason": "explanation"
}}"""
                    
                    import asyncio
                    loop = asyncio.get_event_loop()
                    llm_response = await loop.run_in_executor(
                        None,
                        lambda: llm_service.gemini_model.generate_content(duplicate_check_prompt)
                    )
                    
                    if llm_response and llm_response.text:
                        import json
                        try:
                            # Try to extract JSON from response
                            response_text_clean = llm_response.text.strip()
                            # Remove markdown code blocks if present
                            if '```json' in response_text_clean:
                                response_text_clean = response_text_clean.split('```json')[1].split('```')[0]
                            elif '```' in response_text_clean:
                                response_text_clean = response_text_clean.split('```')[1].split('```')[0]
                            
                            duplicate_result = json.loads(response_text_clean)
                            if duplicate_result.get('is_duplicate', False):
                                log_warning(f"[ANTI-CHEAT] LLM detected duplicate response: {duplicate_result.get('reason', 'Similar to previous response')}")
                                return {
                                    'is_duplicate': True,
                                    'duplicate_count': duplicate_result.get('duplicate_count', 1),
                                    'similarity_score': duplicate_result.get('similarity_score', 0.85),
                                    'reason': duplicate_result.get('reason', 'LLM detected similarity')
                                }
                        except:
                            pass  # Fall through to rule-based detection
            except Exception as e:
                log_warning(f"[WARNING] LLM duplicate detection failed: {e}, using rule-based")
            
            # Fallback: Rule-based duplicate detection
            # Normalize response text
            normalized_response = self._normalize_text(response_text)
            duplicate_count = 0
            max_similarity = 0.0
            
            for prev_response in previous_responses:
                # Support both database Response objects and in-memory dictionaries
                if isinstance(prev_response, dict):
                    prev_text = prev_response.get("response_text", "")
                else:
                    prev_text = getattr(prev_response, "response_text", "")
                
                if not prev_text:
                    continue
                
                normalized_prev = self._normalize_text(prev_text)
                similarity = self._calculate_similarity(normalized_response, normalized_prev)
                
                if similarity >= self.DUPLICATE_THRESHOLD:
                    duplicate_count += 1
                    max_similarity = max(max_similarity, similarity)
            
            # Check for exact duplicates using SHA-256
            response_hash = hashlib.sha256(normalized_response.encode()).hexdigest()
            exact_duplicates = 0
            for resp in previous_responses:
                if isinstance(resp, dict):
                    resp_text = resp.get("response_text", "")
                else:
                    resp_text = getattr(resp, "response_text", "")
                
                if resp_text:
                    resp_hash = hashlib.sha256(self._normalize_text(resp_text).encode()).hexdigest()
                    if resp_hash == response_hash:
                        exact_duplicates += 1
            
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
        previous_responses: List[Response]
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
            ai_analysis = self._detect_ai_generated_content(response_text)
            if ai_analysis['is_ai_generated']:
                flags.append(f"AI-generated content detected (confidence: {ai_analysis['confidence']:.2f})")
                flags.extend(ai_analysis['indicators'])
            
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
        previous_responses: List[Response]
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
    
    async def _analyze_ai_generated_content(
        self,
        response_text: str,
        interview_id: str,
        previous_responses: List[Response]
    ) -> Dict:
        """Analyze AI-generated content with warning system"""
        try:
            # Initialize AI tracking for this interview
            if interview_id not in self.behavior_patterns:
                self.behavior_patterns[interview_id] = {
                    'ai_generated_count': 0,
                    'ai_warnings': 0,
                    'ai_confidence_scores': []
                }
            
            behavior_data = self.behavior_patterns[interview_id]
            
            # Detect AI-generated content
            ai_analysis = self._detect_ai_generated_content(response_text)
            
            result = {
                'is_ai_generated': ai_analysis['is_ai_generated'],
                'ai_confidence': ai_analysis['confidence'],
                'ai_indicators': ai_analysis['indicators'],
                'ai_patterns': ai_analysis['patterns'],
                'ai_generated_count': behavior_data['ai_generated_count'],
                'ai_warnings': behavior_data['ai_warnings']
            }
            
            # If AI-generated content detected
            if ai_analysis['is_ai_generated']:
                behavior_data['ai_generated_count'] += 1
                behavior_data['ai_confidence_scores'].append(ai_analysis['confidence'])
                
                # Generate warning message
                if behavior_data['ai_warnings'] < self.MAX_AI_GENERATED_WARNINGS:
                    behavior_data['ai_warnings'] += 1
                    warning_message = self._generate_ai_warning_message(
                        behavior_data['ai_warnings'], 
                        ai_analysis['indicators']
                    )
                    result['warnings'] = [warning_message]
                else:
                    # Final warning - interview will be terminated
                    termination_message = self._generate_ai_termination_message(
                        behavior_data['ai_generated_count'],
                        ai_analysis['indicators']
                    )
                    result['termination_message'] = termination_message
                    result['should_terminate'] = True
            
            return result
            
        except Exception as e:
            log_warning(f"Error in AI content analysis: {e}")
            return {
                'is_ai_generated': False,
                'ai_confidence': 0.0,
                'ai_indicators': [],
                'ai_patterns': [],
                'ai_generated_count': 0,
                'ai_warnings': 0
            }
    
    def _generate_ai_warning_message(self, warning_count: int, indicators: List[str]) -> str:
        """Generate warning message for AI-generated content"""
        if warning_count == 1:
            return (
                "[WARNING] WARNING: Your response appears to be AI-generated or copied from external sources. "
                "Please provide original, personal responses based on your own experience. "
                "This is your first warning - continued use of AI-generated content will result in interview termination."
            )
        elif warning_count == 2:
            return (
                "🚨 FINAL WARNING: This is your second warning for AI-generated content. "
                "Please provide genuine, personal responses. "
                "Any further AI-generated responses will result in immediate interview termination with a score of 0."
            )
        else:
            return "AI-generated content detected. Please provide original responses."
    
    def _generate_ai_termination_message(self, ai_count: int, indicators: List[str]) -> str:
        """Generate termination message for excessive AI-generated content"""
        return (
            "❌ INTERVIEW TERMINATED: Your interview has been terminated due to repeated use of AI-generated content. "
            f"This was detected {ai_count} times during the interview. "
            "Your final score is 0/10. "
            "Please note that using AI tools or copying responses from external sources violates the interview integrity policy. "
            "For future interviews, please provide original, personal responses based on your own experience and knowledge."
        )
    
    async def _determine_termination(
        self,
        analysis_results: Dict,
        previous_responses: List[Response]
    ) -> Dict:
        """Determine if interview should be terminated with enhanced logic"""
        try:
            should_terminate = False
            termination_reason = None
            termination_message = None
            
            # Check for AI-generated content termination
            if analysis_results.get('should_terminate', False) and analysis_results.get('termination_message'):
                should_terminate = True
                termination_reason = 'excessive_ai_generated_content'
                termination_message = analysis_results.get('termination_message')
            
            # Check for excessive duplicates
            elif analysis_results.get('duplicate_count', 0) >= self.MAX_DUPLICATES:
                should_terminate = True
                termination_reason = 'excessive_duplicate_responses'
                termination_message = self._generate_duplicate_termination_message(
                    analysis_results.get('duplicate_count', 0)
                )
            
            # Check for multiple suspicious flags
            else:
                all_flags = (
                    analysis_results.get('flags', []) +
                    analysis_results.get('timing_flags', []) +
                    analysis_results.get('content_flags', []) +
                    analysis_results.get('behavioral_flags', [])
                )
                
                if len(all_flags) >= 5:
                    should_terminate = True
                    termination_reason = 'multiple_suspicious_activities'
                    termination_message = self._generate_suspicious_termination_message(len(all_flags))
                
                # Check for off-topic responses
                elif analysis_results.get('is_off_topic', False):
                    # Count off-topic responses (support both database and in-memory)
                    off_topic_count = 0
                    for resp in previous_responses:
                        if isinstance(resp, dict):
                            if resp.get('is_off_topic', False):
                                off_topic_count += 1
                        else:
                            if getattr(resp, 'is_off_topic', False):
                                off_topic_count += 1
                    
                    if off_topic_count >= 3:
                        should_terminate = True
                        termination_reason = 'excessive_off_topic_responses'
                        termination_message = self._generate_offtopic_termination_message(off_topic_count)
            
            # Calculate confidence score
            all_flags = (
                analysis_results.get('flags', []) +
                analysis_results.get('timing_flags', []) +
                analysis_results.get('content_flags', []) +
                analysis_results.get('behavioral_flags', [])
            )
            confidence = min(1.0, len(all_flags) / 10.0)
            
            return {
                'should_terminate': should_terminate,
                'termination_reason': termination_reason,
                'termination_message': termination_message,
                'confidence': confidence,
                'total_flags': len(all_flags)
            }
            
        except Exception as e:
            log_warning(f"Error in termination determination: {e}")
            return {
                'should_terminate': False,
                'termination_reason': None,
                'termination_message': None,
                'confidence': 0.0
            }
    
    def _generate_duplicate_termination_message(self, duplicate_count: int) -> str:
        """Generate termination message for duplicate responses"""
        return (
            f"❌ INTERVIEW TERMINATED: Your interview has been terminated due to repeated duplicate responses. "
            f"This was detected {duplicate_count} times during the interview. "
            "Your final score is 0/10. "
            "Please note that providing the same or very similar responses to different questions violates the interview integrity policy. "
            "For future interviews, please provide unique, thoughtful responses to each question."
        )
    
    def _generate_suspicious_termination_message(self, flag_count: int) -> str:
        """Generate termination message for suspicious activities"""
        return (
            f"❌ INTERVIEW TERMINATED: Your interview has been terminated due to multiple suspicious activities detected. "
            f"{flag_count} suspicious patterns were identified during the interview. "
            "Your final score is 0/10. "
            "Please note that suspicious behavior such as copy-pasting, using external tools, or providing inappropriate responses violates the interview integrity policy. "
            "For future interviews, please ensure you provide original, honest responses based on your own knowledge and experience."
        )
    
    def _generate_offtopic_termination_message(self, offtopic_count: int) -> str:
        """Generate termination message for off-topic responses"""
        return (
            f"❌ INTERVIEW TERMINATED: Your interview has been terminated due to excessive off-topic responses. "
            f"{offtopic_count} off-topic responses were detected during the interview. "
            "Your final score is 0/10. "
            "Please note that providing irrelevant or off-topic responses violates the interview integrity policy. "
            "For future interviews, please ensure you understand each question and provide relevant, thoughtful responses."
        )
    
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
        previous_responses: List
    ) -> List[str]:
        """Detect phrases repeated across responses - supports both database and in-memory"""
        try:
            # Extract phrases (2-4 word combinations)
            current_phrases = self._extract_phrases(response_text)
            repeated_phrases = []
            
            for prev_response in previous_responses[-3:]:  # Check last 3 responses
                # Support both database Response objects and in-memory dictionaries
                if isinstance(prev_response, dict):
                    prev_text = prev_response.get("response_text", "")
                else:
                    prev_text = getattr(prev_response, "response_text", "")
                
                if not prev_text:
                    continue
                
                prev_phrases = self._extract_phrases(prev_text)
                
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
    
    def _detect_ai_generated_content(self, text: str) -> Dict:
        """Detect possible AI-generated content patterns with detailed analysis"""
        try:
            analysis = {
                'is_ai_generated': False,
                'confidence': 0.0,
                'indicators': [],
                'patterns': []
            }
            
            text_lower = text.lower()
            confidence_score = 0.0
            indicators = []
            patterns = []
            
            # 1. AI-specific phrases and transitions
            ai_phrases = [
                'in conclusion', 'furthermore', 'moreover', 'additionally',
                'it is important to note', 'it should be noted', 'it is worth mentioning',
                'as previously mentioned', 'as stated earlier', 'to summarize',
                'in summary', 'it is crucial to', 'it is essential to',
                'it is imperative to', 'it is vital to', 'it is necessary to',
                'it is worth noting that', 'it is important to understand',
                'it is worth considering', 'it is worth highlighting'
            ]
            
            ai_phrase_count = sum(1 for phrase in ai_phrases if phrase in text_lower)
            if ai_phrase_count > 0:
                confidence_score += ai_phrase_count * 0.15
                indicators.append(f"AI transition phrases detected ({ai_phrase_count})")
                patterns.append("excessive_formal_transitions")
            
            # 2. Overly formal and corporate language
            formal_words = [
                'utilize', 'facilitate', 'implement', 'optimize', 'leverage',
                'streamline', 'enhance', 'maximize', 'minimize', 'prioritize',
                'strategize', 'methodology', 'paradigm', 'framework',
                'synergy', 'holistic', 'comprehensive', 'robust', 'scalable'
            ]
            
            formal_count = sum(1 for word in formal_words if word in text_lower)
            if formal_count >= 3:
                confidence_score += min(0.3, formal_count * 0.08)
                indicators.append(f"Excessive formal language ({formal_count} instances)")
                patterns.append("overly_corporate_tone")
            
            # 3. Repetitive sentence structures
            sentences = [s.strip() for s in text.split('.') if s.strip()]
            if len(sentences) >= 3:
                sentence_lengths = [len(sent.split()) for sent in sentences]
                length_variance = np.var(sentence_lengths) if len(sentence_lengths) > 1 else 0
                
                if length_variance < 5:  # Very similar sentence lengths
                    confidence_score += 0.2
                    indicators.append("Repetitive sentence structures")
                    patterns.append("uniform_sentence_length")
                
                # Check for similar sentence starts
                sentence_starts = [sent.split()[0].lower() if sent.split() else '' for sent in sentences]
                start_repetition = len(set(sentence_starts)) / len(sentence_starts) if sentence_starts else 1
                if start_repetition < 0.5:  # Many sentences start the same way
                    confidence_score += 0.15
                    indicators.append("Repetitive sentence beginnings")
                    patterns.append("repetitive_sentence_starts")
            
            # 4. Lack of personal pronouns and specific details
            personal_indicators = ['i', 'me', 'my', 'we', 'our', 'us']
            personal_count = sum(1 for word in personal_indicators if word in text_lower)
            total_words = len(text.split())
            
            if total_words > 20 and personal_count / total_words < 0.05:  # Less than 5% personal pronouns
                confidence_score += 0.2
                indicators.append("Lack of personal pronouns and specific details")
                patterns.append("impersonal_tone")
            
            # 5. Perfect grammar and structure (too perfect)
            # Check for complex sentence structures that are too perfect
            complex_structures = [
                'not only', 'but also', 'in order to', 'so as to',
                'provided that', 'in the event that', 'with regard to',
                'in terms of', 'with respect to', 'in accordance with'
            ]
            
            complex_count = sum(1 for structure in complex_structures if structure in text_lower)
            if complex_count >= 2 and len(text.split()) < 100:  # Too many complex structures in short text
                confidence_score += 0.15
                indicators.append("Overly complex sentence structures")
                patterns.append("excessive_complexity")
            
            # 6. Generic responses without specific examples
            generic_phrases = [
                'it depends', 'it varies', 'generally speaking', 'in most cases',
                'typically', 'usually', 'often', 'frequently', 'commonly'
            ]
            
            generic_count = sum(1 for phrase in generic_phrases if phrase in text_lower)
            if generic_count >= 3:
                confidence_score += 0.1
                indicators.append("Excessive generic language")
                patterns.append("generic_responses")
            
            # 7. Check for ChatGPT-like responses
            chatgpt_patterns = [
                'as an ai', 'i don\'t have personal', 'i cannot provide',
                'i\'m not able to', 'i don\'t have access to', 'i cannot',
                'i don\'t have the ability to', 'i\'m designed to',
                'my training data', 'i was trained on'
            ]
            
            chatgpt_count = sum(1 for pattern in chatgpt_patterns if pattern in text_lower)
            if chatgpt_count > 0:
                confidence_score += 0.4
                indicators.append("ChatGPT-like response patterns")
                patterns.append("chatgpt_indicators")
            
            # 8. Check for copy-paste from AI tools
            ai_tool_indicators = [
                'here\'s a', 'here is a', 'let me', 'i\'ll help you',
                'i can help you', 'i\'d be happy to', 'i\'m here to help',
                'i can assist you', 'i can provide', 'i can offer'
            ]
            
            tool_count = sum(1 for indicator in ai_tool_indicators if indicator in text_lower)
            if tool_count > 0:
                confidence_score += 0.3
                indicators.append("AI assistant response patterns")
                patterns.append("ai_assistant_tone")
            
            # 9. Check for perfect bullet points or numbered lists
            if text.count('•') > 2 or text.count('1.') > 2 or text.count('-') > 3:
                confidence_score += 0.1
                indicators.append("Overly structured formatting")
                patterns.append("excessive_formatting")
            
            # 10. Check for lack of natural speech patterns
            natural_patterns = ['um', 'uh', 'like', 'you know', 'i mean', 'actually', 'basically']
            natural_count = sum(1 for pattern in natural_patterns if pattern in text_lower)
            
            if len(text.split()) > 50 and natural_count == 0:  # Long response with no natural speech patterns
                confidence_score += 0.1
                indicators.append("Lack of natural speech patterns")
                patterns.append("unnatural_formality")
            
            # Determine if AI-generated based on confidence score
            analysis['is_ai_generated'] = confidence_score >= 0.4
            analysis['confidence'] = min(1.0, confidence_score)
            analysis['indicators'] = indicators
            analysis['patterns'] = patterns
            
            return analysis
            
        except Exception as e:
            log_warning(f"Error detecting AI-generated content: {e}")
            return {
                'is_ai_generated': False,
                'confidence': 0.0,
                'indicators': [],
                'patterns': []
            }
    
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
    
    def _calculate_question_engagement(self, response_text: str, previous_responses: List) -> float:
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
