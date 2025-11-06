"""
ML-Based Response Quality Prediction Service for SkillScreen
Uses machine learning models (XGBoost, LightGBM) to predict response quality scores
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone
import logging
import pickle
import os
from pathlib import Path
import aiofiles

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from database.models import Interview, InterviewResponse, Candidate, Job
from utils.logger import log_info, log_error, log_warning

# Try to import ML libraries (with fallback)
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    log_warning("XGBoost not available, using fallback models")

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    log_warning("LightGBM not available, using fallback models")

class QualityPredictionService:
    """ML-based service for predicting response quality scores"""
    
    def __init__(self):
        self.models = {}
        self.scaler = StandardScaler()
        self.feature_names = []
        self.model_trained = False
        self.model_path = Path(__file__).parent.parent / 'models' / 'quality_predictor.pkl'
        self._initialize_models()
        # Note: _load_or_train_model is async, call it separately if needed
    
    def _initialize_models(self):
        """Initialize ML models for quality prediction"""
        try:
            log_info("Initializing ML-based quality prediction models...")
            
            # Create models directory if it doesn't exist
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Initialize models
            if XGBOOST_AVAILABLE:
                self.models['xgboost'] = xgb.XGBRegressor(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=42,
                    objective='reg:squarederror'
                )
                log_info("✅ XGBoost model initialized")
            
            if LIGHTGBM_AVAILABLE:
                self.models['lightgbm'] = lgb.LGBMRegressor(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=42,
                    objective='regression'
                )
                log_info("✅ LightGBM model initialized")
            
            # Fallback models (always available)
            self.models['random_forest'] = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_leaf=1,
                max_features='sqrt',
                random_state=42
            )
            
            self.models['gradient_boosting'] = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
            
            log_info("✅ Quality prediction models initialized")
            
        except Exception as e:
            log_error(f"❌ Failed to initialize quality prediction models: {e}")
            self.models = {}
    
    async def _load_or_train_model(self):
        """Load trained model or train a new one"""
        try:
            if self.model_path.exists():
                async with aiofiles.open(self.model_path, 'rb') as f:
                    model_data = pickle.loads(await f.read())
                    self.models['primary'] = model_data['model']
                    self.scaler = model_data['scaler']
                    self.feature_names = model_data['feature_names']
                    self.model_trained = True
                    log_info("✅ Loaded pre-trained quality prediction model")
            else:
                log_info("No pre-trained model found, will train on first use")
                self.model_trained = False
                
        except Exception as e:
            log_warning(f"Could not load model: {e}, will train new model")
            self.model_trained = False
    
    async def predict_quality_score(
        self,
        question: str,
        response: str,
        candidate_context: Optional[Dict] = None,
        job_context: Optional[Dict] = None
    ) -> Dict:
        """Predict response quality score using ML models"""
        try:
            features = self._extract_features(question, response, candidate_context, job_context)
            feature_array_scaled = self._prepare_features_for_prediction(features)
            predictions, confidence_scores = self._get_model_predictions(feature_array_scaled)
            
            if predictions:
                return self._build_prediction_result(predictions, confidence_scores, features)
            else:
                return self._fallback_prediction(features)
                
        except Exception as e:
            log_error(f"Error predicting quality score: {e}")
            return self._fallback_prediction({})
    
    def _prepare_features_for_prediction(self, features: Dict) -> np.ndarray:
        """Prepare and scale features for prediction"""
        feature_array = np.array([list(features.values())])
        self.feature_names = list(features.keys())
        
        if self.model_trained and hasattr(self.scaler, 'mean_'):
            return self.scaler.transform(feature_array)
        else:
            return feature_array
    
    def _get_model_predictions(self, feature_array_scaled: np.ndarray) -> Tuple[Dict, Dict]:
        """Get predictions from all available models"""
        predictions = {}
        confidence_scores = {}
        
        # Try primary model first
        if self.model_trained and 'primary' in self.models:
            model = self.models['primary']
            prediction = model.predict(feature_array_scaled)[0]
            predictions['primary'] = float(prediction)
            confidence_scores['primary'] = self._calculate_confidence(feature_array_scaled)
        
        # Try other models for ensemble
        for model_name, model in self.models.items():
            if model_name == 'primary':
                continue
            try:
                if hasattr(model, 'predict'):
                    pred = model.predict(feature_array_scaled)[0]
                    predictions[model_name] = float(pred)
                    confidence_scores[model_name] = self._calculate_confidence(feature_array_scaled)
            except Exception as e:
                log_warning(f"Error predicting with {model_name}: {e}")
        
        return predictions, confidence_scores
    
    def _build_prediction_result(self, predictions: Dict, confidence_scores: Dict, features: Dict) -> Dict:
        """Build final prediction result from model predictions"""
        weights = {
            'primary': 0.4,
            'xgboost': 0.25,
            'lightgbm': 0.25,
            'gradient_boosting': 0.05,
            'random_forest': 0.05
        }
        
        ensemble_score = sum(
            predictions.get(name, 0) * weights.get(name, 0.1)
            for name in weights.keys()
            if name in predictions
        )
        
        total_weight = sum(weights.get(name, 0) for name in predictions.keys())
        if total_weight > 0:
            ensemble_score = ensemble_score / total_weight * sum(weights.values())
        
        avg_confidence = np.mean(list(confidence_scores.values())) if confidence_scores else 0.7
        feature_importance = self._get_feature_importance()
        
        return {
            'predicted_score': round(float(ensemble_score), 2),
            'score_range': (0.0, 10.0),
            'confidence': round(float(avg_confidence), 2),
            'model_predictions': predictions,
            'feature_importance': feature_importance,
            'features_used': len(self.feature_names),
            'prediction_timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def _extract_features(
        self,
        question: str,
        response: str,
        candidate_context: Optional[Dict],
        job_context: Optional[Dict]
    ) -> Dict[str, float]:
        """Extract features for ML models"""
        try:
            features = {}
            
            # Text-based features
            words = response.split()
            sentences = [s.strip() for s in response.split('.') if s.strip()]
            
            features['response_length'] = len(words)
            features['sentence_count'] = len(sentences)
            features['avg_sentence_length'] = len(words) / max(1, len(sentences))
            features['avg_word_length'] = sum(len(w) for w in words) / max(1, len(words))
            
            # Vocabulary features
            unique_words = len({word.lower() for word in words})
            features['vocabulary_diversity'] = unique_words / max(1, len(words))
            
            # Question-response alignment
            question_words = set(question.lower().split())
            response_words = set(response.lower().split())
            features['keyword_overlap'] = len(question_words.intersection(response_words)) / max(1, len(question_words))
            
            # Content quality indicators
            features['personal_pronouns'] = sum(1 for w in words if w.lower() in ['i', 'me', 'my', 'we', 'our'])
            features['specific_examples'] = sum(1 for w in words if w.lower() in ['example', 'specifically', 'instance', 'case'])
            features['quantifiers'] = sum(1 for w in words if w.isdigit() or any(char.isdigit() for char in w))
            features['technical_terms'] = sum(1 for w in words if len(w) > 8)  # Long words often technical
            
            # Engagement indicators
            engagement_words = ['experience', 'project', 'team', 'worked', 'developed', 'implemented']
            features['engagement_score'] = sum(1 for word in engagement_words if word in response.lower())
            
            # Structure indicators
            features['has_structure'] = 1.0 if any(marker in response.lower() for marker in ['first', 'second', 'then', 'finally', 'next']) else 0.0
            features['has_conclusion'] = 1.0 if any(marker in response.lower() for marker in ['conclusion', 'summary', 'in summary', 'to conclude']) else 0.0
            
            # Complexity features
            features['complexity_score'] = self._calculate_complexity(response)
            
            # Candidate context features (if available)
            if candidate_context:
                features['candidate_experience'] = candidate_context.get('experience_years', 0)
                features['candidate_skill_count'] = len(candidate_context.get('skills', []))
            else:
                features['candidate_experience'] = 0.0
                features['candidate_skill_count'] = 0.0
            
            # Job context features (if available)
            if job_context:
                features['job_skill_requirements'] = len(job_context.get('required_skills', []))
                job_level = job_context.get('experience_level', 'mid')
                level_mapping = {'entry': 1, 'junior': 2, 'mid': 3, 'senior': 4, 'lead': 5}
                features['job_level'] = level_mapping.get(job_level.lower(), 3)
            else:
                features['job_skill_requirements'] = 0.0
                features['job_level'] = 3.0
            
            # Normalize some features
            if features['response_length'] > 0:
                features['personal_pronoun_ratio'] = features['personal_pronouns'] / features['response_length']
                features['example_ratio'] = features['specific_examples'] / features['response_length']
            else:
                features['personal_pronoun_ratio'] = 0.0
                features['example_ratio'] = 0.0
            
            return features
            
        except Exception as e:
            log_error(f"Error extracting features: {e}")
            return {}
    
    def _calculate_complexity(self, text: str) -> float:
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
            
            # Combine
            complexity = (
                avg_word_length * 0.3 +
                avg_sentence_length * 0.3 +
                vocabulary_diversity * 10 * 0.4
            )
            
            return min(10.0, complexity)
            
        except Exception as e:
            log_warning(f"Error calculating complexity: {e}")
            return 5.0
    
    def _calculate_confidence(self, features: np.ndarray) -> float:
        """Calculate prediction confidence"""
        try:
            # For tree-based models, we can use prediction variance
            # For now, use a simple heuristic based on feature values
            
            # Check if features are in reasonable range
            feature_std = np.std(features)
            
            # Higher confidence if features are well-distributed
            if feature_std > 0:
                confidence = min(1.0, 0.5 + (1.0 / (1.0 + feature_std)))
            else:
                confidence = 0.7
            
            return confidence
            
        except Exception as e:
            log_warning(f"Error calculating confidence: {e}")
            return 0.7
    
    def _get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from models"""
        try:
            importance = self._extract_importance_from_primary_model()
            
            if not importance:
                importance = self._extract_importance_from_other_models()
            
            return self._normalize_importance(importance)
            
        except Exception as e:
            log_warning(f"Error getting feature importance: {e}")
            return {}
    
    def _extract_importance_from_primary_model(self) -> Dict[str, float]:
        """Extract feature importance from primary model"""
        if 'primary' in self.models:
            model = self.models['primary']
            return self._get_importance_from_model(model)
        return {}
    
    def _extract_importance_from_other_models(self) -> Dict[str, float]:
        """Extract feature importance from other models"""
        for model_name, model in self.models.items():
            importance = self._get_importance_from_model(model)
            if importance:
                return importance
        return {}
    
    def _get_importance_from_model(self, model: Any) -> Dict[str, float]:
        """Get importance from a single model"""
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            if len(importances) == len(self.feature_names):
                return dict(zip(self.feature_names, importances.tolist()))
        return {}
    
    def _normalize_importance(self, importance: Dict[str, float]) -> Dict[str, float]:
        """Normalize importance values"""
        if importance:
            total = sum(importance.values())
            if total > 0:
                return {k: v/total for k, v in importance.items()}
        return importance
    
    def _fallback_prediction(self, features: Dict) -> Dict:
        """Fallback rule-based prediction"""
        try:
            # Simple rule-based scoring
            score = 5.0  # Base score
            
            if features:
                # Length-based
                if features.get('response_length', 0) > 50:
                    score += 1.0
                elif features.get('response_length', 0) < 10:
                    score -= 2.0
                
                # Engagement
                if features.get('engagement_score', 0) > 2:
                    score += 1.0
                
                # Examples
                if features.get('specific_examples', 0) > 0:
                    score += 0.5
                
                # Structure
                if features.get('has_structure', 0) > 0:
                    score += 0.5
            
            return {
                'predicted_score': round(max(0.0, min(10.0, score)), 2),
                'score_range': (0.0, 10.0),
                'confidence': 0.6,
                'model_predictions': {'fallback': score},
                'feature_importance': {},
                'features_used': len(features),
                'prediction_timestamp': datetime.now(timezone.utc).isoformat(),
                'note': 'Using fallback rule-based prediction'
            }
            
        except Exception as e:
            log_error(f"Error in fallback prediction: {e}")
            return {
                'predicted_score': 5.0,
                'score_range': (0.0, 10.0),
                'confidence': 0.5,
                'error': str(e)
            }
    
    async def train_model(self, training_data: List[Dict]) -> Dict:
        """Train the quality prediction model on historical data"""
        try:
            if len(training_data) < 10:
                return {
                    'success': False,
                    'message': 'Insufficient training data (need at least 10 samples)'
                }
            
            log_info(f"Training quality prediction model on {len(training_data)} samples...")
            
            X, y = self._prepare_training_data(training_data)
            if len(X) < 10:
                return {
                    'success': False,
                    'message': 'Insufficient valid training samples'
                }
            
            X_train, X_test, y_train, y_test, x_train_scaled, x_test_scaled = self._split_and_scale_data(X, y)
            results = self._train_all_models(x_train_scaled, y_train, x_test_scaled, y_test)
            return await self._select_and_save_best_model(results, X_train, X_test)
                
        except Exception as e:
            log_error(f"Error training model: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _prepare_training_data(self, training_data: List[Dict]) -> Tuple[List, List]:
        """Prepare features and labels from training data"""
        X = []
        y = []
        
        for sample in training_data:
            features = self._extract_features(
                sample.get('question', ''),
                sample.get('response', ''),
                sample.get('candidate_context'),
                sample.get('job_context')
            )
            
            if features:
                X.append(list(features.values()))
                y.append(sample.get('actual_score', 5.0))
                self.feature_names = list(features.keys())
        
        return X, y
    
    def _split_and_scale_data(self, X: List, y: List) -> Tuple:
        """Split and scale training data"""
        X_array = np.array(X)
        y_array = np.array(y)
        
        X_train, X_test, y_train, y_test = train_test_split(
            X_array, y_array, test_size=0.2, random_state=42
        )
        
        x_train_scaled = self.scaler.fit_transform(X_train)
        x_test_scaled = self.scaler.transform(X_test)
        
        return X_train, X_test, y_train, y_test, x_train_scaled, x_test_scaled
    
    def _train_all_models(self, x_train_scaled: np.ndarray, y_train: np.ndarray,
                         x_test_scaled: np.ndarray, y_test: np.ndarray) -> Dict:
        """Train all models and return results"""
        results = {}
        
        for model_name, model in self.models.items():
            if model_name == 'primary':
                continue
            
            try:
                model.fit(x_train_scaled, y_train)
                y_pred = model.predict(x_test_scaled)
                
                results[model_name] = {
                    'mse': float(mean_squared_error(y_test, y_pred)),
                    'mae': float(mean_absolute_error(y_test, y_pred)),
                    'r2': float(r2_score(y_test, y_pred)),
                    'trained': True
                }
                
                log_info(f"✅ {model_name} trained - MSE: {results[model_name]['mse']:.3f}, "
                        f"MAE: {results[model_name]['mae']:.3f}, R²: {results[model_name]['r2']:.3f}")
                
            except Exception as e:
                log_warning(f"Error training {model_name}: {e}")
                results[model_name] = {'trained': False, 'error': str(e)}
        
        return results
    
    async def _select_and_save_best_model(self, results: Dict, X_train: np.ndarray, X_test: np.ndarray) -> Dict:
        """Select best model and save it"""
        best_model_name = None
        best_r2 = -float('inf')
        
        for model_name, result in results.items():
            if result.get('trained', False) and result.get('r2', -1) > best_r2:
                best_r2 = result['r2']
                best_model_name = model_name
        
        if not best_model_name:
            return {
                'success': False,
                'message': 'No models could be trained successfully'
            }
        
        self.models['primary'] = self.models[best_model_name]
        self.model_trained = True
        
        model_data = {
            'model': self.models['primary'],
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'training_date': datetime.now(timezone.utc).isoformat(),
            'performance': results[best_model_name]
        }
        
        async with aiofiles.open(self.model_path, 'wb') as f:
            await f.write(pickle.dumps(model_data))
        
        log_info(f"✅ Model trained and saved. Best model: {best_model_name} (R²: {best_r2:.3f})")
        
        return {
            'success': True,
            'best_model': best_model_name,
            'performance': results[best_model_name],
            'all_results': results,
            'training_samples': len(X_train),
            'test_samples': len(X_test)
        }

# Global instance
quality_prediction_service = QualityPredictionService()

