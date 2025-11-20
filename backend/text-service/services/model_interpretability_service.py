"""
Model Interpretability Service for SkillScreen
Provides SHAP and LIME explanations for ML model predictions
"""

import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from utils.logger import log_info, log_error, log_warning

# Optional imports for interpretability libraries
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    shap = None
    log_warning("SHAP not available, interpretability features will be limited")

try:
    from lime import lime_tabular
    from lime.lime_text import LimeTextExplainer
    LIME_AVAILABLE = True
except ImportError:
    LIME_AVAILABLE = False
    lime_tabular = None
    LimeTextExplainer = None
    log_warning("LIME not available, text explanations will be limited")

class ModelInterpretabilityService:
    """Service for providing model interpretability using SHAP and LIME"""
    
    def __init__(self):
        self.shap_explainers = {}
        self.lime_explainers = {}
        log_info("[OK] Model Interpretability Service initialized")
    
    async def explain_prediction_with_shap(
        self,
        model: Any,
        features: np.ndarray,
        feature_names: List[str],
        background_data: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """Generate SHAP explanation for a prediction"""
        try:
            if not SHAP_AVAILABLE:
                return {
                    'available': False,
                    'error': 'SHAP library not installed',
                    'fallback': self._fallback_explanation(features, feature_names)
                }
            
            # Create explainer if not exists
            explainer_key = id(model)
            if explainer_key not in self.shap_explainers:
                if background_data is not None:
                    self.shap_explainers[explainer_key] = shap.TreeExplainer(model, background_data)
                else:
                    self.shap_explainers[explainer_key] = shap.TreeExplainer(model)
            
            explainer = self.shap_explainers[explainer_key]
            
            # Calculate SHAP values
            shap_values = explainer.shap_values(features)
            
            # Get feature importance
            feature_importance = {}
            if isinstance(shap_values, list):
                shap_values = shap_values[0]  # For multi-output models
            
            if len(shap_values.shape) > 1:
                shap_values = shap_values[0]  # Get first sample
            
            for i, feature_name in enumerate(feature_names):
                if i < len(shap_values):
                    feature_importance[feature_name] = float(shap_values[i])
            
            # Calculate summary statistics
            mean_abs_shap = np.mean(np.abs(shap_values))
            max_contributor_idx = np.argmax(np.abs(shap_values))
            max_contributor = feature_names[max_contributor_idx] if max_contributor_idx < len(feature_names) else 'unknown'
            
            return {
                'available': True,
                'shap_values': shap_values.tolist() if isinstance(shap_values, np.ndarray) else shap_values,
                'feature_importance': feature_importance,
                'expected_value': float(explainer.expected_value) if hasattr(explainer, 'expected_value') else None,
                'mean_abs_shap': float(mean_abs_shap),
                'max_contributor': max_contributor,
                'explanation': self._generate_shap_explanation(feature_importance, max_contributor)
            }
            
        except Exception as e:
            log_error(f"Error generating SHAP explanation: {e}")
            return {
                'available': False,
                'error': str(e),
                'fallback': self._fallback_explanation(features, feature_names)
            }
    
    async def explain_text_with_lime(
        self,
        text: str,
        model_predict_fn: callable,
        num_features: int = 10
    ) -> Dict[str, Any]:
        """Generate LIME explanation for text prediction"""
        try:
            if not LIME_AVAILABLE:
                return {
                    'available': False,
                    'error': 'LIME library not installed'
                }
            
            # Create text explainer
            explainer = LimeTextExplainer(class_names=['Low', 'Medium', 'High'])
            
            # Generate explanation
            explanation = explainer.explain_instance(
                text,
                model_predict_fn,
                num_features=num_features
            )
            
            # Extract important features
            important_features = []
            for feature, weight in explanation.as_list():
                important_features.append({
                    'feature': feature,
                    'weight': float(weight),
                    'contribution': 'positive' if weight > 0 else 'negative'
                })
            
            return {
                'available': True,
                'important_features': important_features,
                'explanation_text': explanation.as_list(),
                'prediction': explanation.predict_proba.tolist() if hasattr(explanation, 'predict_proba') else None
            }
            
        except Exception as e:
            log_error(f"Error generating LIME explanation: {e}")
            return {
                'available': False,
                'error': str(e)
            }
    
    def _generate_shap_explanation(
        self,
        feature_importance: Dict[str, float],
        max_contributor: str
    ) -> str:
        """Generate human-readable explanation from SHAP values"""
        sorted_features = sorted(
            feature_importance.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        top_positive = [f for f, v in sorted_features[:3] if v > 0]
        top_negative = [f for f, v in sorted_features[:3] if v < 0]
        
        explanation_parts = []
        
        if top_positive:
            explanation_parts.append(
                f"The score is increased by: {', '.join(top_positive)}"
            )
        
        if top_negative:
            explanation_parts.append(
                f"The score is decreased by: {', '.join(top_negative)}"
            )
        
        if max_contributor:
            explanation_parts.append(
                f"The most important factor is: {max_contributor}"
            )
        
        return ". ".join(explanation_parts) if explanation_parts else "No significant factors identified."
    
    def _fallback_explanation(
        self,
        features: np.ndarray,
        feature_names: List[str]
    ) -> Dict[str, Any]:
        """Fallback explanation when SHAP is not available"""
        try:
            # Simple feature importance based on absolute values
            feature_importance = {}
            if len(features.shape) > 1:
                features = features[0]
            
            for i, feature_name in enumerate(feature_names):
                if i < len(features):
                    feature_importance[feature_name] = float(features[i])
            
            # Normalize
            max_val = max(abs(v) for v in feature_importance.values()) if feature_importance else 1
            if max_val > 0:
                feature_importance = {k: v/max_val for k, v in feature_importance.items()}
            
            sorted_features = sorted(
                feature_importance.items(),
                key=lambda x: abs(x[1]),
                reverse=True
            )
            
            return {
                'feature_importance': dict(sorted_features[:10]),  # Top 10
                'method': 'fallback',
                'note': 'SHAP not available, using simple feature analysis'
            }
            
        except Exception as e:
            log_error(f"Error in fallback explanation: {e}")
            return {'error': str(e)}

# Global instance
model_interpretability_service = ModelInterpretabilityService()

