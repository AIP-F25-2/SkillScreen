"""
Bias Detection Service for SkillScreen
Uses statistical tests to detect bias in interview scoring and question generation
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from collections import defaultdict
import logging
from scipy import stats
from scipy.stats import chi2_contingency, ttest_ind, mannwhitneyu
import math

from database.models import Interview, Response, Candidate, JobPosition
from utils.logger import log_info, log_error, log_warning

class BiasDetectionService:
    """Statistical bias detection service for interview fairness"""
    
    def __init__(self):
        self.demographic_data = {}  # Store demographic data for analysis
        self.score_distributions = defaultdict(list)  # Group scores by demographic
        self.question_analysis = {}  # Analyze questions for bias
        self._initialize_thresholds()
    
    def _initialize_thresholds(self):
        """Initialize bias detection thresholds"""
        self.THRESHOLDS = {
            'demographic_parity': 0.1,  # 10% difference threshold
            'equal_opportunity': 0.15,  # 15% difference threshold
            'p_value_significance': 0.05,  # Statistical significance level
            'effect_size_medium': 0.5,  # Cohen's d medium effect
            'effect_size_large': 0.8,  # Cohen's d large effect
        }
    
    async def detect_bias_in_scoring(
        self,
        interview_id: str,
        candidate_id: str,
        scores: Dict[str, float],
        db
    ) -> Dict:
        """Detect bias in interview scoring"""
        try:
            # Get candidate demographic data
            candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            if not candidate:
                return {'bias_detected': False, 'message': 'Candidate not found'}
            
            # Extract demographic information (if available)
            # Note: In production, this would come from user profile
            demographics = self._extract_demographics(candidate)
            
            # Store scores for demographic group
            demographic_key = self._get_demographic_key(demographics)
            if demographic_key:
                self.score_distributions[demographic_key].append(scores.get('overall_score', 0.0))
            
            # Perform statistical tests
            bias_results = {
                'bias_detected': False,
                'bias_type': None,
                'statistical_tests': {},
                'demographic_parity': {},
                'equal_opportunity': {},
                'recommendations': []
            }
            
            # Compare with other demographic groups if enough data
            if len(self.score_distributions) >= 2:
                statistical_results = await self._perform_statistical_tests()
                bias_results['statistical_tests'] = statistical_results
                
                # Check for demographic parity violations
                parity_results = await self._check_demographic_parity()
                bias_results['demographic_parity'] = parity_results
                
                # Check for equal opportunity violations
                opportunity_results = await self._check_equal_opportunity()
                bias_results['equal_opportunity'] = opportunity_results
                
                # Determine if bias is detected
                bias_results['bias_detected'] = self._determine_bias(
                    statistical_results, parity_results, opportunity_results
                )
                
                if bias_results['bias_detected']:
                    bias_results['bias_type'] = self._identify_bias_type(
                        statistical_results, parity_results, opportunity_results
                    )
                    bias_results['recommendations'] = self._generate_bias_recommendations(
                        bias_results['bias_type']
                    )
            
            return bias_results
            
        except Exception as e:
            log_error(f"Error in bias detection: {e}")
            return {
                'bias_detected': False,
                'error': str(e)
            }
    
    async def detect_bias_in_questions( # nosonar
        self,
        question: str,
        db
    ) -> Dict:
        """Detect bias in generated questions"""
        try:
            bias_indicators = {
                'demographic_references': [],
                'age_indicators': [],
                'gender_indicators': [],
                'cultural_biases': [],
                'bias_score': 0.0,
                'is_biased': False
            }
            
            question_lower = question.lower()
            
            # Check for demographic references
            demographic_keywords = [
                'age', 'old', 'young', 'years old',
                'male', 'female', 'man', 'woman', 'gender',
                'race', 'ethnicity', 'nationality',
                'religion', 'religious',
                'married', 'single', 'divorced',
                'pregnant', 'children', 'kids'
            ]
            
            for keyword in demographic_keywords:
                if keyword in question_lower:
                    bias_indicators['demographic_references'].append(keyword)
                    bias_indicators['bias_score'] += 0.2
            
            # Check for age-related bias
            age_patterns = [
                r'\b\d{2}\s*years?\s*old\b',
                r'\b(young|old|elderly|senior)\b',
                r'\b(fresh|recent)\s*graduate\b'
            ]
            
            import re
            for pattern in age_patterns:
                if re.search(pattern, question_lower):
                    bias_indicators['age_indicators'].append(pattern)
                    bias_indicators['bias_score'] += 0.15
            
            # Check for gender bias
            gender_patterns = [
                r'\b(he|she|his|her|him)\b',
                r'\b(gentleman|ladies|guys|gals)\b'
            ]
            
            for pattern in gender_patterns:
                if re.search(pattern, question_lower):
                    bias_indicators['gender_indicators'].append(pattern)
                    bias_indicators['bias_score'] += 0.15
            
            # Check for cultural bias
            cultural_patterns = [
                r'\b(american|western|eastern|asian|european)\b',
                r'\b(native|foreign|immigrant)\b'
            ]
            
            for pattern in cultural_patterns:
                if re.search(pattern, question_lower):
                    bias_indicators['cultural_biases'].append(pattern)
                    bias_indicators['bias_score'] += 0.2
            
            # Determine if question is biased
            bias_indicators['is_biased'] = bias_indicators['bias_score'] >= 0.3
            
            return bias_indicators
            
        except Exception as e:
            log_error(f"Error detecting bias in questions: {e}")
            return {
                'is_biased': False,
                'error': str(e)
            }
    
    async def _perform_statistical_tests(self) -> Dict: # nosonar
        """Perform statistical tests for bias detection"""
        try:
            if len(self.score_distributions) < 2:
                return {}
            
            results = {}
            
            # Get all demographic groups
            groups = list(self.score_distributions.keys())
            
            # Perform pairwise comparisons
            for i, group1 in enumerate(groups):
                for group2 in groups[i+1:]:
                    scores1 = self.score_distributions[group1]
                    scores2 = self.score_distributions[group2]
                    
                    if len(scores1) < 3 or len(scores2) < 3:
                        continue
                    
                    comparison_key = f"{group1}_vs_{group2}"
                    
                    # T-test for mean difference
                    t_stat, p_value = ttest_ind(scores1, scores2)
                    
                    # Mann-Whitney U test (non-parametric)
                    u_stat, u_p_value = mannwhitneyu(scores1, scores2, alternative='two-sided')
                    
                    # Calculate effect size (Cohen's d)
                    pooled_std = math.sqrt(
                        ((len(scores1) - 1) * np.var(scores1) + (len(scores2) - 1) * np.var(scores2)) /
                        (len(scores1) + len(scores2) - 2)
                    )
                    cohens_d = (np.mean(scores1) - np.mean(scores2)) / pooled_std if pooled_std > 0 else 0
                    
                    # Determine effect size category
                    if abs(cohens_d) < 0.2:
                        effect_size = 'negligible'
                    elif abs(cohens_d) < 0.5:
                        effect_size = 'small'
                    elif abs(cohens_d) < 0.8:
                        effect_size = 'medium'
                    else:
                        effect_size = 'large'
                    
                    results[comparison_key] = {
                        't_test': {
                            'statistic': float(t_stat),
                            'p_value': float(p_value),
                            'significant': p_value < self.THRESHOLDS['p_value_significance']
                        },
                        'mann_whitney': {
                            'statistic': float(u_stat),
                            'p_value': float(u_p_value),
                            'significant': u_p_value < self.THRESHOLDS['p_value_significance']
                        },
                        'effect_size': {
                            'cohens_d': float(cohens_d),
                            'category': effect_size
                        },
                        'mean_difference': float(np.mean(scores1) - np.mean(scores2)),
                        'group1_mean': float(np.mean(scores1)),
                        'group2_mean': float(np.mean(scores2)),
                        'group1_count': len(scores1),
                        'group2_count': len(scores2)
                    }
            
            return results
            
        except Exception as e:
            log_error(f"Error performing statistical tests: {e}")
            return {}
    
    async def _check_demographic_parity(self) -> Dict: # nosonar
        """Check demographic parity (equal pass rates)"""
        try:
            if len(self.score_distributions) < 2:
                return {}
            
            # Define pass threshold (e.g., score >= 7.0)
            pass_threshold = 7.0
            
            parity_results = {}
            
            for group, scores in self.score_distributions.items():
                if len(scores) < 3:
                    continue
                
                pass_rate = sum(1 for s in scores if s >= pass_threshold) / len(scores)
                parity_results[group] = {
                    'pass_rate': float(pass_rate),
                    'total_candidates': len(scores),
                    'passed': sum(1 for s in scores if s >= pass_threshold),
                    'average_score': float(np.mean(scores))
                }
            
            # Check for violations
            if len(parity_results) >= 2:
                pass_rates = [r['pass_rate'] for r in parity_results.values()]
                max_rate = max(pass_rates)
                min_rate = min(pass_rates)
                difference = max_rate - min_rate
                
                parity_results['_summary'] = {
                    'max_pass_rate': float(max_rate),
                    'min_pass_rate': float(min_rate),
                    'difference': float(difference),
                    'violation': difference > self.THRESHOLDS['demographic_parity'],
                    'threshold': self.THRESHOLDS['demographic_parity']
                }
            
            return parity_results
            
        except Exception as e:
            log_error(f"Error checking demographic parity: {e}")
            return {}
    
    async def _check_equal_opportunity(self) -> Dict: # nosonar
        """Check equal opportunity (equal true positive rates)"""
        try:
            if len(self.score_distributions) < 2:
                return {}
            
            # For equal opportunity, we need to compare pass rates
            # among qualified candidates (e.g., those with relevant experience)
            # This is a simplified version - in production, you'd have qualification data
            
            opportunity_results = {}
            
            # Use a lower threshold for "qualified" candidates
            qualified_threshold = 6.0
            pass_threshold = 7.0
            
            for group, scores in self.score_distributions.items():
                if len(scores) < 3:
                    continue
                
                qualified_scores = [s for s in scores if s >= qualified_threshold]
                if len(qualified_scores) == 0:
                    continue
                
                true_positive_rate = sum(1 for s in qualified_scores if s >= pass_threshold) / len(qualified_scores)
                
                opportunity_results[group] = {
                    'true_positive_rate': float(true_positive_rate),
                    'qualified_count': len(qualified_scores),
                    'passed_count': sum(1 for s in qualified_scores if s >= pass_threshold)
                }
            
            # Check for violations
            if len(opportunity_results) >= 2:
                tpr_rates = [r['true_positive_rate'] for r in opportunity_results.values()]
                max_tpr = max(tpr_rates)
                min_tpr = min(tpr_rates)
                difference = max_tpr - min_tpr
                
                opportunity_results['_summary'] = {
                    'max_tpr': float(max_tpr),
                    'min_tpr': float(min_tpr),
                    'difference': float(difference),
                    'violation': difference > self.THRESHOLDS['equal_opportunity'],
                    'threshold': self.THRESHOLDS['equal_opportunity']
                }
            
            return opportunity_results
            
        except Exception as e:
            log_error(f"Error checking equal opportunity: {e}")
            return {}
    
    def _extract_demographics(self, candidate: Candidate) -> Dict:
        """Extract demographic information from candidate (currently disabled)"""
        # Demographic data collection is disabled - return empty dict
        return {}
    
    def _get_demographic_key(self, demographics: Dict) -> Optional[str]:
        """Create a key for demographic grouping"""
        if not demographics:
            return None
        
        # Create key from available demographic data
        parts = []
        if demographics.get('gender'):
            parts.append(f"gender_{demographics['gender']}")
        if demographics.get('age_range'):
            parts.append(f"age_{demographics['age_range']}")
        if demographics.get('ethnicity'):
            parts.append(f"ethnicity_{demographics['ethnicity']}")
        
        return "_".join(parts) if parts else None
    
    def _determine_bias(
        self,
        statistical_tests: Dict,
        demographic_parity: Dict,
        equal_opportunity: Dict
    ) -> bool:
        """Determine if bias is detected based on all tests"""
        bias_detected = False
        
        # Check statistical significance
        for test_name, test_result in statistical_tests.items():
            if test_result.get('t_test', {}).get('significant', False):
                if test_result.get('effect_size', {}).get('category') in ['medium', 'large']:
                    bias_detected = True
                    break
        
        # Check demographic parity violation
        if demographic_parity.get('_summary', {}).get('violation', False):
            bias_detected = True
        
        # Check equal opportunity violation
        if equal_opportunity.get('_summary', {}).get('violation', False):
            bias_detected = True
        
        return bias_detected
    
    def _identify_bias_type(
        self,
        statistical_tests: Dict,
        demographic_parity: Dict,
        equal_opportunity: Dict
    ) -> str:
        """Identify the type of bias detected"""
        bias_types = []
        
        if demographic_parity.get('_summary', {}).get('violation', False):
            bias_types.append('demographic_parity')
        
        if equal_opportunity.get('_summary', {}).get('violation', False):
            bias_types.append('equal_opportunity')
        
        for test_name, test_result in statistical_tests.items():
            if test_result.get('t_test', {}).get('significant', False):
                if 'mean_difference' in test_result and test_result['mean_difference'] < 0:
                    bias_types.append('systematic_under_scoring')
                elif 'mean_difference' in test_result and test_result['mean_difference'] > 0:
                    bias_types.append('systematic_over_scoring')
        
        return ', '.join(bias_types) if bias_types else 'unknown'
    
    def _generate_bias_recommendations(self, bias_type: str) -> List[str]:
        """Generate recommendations based on bias type"""
        recommendations = []
        
        if 'demographic_parity' in bias_type:
            recommendations.append("Review scoring criteria for demographic parity violations")
            recommendations.append("Consider blind scoring or multiple evaluators")
        
        if 'equal_opportunity' in bias_type:
            recommendations.append("Ensure equal opportunity for qualified candidates across all groups")
            recommendations.append("Review qualification thresholds and pass criteria")
        
        if 'systematic_under_scoring' in bias_type:
            recommendations.append("Investigate potential systematic under-scoring of certain groups")
            recommendations.append("Review scoring rubrics for implicit bias")
        
        if 'systematic_over_scoring' in bias_type:
            recommendations.append("Investigate potential systematic over-scoring of certain groups")
            recommendations.append("Ensure consistent application of scoring criteria")
        
        if not recommendations:
            recommendations.append("Review interview process for potential bias")
            recommendations.append("Consider bias training for evaluators")
        
        return recommendations
    
    def get_bias_summary(self) -> Dict:
        """Get overall bias detection summary"""
        try:
            summary = {
                'total_groups': len(self.score_distributions),
                'total_candidates': sum(len(scores) for scores in self.score_distributions.values()),
                'groups': {}
            }
            
            for group, scores in self.score_distributions.items():
                summary['groups'][group] = {
                    'count': len(scores),
                    'mean_score': float(np.mean(scores)) if scores else 0.0,
                    'std_score': float(np.std(scores)) if len(scores) > 1 else 0.0,
                    'min_score': float(min(scores)) if scores else 0.0,
                    'max_score': float(max(scores)) if scores else 0.0
                }
            
            return summary
            
        except Exception as e:
            log_error(f"Error getting bias summary: {e}")
            return {
                'error': str(e)
            }
    
    def reset_statistics(self):
        """Reset bias detection statistics"""
        self.score_distributions.clear()
        self.demographic_data.clear()
        log_info("Bias detection statistics reset")

# Global instance
bias_detection_service = BiasDetectionService()

