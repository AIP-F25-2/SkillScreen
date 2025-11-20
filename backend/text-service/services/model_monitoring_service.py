"""
Model Monitoring Service for SkillScreen
Tracks model performance, detects drift, and manages model versions
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from collections import deque
import logging
from scipy import stats

from utils.logger import log_info, log_error, log_warning

class ModelMonitoringService:
    """Service for monitoring ML model performance and detecting drift"""
    
    def __init__(self):
        # Performance tracking
        self.prediction_history = {}  # {model_name: deque of predictions}
        self.actual_scores_history = {}  # {model_name: deque of actual scores}
        self.confidence_history = {}  # {model_name: deque of confidence scores}
        self.feature_distributions = {}  # Track feature distributions over time
        
        # Model versions
        self.model_versions = {}  # {model_name: [version_info]}
        self.current_versions = {}  # {model_name: current_version}
        
        # Drift detection
        self.reference_distributions = {}  # Baseline distributions for drift detection
        
        # Performance metrics
        self.performance_metrics = {}  # {model_name: {metric: value}}
        
        log_info("[OK] Model Monitoring Service initialized")
    
    def track_prediction(
        self,
        model_name: str,
        predicted_score: float,
        actual_score: Optional[float] = None,
        confidence: Optional[float] = None,
        features: Optional[Dict] = None
    ) -> None:
        """Track a model prediction"""
        try:
            # Initialize tracking if needed
            if model_name not in self.prediction_history:
                self.prediction_history[model_name] = deque(maxlen=1000)
                self.actual_scores_history[model_name] = deque(maxlen=1000)
                self.confidence_history[model_name] = deque(maxlen=1000)
            
            # Store prediction
            self.prediction_history[model_name].append(predicted_score)
            if actual_score is not None:
                self.actual_scores_history[model_name].append(actual_score)
            if confidence is not None:
                self.confidence_history[model_name].append(confidence)
            
            # Track feature distributions
            if features:
                self._update_feature_distributions(model_name, features)
            
            # Update performance metrics
            if actual_score is not None:
                self._update_performance_metrics(model_name, predicted_score, actual_score)
            
        except Exception as e:
            log_error(f"Error tracking prediction: {e}")
    
    def _update_performance_metrics(
        self,
        model_name: str,
        predicted: float,
        actual: float
    ) -> None:
        """Update performance metrics for a model"""
        try:
            if model_name not in self.performance_metrics:
                self.performance_metrics[model_name] = {
                    'predictions': [],
                    'actuals': [],
                    'errors': [],
                    'last_updated': datetime.now(timezone.utc)
                }
            
            metrics = self.performance_metrics[model_name]
            metrics['predictions'].append(predicted)
            metrics['actuals'].append(actual)
            metrics['errors'].append(abs(predicted - actual))
            
            # Keep only last 1000
            if len(metrics['predictions']) > 1000:
                metrics['predictions'] = metrics['predictions'][-1000:]
                metrics['actuals'] = metrics['actuals'][-1000:]
                metrics['errors'] = metrics['errors'][-1000:]
            
            metrics['last_updated'] = datetime.now(timezone.utc)
            
        except Exception as e:
            log_error(f"Error updating performance metrics: {e}")
    
    def _update_feature_distributions(
        self,
        model_name: str,
        features: Dict
    ) -> None:
        """Update feature distributions for drift detection"""
        try:
            if model_name not in self.feature_distributions:
                self.feature_distributions[model_name] = {}
            
            for feature_name, feature_value in features.items():
                if feature_name not in self.feature_distributions[model_name]:
                    self.feature_distributions[model_name][feature_name] = deque(maxlen=500)
                
                self.feature_distributions[model_name][feature_name].append(float(feature_value))
            
        except Exception as e:
            log_error(f"Error updating feature distributions: {e}")
    
    async def detect_drift(
        self,
        model_name: str,
        current_features: Dict
    ) -> Dict[str, Any]:
        """Detect if model input distribution has drifted"""
        try:
            drift_results = {
                'drift_detected': False,
                'drifted_features': [],
                'drift_scores': {},
                'confidence': 0.0
            }
            
            if model_name not in self.feature_distributions:
                return drift_results
            
            # Get reference distribution (first 100 samples or stored reference)
            if model_name not in self.reference_distributions:
                # Use first 100 samples as reference
                feature_dists = self.feature_distributions[model_name]
                self.reference_distributions[model_name] = {
                    name: list(dist)[:100] for name, dist in feature_dists.items()
                }
            
            reference = self.reference_distributions[model_name]
            current_dist = self.feature_distributions[model_name]
            
            # Compare distributions using Kolmogorov-Smirnov test
            for feature_name in current_features:
                if feature_name in reference and feature_name in current_dist:
                    ref_values = reference[feature_name]
                    curr_values = list(current_dist[feature_name])[-100:]  # Last 100 samples
                    
                    if len(ref_values) >= 10 and len(curr_values) >= 10:
                        # Perform KS test
                        statistic, p_value = stats.ks_2samp(ref_values, curr_values)
                        
                        # Drift detected if p-value < 0.05
                        if p_value < 0.05:
                            drift_results['drift_detected'] = True
                            drift_results['drifted_features'].append(feature_name)
                            drift_results['drift_scores'][feature_name] = {
                                'statistic': float(statistic),
                                'p_value': float(p_value),
                                'drift_magnitude': 'high' if statistic > 0.3 else 'medium' if statistic > 0.2 else 'low'
                            }
            
            # Calculate overall confidence
            if drift_results['drifted_features']:
                drift_results['confidence'] = min(1.0, len(drift_results['drifted_features']) / len(current_features))
            
            return drift_results
            
        except Exception as e:
            log_error(f"Error detecting drift: {e}")
            return {'drift_detected': False, 'error': str(e)}
    
    def get_performance_metrics(self, model_name: str) -> Dict[str, Any]:
        """Get performance metrics for a model"""
        try:
            if model_name not in self.performance_metrics:
                return {
                    'model_name': model_name,
                    'status': 'no_data',
                    'message': 'No performance data available'
                }
            
            metrics = self.performance_metrics[model_name]
            
            if not metrics['predictions']:
                return {
                    'model_name': model_name,
                    'status': 'no_data',
                    'message': 'No predictions tracked yet'
                }
            
            predictions = np.array(metrics['predictions'])
            actuals = np.array(metrics['actuals'])
            errors = np.array(metrics['errors'])
            
            # Calculate metrics
            mae = np.mean(errors)
            rmse = np.sqrt(np.mean(errors ** 2))
            mape = np.mean(np.abs(errors / (actuals + 1e-6))) * 100
            
            # R² score
            ss_res = np.sum((actuals - predictions) ** 2)
            ss_tot = np.sum((actuals - np.mean(actuals)) ** 2)
            r2 = 1 - (ss_res / (ss_tot + 1e-6))
            
            # Prediction distribution
            pred_mean = np.mean(predictions)
            pred_std = np.std(predictions)
            
            return {
                'model_name': model_name,
                'status': 'active',
                'total_predictions': len(predictions),
                'metrics': {
                    'mae': float(mae),
                    'rmse': float(rmse),
                    'mape': float(mape),
                    'r2_score': float(r2),
                    'mean_prediction': float(pred_mean),
                    'std_prediction': float(pred_std)
                },
                'last_updated': metrics['last_updated'].isoformat()
            }
            
        except Exception as e:
            log_error(f"Error getting performance metrics: {e}")
            return {'error': str(e)}
    
    def register_model_version(
        self,
        model_name: str,
        version: str,
        performance: Dict,
        metadata: Optional[Dict] = None
    ) -> None:
        """Register a new model version"""
        try:
            if model_name not in self.model_versions:
                self.model_versions[model_name] = []
            
            version_info = {
                'version': version,
                'performance': performance,
                'metadata': metadata or {},
                'registered_at': datetime.now(timezone.utc).isoformat()
            }
            
            self.model_versions[model_name].append(version_info)
            self.current_versions[model_name] = version
            
            log_info(f"Registered model version: {model_name} v{version}")
            
        except Exception as e:
            log_error(f"Error registering model version: {e}")
    
    def get_model_versions(self, model_name: str) -> List[Dict]:
        """Get all versions of a model"""
        return self.model_versions.get(model_name, [])
    
    def get_current_version(self, model_name: str) -> Optional[str]:
        """Get current version of a model"""
        return self.current_versions.get(model_name)

# Global instance
model_monitoring_service = ModelMonitoringService()

