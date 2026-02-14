"""
ML-Based Behavioral Analysis Service for SkillScreen
Uses machine learning models to analyze candidate behavior patterns during interviews
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone
from collections import deque
import logging
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import pickle
import os

from database.models import Interview, Response
from utils.logger import log_info, log_error, log_warning

class BehavioralAnalysisService:
    """ML-based service for analyzing candidate behavioral patterns"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.isolation_forest = None
        self.kmeans_clusterer = None
        self.behavior_profiles = {}  # Store behavior profiles per interview
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize ML models for behavioral analysis"""
        try:
            log_info("Initializing ML-based behavioral analysis models...")
            
            # Isolation Forest for anomaly detection
            self.isolation_forest = IsolationForest(
                contamination=0.1,  # Expect 10% anomalies
                random_state=42,
                n_estimators=100
            )
            
            # KMeans for behavior clustering
            self.kmeans_clusterer = KMeans(
                n_clusters=4,  # 4 behavior types: engaged, declining, consistent, erratic
                random_state=42,
                n_init=10
            )
            
            log_info("[OK] ML-based behavioral analysis models initialized")
            
        except Exception as e:
            log_error(f"[ERROR] Failed to initialize behavioral analysis models: {e}")
            self.isolation_forest = None
            self.kmeans_clusterer = None
    
    async def analyze_behavioral_patterns(
        self,
        response_text: str,
        interview_id: str,
        response_time_seconds: Optional[float] = None,
        question_number: int = 0
    ) -> Dict:
        """Comprehensive ML-based behavioral pattern analysis"""
        try:
            # Initialize behavior profile for this interview
            if interview_id not in self.behavior_profiles:
                self.behavior_profiles[interview_id] = {
                    'response_lengths': deque(maxlen=20),
                    'complexity_scores': deque(maxlen=20),
                    'response_times': deque(maxlen=20),
                    'engagement_scores': deque(maxlen=20),
                    'sentiment_scores': deque(maxlen=20),
                    'question_numbers': deque(maxlen=20),
                    'features': []
                }
            
            profile = self.behavior_profiles[interview_id]
            
            # Extract features from current response
            features = self._extract_behavioral_features(
                response_text, response_time_seconds, question_number
            )
            
            # Add to profile
            profile['response_lengths'].append(features['response_length'])
            profile['complexity_scores'].append(features['complexity_score'])
            if response_time_seconds:
                profile['response_times'].append(response_time_seconds)
            profile['engagement_scores'].append(features['engagement_score'])
            profile['question_numbers'].append(question_number)
            profile['features'].append(features)
            
            # Perform ML-based analysis if we have enough data
            analysis_results = {
                'behavior_type': 'unknown',
                'anomaly_score': 0.0,
                'engagement_trend': 'stable',
                'consistency_score': 0.0,
                'behavioral_flags': [],
                'confidence': 0.0,
                'ml_predictions': {}
            }
            
            if len(profile['response_lengths']) >= 3:
                # ML-based analysis
                ml_results = self._ml_behavioral_analysis(profile)
                analysis_results.update(ml_results)
            
            # Pattern-based analysis (fallback and supplement)
            pattern_results = self._pattern_based_analysis(profile)
            analysis_results['behavioral_flags'].extend(pattern_results.get('flags', []))
            
            # Combine ML and pattern-based results
            if analysis_results['behavior_type'] == 'unknown' and pattern_results.get('behavior_type'):
                analysis_results['behavior_type'] = pattern_results['behavior_type']
            
            return analysis_results
            
        except Exception as e:
            log_error(f"Error in behavioral pattern analysis: {e}")
            return {
                'behavior_type': 'unknown',
                'anomaly_score': 0.0,
                'engagement_trend': 'stable',
                'consistency_score': 0.0,
                'behavioral_flags': [],
                'confidence': 0.0
            }
    
    def _extract_behavioral_features(
        self,
        response_text: str,
        response_time_seconds: Optional[float],
        question_number: int
    ) -> Dict[str, float]:
        """Extract features for ML models"""
        try:
            words = response_text.split()
            sentences = [s.strip() for s in response_text.split('.') if s.strip()]
            
            features = {
                'response_length': len(words),
                'sentence_count': len(sentences),
                'avg_sentence_length': len(words) / max(1, len(sentences)),
                'complexity_score': self._calculate_complexity_score(response_text),
                'engagement_score': self._calculate_engagement_score(response_text),
                'question_number': question_number,
                'response_time': response_time_seconds or 0.0,
                'personal_pronouns': sum(1 for word in words if word.lower() in ['i', 'me', 'my', 'we', 'our']),
                'specific_examples': sum(1 for word in words if word.lower() in ['example', 'specifically', 'instance', 'case']),
                'uncertainty_markers': sum(1 for word in words if word.lower() in ['maybe', 'perhaps', 'might', 'could', 'possibly']),
                'confidence_markers': sum(1 for word in words if word.lower() in ['definitely', 'certainly', 'absolutely', 'sure']),
            }
            
            # Normalize counts by response length
            if features['response_length'] > 0:
                features['personal_pronoun_ratio'] = features['personal_pronouns'] / features['response_length']
                features['example_ratio'] = features['specific_examples'] / features['response_length']
                features['uncertainty_ratio'] = features['uncertainty_markers'] / features['response_length']
                features['confidence_ratio'] = features['confidence_markers'] / features['response_length']
            else:
                features['personal_pronoun_ratio'] = 0.0
                features['example_ratio'] = 0.0
                features['uncertainty_ratio'] = 0.0
                features['confidence_ratio'] = 0.0
            
            return features
            
        except Exception as e:
            log_warning(f"Error extracting behavioral features: {e}")
            return {
                'response_length': 0.0,
                'complexity_score': 0.0,
                'engagement_score': 0.0,
                'question_number': question_number,
                'response_time': 0.0
            }
    
    def _ml_behavioral_analysis(self, profile: Dict) -> Dict:
        """Perform ML-based behavioral analysis"""
        try:
            if not self.isolation_forest or len(profile['features']) < 3:
                return {}
            
            # Prepare feature matrix
            feature_names = [
                'response_length', 'complexity_score', 'engagement_score',
                'personal_pronoun_ratio', 'example_ratio', 'uncertainty_ratio',
                'confidence_ratio'
            ]
            
            feature_matrix = []
            for features in profile['features']:
                row = [features.get(name, 0.0) for name in feature_names]
                feature_matrix.append(row)
            
            feature_matrix = np.array(feature_matrix)
            
            # Standardize features
            if len(feature_matrix) > 1:
                feature_matrix_scaled = self.scaler.fit_transform(feature_matrix)
            else:
                feature_matrix_scaled = feature_matrix
            
            # Anomaly detection
            anomaly_scores = self.isolation_forest.fit_predict(feature_matrix_scaled)
            anomaly_score = float(anomaly_scores[-1])  # -1 for anomaly, 1 for normal
            
            # Behavior clustering
            if len(feature_matrix) >= 4:
                clusters = self.kmeans_clusterer.fit_predict(feature_matrix_scaled)
                behavior_cluster = int(clusters[-1])
                
                # Map clusters to behavior types
                behavior_types = {
                    0: 'engaged',      # High engagement, consistent
                    1: 'declining',    # Decreasing engagement over time
                    2: 'consistent',   # Stable but moderate
                    3: 'erratic'       # Inconsistent patterns
                }
                behavior_type = behavior_types.get(behavior_cluster, 'unknown')
            else:
                behavior_type = 'unknown'
            
            # Calculate trends
            engagement_trend = self._calculate_trend(profile['engagement_scores'])
            consistency_score = self._calculate_consistency(profile['features'])
            
            # Calculate confidence based on data quality
            confidence = min(1.0, len(profile['features']) / 10.0)
            
            return {
                'behavior_type': behavior_type,
                'anomaly_score': anomaly_score,
                'engagement_trend': engagement_trend,
                'consistency_score': consistency_score,
                'confidence': confidence,
                'ml_predictions': {
                    'anomaly_detected': anomaly_score == -1,
                    'cluster_id': behavior_cluster if len(feature_matrix) >= 4 else None,
                    'feature_importance': self._get_feature_importance(feature_matrix_scaled)
                }
            }
            
        except Exception as e:
            log_warning(f"Error in ML behavioral analysis: {e}")
            return {}
    
    def _pattern_based_analysis(self, profile: Dict) -> Dict:
        """Pattern-based analysis as fallback and supplement"""
        flags = []
        behavior_type = 'unknown'
        
        # Check for declining engagement
        if len(profile['engagement_scores']) >= 3:
            recent_scores = list(profile['engagement_scores'])[-3:]
            if all(recent_scores[i] >= recent_scores[i+1] for i in range(len(recent_scores)-1)):
                flags.append('Declining engagement detected')
                behavior_type = 'declining'
        
        # Check for erratic behavior
        if len(profile['response_lengths']) >= 5:
            lengths = list(profile['response_lengths'])
            variance = np.var(lengths)
            if variance > np.mean(lengths) * 0.5:  # High variance
                flags.append('Erratic response patterns detected')
                if behavior_type == 'unknown':
                    behavior_type = 'erratic'
        
        # Check for consistency
        if len(profile['complexity_scores']) >= 3:
            complexity_variance = np.var(list(profile['complexity_scores']))
            if complexity_variance < 1.0:  # Low variance = consistent
                if behavior_type == 'unknown':
                    behavior_type = 'consistent'
        
        return {
            'flags': flags,
            'behavior_type': behavior_type
        }
    
    def _calculate_complexity_score(self, text: str) -> float:
        """Calculate text complexity score"""
        try:
            if not text:
                return 0.0
            
            words = text.split()
            if not words:
                return 0.0
            
            # Average word length
            avg_word_length = sum(len(word) for word in words) / len(words)
            
            # Sentence complexity
            sentences = [s.strip() for s in text.split('.') if s.strip()]
            avg_sentence_length = len(words) / max(1, len(sentences))
            
            # Vocabulary diversity
            unique_words = len({word.lower() for word in words})
            vocabulary_diversity = unique_words / len(words)
            
            # Combine metrics
            complexity = (
                avg_word_length * 0.3 +
                avg_sentence_length * 0.3 +
                vocabulary_diversity * 10 * 0.4
            )
            
            return min(10.0, complexity)
            
        except Exception as e:
            log_warning(f"Error calculating complexity score: {e}")
            return 5.0
    
    def _calculate_engagement_score(self, text: str) -> float:
        """Calculate engagement score"""
        try:
            if not text:
                return 0.0
            
            text_lower = text.lower()
            engagement_indicators = [
                'in my experience', 'for example', 'specifically',
                'when i', 'i have', 'i was', 'i did', 'i worked',
                'the project', 'the team', 'the company',
                'i learned', 'i developed', 'i implemented'
            ]
            
            engagement_count = sum(1 for indicator in engagement_indicators if indicator in text_lower)
            
            # Normalize to 0-10 scale
            score = min(10.0, engagement_count * 2.0)
            
            return score
            
        except Exception as e:
            log_warning(f"Error calculating engagement score: {e}")
            return 5.0
    
    def _calculate_trend(self, scores: deque) -> str:
        """Calculate trend direction"""
        try:
            if len(scores) < 3:
                return 'stable'
            
            scores_list = list(scores)
            
            # Simple linear trend
            if all(scores_list[i] >= scores_list[i+1] for i in range(len(scores_list)-1)):
                return 'declining'
            elif all(scores_list[i] <= scores_list[i+1] for i in range(len(scores_list)-1)):
                return 'improving'
            else:
                return 'stable'
                
        except Exception as e:
            log_warning(f"Error calculating trend: {e}")
            return 'stable'
    
    def _calculate_consistency(self, features: List[Dict]) -> float:
        """Calculate consistency score (0-1, higher = more consistent)"""
        try:
            if len(features) < 2:
                return 0.5
            
            # Calculate variance for key features
            key_features = ['response_length', 'complexity_score', 'engagement_score']
            
            variances = []
            for feature_name in key_features:
                values = [f.get(feature_name, 0.0) for f in features]
                if values:
                    variance = np.var(values)
                    mean_val = np.mean(values)
                    if mean_val > 0:
                        # Coefficient of variation
                        cv = variance / mean_val
                        variances.append(cv)
            
            if variances:
                avg_variance = np.mean(variances)
                # Lower variance = higher consistency
                consistency = max(0.0, min(1.0, 1.0 - avg_variance))
                return consistency
            
            return 0.5
            
        except Exception as e:
            log_warning(f"Error calculating consistency: {e}")
            return 0.5
    
    def _get_feature_importance(self, feature_matrix: np.ndarray) -> Dict[str, float]:
        """Get feature importance (simple variance-based)"""
        try:
            if feature_matrix.shape[0] < 2:
                return {}
            
            # Calculate variance for each feature
            variances = np.var(feature_matrix, axis=0)
            
            feature_names = [
                'response_length', 'complexity_score', 'engagement_score',
                'personal_pronoun_ratio', 'example_ratio', 'uncertainty_ratio',
                'confidence_ratio'
            ]
            
            importance = {}
            for i, name in enumerate(feature_names):
                if i < len(variances):
                    importance[name] = float(variances[i])
            
            # Normalize
            total = sum(importance.values())
            if total > 0:
                importance = {k: v/total for k, v in importance.items()}
            
            return importance
            
        except Exception as e:
            log_warning(f"Error getting feature importance: {e}")
            return {}
    
    def get_behavior_summary(self, interview_id: str) -> Dict:
        """Get behavioral summary for an interview"""
        try:
            if interview_id not in self.behavior_profiles:
                return {
                    'status': 'insufficient_data',
                    'message': 'Not enough responses for behavioral analysis'
                }
            
            profile = self.behavior_profiles[interview_id]
            
            if len(profile['features']) < 3:
                return {
                    'status': 'insufficient_data',
                    'message': 'Need at least 3 responses for analysis'
                }
            
            # Calculate summary statistics
            avg_length = np.mean(list(profile['response_lengths'])) if profile['response_lengths'] else 0
            avg_complexity = np.mean(list(profile['complexity_scores'])) if profile['complexity_scores'] else 0
            avg_engagement = np.mean(list(profile['engagement_scores'])) if profile['engagement_scores'] else 0
            
            return {
                'status': 'complete',
                'total_responses': len(profile['features']),
                'average_response_length': float(avg_length),
                'average_complexity': float(avg_complexity),
                'average_engagement': float(avg_engagement),
                'engagement_trend': self._calculate_trend(profile['engagement_scores']),
                'consistency_score': self._calculate_consistency(profile['features'])
            }
            
        except Exception as e:
            log_error(f"Error getting behavior summary: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def cleanup_old_profiles(self):
        """Clean up old behavior profiles"""
        try:
            # In production, this would check timestamps
            # For now, just limit the number of profiles
            if len(self.behavior_profiles) > 1000:
                # Keep only recent 500
                keys_to_remove = list(self.behavior_profiles.keys())[:-500]
                for key in keys_to_remove:
                    del self.behavior_profiles[key]
                log_info(f"Cleaned up {len(keys_to_remove)} old behavior profiles")
                
        except Exception as e:
            log_warning(f"Error cleaning up behavior profiles: {e}")

# Global instance
behavioral_analysis_service = BehavioralAnalysisService()

