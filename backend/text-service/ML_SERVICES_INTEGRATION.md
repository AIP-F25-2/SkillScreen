# ML Services Integration Guide

## Overview

Three new ML-based services have been added to enhance the text service:

1. **Behavioral Analysis Service** - ML-based behavioral pattern analysis
2. **Bias Detection Service** - Statistical bias detection
3. **Quality Prediction Service** - ML-based response quality prediction

---

## 1. Behavioral Analysis Service

### Purpose
Uses machine learning (Isolation Forest, K-Means clustering) to analyze candidate behavior patterns during interviews.

### Features
- **Anomaly Detection**: Identifies unusual response patterns
- **Behavior Clustering**: Classifies behavior types (engaged, declining, consistent, erratic)
- **Engagement Trend Analysis**: Tracks engagement over time
- **Consistency Scoring**: Measures response consistency

### Usage Example

```python
from services.behavioral_analysis_service import behavioral_analysis_service

# Analyze behavioral patterns
behavioral_result = await behavioral_analysis_service.analyze_behavioral_patterns(
    response_text="I have 5 years of experience...",
    interview_id="interview_123",
    previous_responses=previous_responses_list,
    response_time_seconds=45.2,
    question_number=3
)

# Result structure:
# {
#     'behavior_type': 'engaged' | 'declining' | 'consistent' | 'erratic',
#     'anomaly_score': -1.0 (anomaly) or 1.0 (normal),
#     'engagement_trend': 'improving' | 'declining' | 'stable',
#     'consistency_score': 0.0-1.0,
#     'behavioral_flags': ['flag1', 'flag2'],
#     'confidence': 0.0-1.0,
#     'ml_predictions': {...}
# }

# Get behavior summary
summary = behavioral_analysis_service.get_behavior_summary(interview_id)
```

### Integration Points
- Call in `submit_response()` endpoint after response submission
- Use results to flag suspicious behavior patterns
- Include in interview summary for recruiter review

---

## 2. Bias Detection Service

### Purpose
Uses statistical tests (t-tests, Mann-Whitney U, chi-square) to detect bias in scoring and question generation.

### Features
- **Statistical Tests**: T-tests, Mann-Whitney U tests for score differences
- **Demographic Parity**: Checks equal pass rates across groups
- **Equal Opportunity**: Checks equal true positive rates
- **Question Bias Detection**: Identifies biased language in questions

### Usage Example

```python
from services.bias_detection_service import bias_detection_service

# Detect bias in scoring
bias_result = await bias_detection_service.detect_bias_in_scoring(
    interview_id="interview_123",
    candidate_id="candidate_456",
    scores={
        'overall_score': 7.5,
        'technical_score': 8.0,
        'communication_score': 7.0
    },
    db=db_session
)

# Result structure:
# {
#     'bias_detected': True/False,
#     'bias_type': 'demographic_parity' | 'equal_opportunity' | 'systematic_under_scoring',
#     'statistical_tests': {
#         'group1_vs_group2': {
#             't_test': {'statistic': 2.5, 'p_value': 0.01, 'significant': True},
#             'effect_size': {'cohens_d': 0.6, 'category': 'medium'},
#             'mean_difference': 1.2
#         }
#     },
#     'demographic_parity': {
#         'group1': {'pass_rate': 0.8, ...},
#         '_summary': {'violation': True, 'difference': 0.15}
#     },
#     'recommendations': ['Review scoring criteria...']
# }

# Detect bias in questions
question_bias = await bias_detection_service.detect_bias_in_questions(
    question="How many years of experience do you have?",
    job_id="job_789",
    db=db_session
)

# Get bias summary
summary = bias_detection_service.get_bias_summary()
```

### Integration Points
- Call after scoring each response
- Check questions before sending to candidates
- Generate bias reports for compliance
- Include in audit logs

---

## 3. Quality Prediction Service

### Purpose
Uses ML models (XGBoost, LightGBM, Random Forest) to predict response quality scores.

### Features
- **Ensemble Prediction**: Combines multiple ML models
- **Feature Engineering**: Extracts 20+ features from responses
- **Confidence Scoring**: Provides prediction confidence
- **Model Training**: Can be trained on historical data

### Usage Example

```python
from services.quality_prediction_service import quality_prediction_service

# Predict quality score
prediction = await quality_prediction_service.predict_quality_score(
    question="Tell me about your experience with Python.",
    response="I have 5 years of experience working with Python...",
    candidate_context={
        'experience_years': 5,
        'skills': ['Python', 'FastAPI']
    },
    job_context={
        'title': 'Senior Software Engineer',
        'required_skills': ['Python', 'FastAPI'],
        'experience_level': 'senior'
    }
)

# Result structure:
# {
#     'predicted_score': 7.8,
#     'score_range': (0.0, 10.0),
#     'confidence': 0.85,
#     'model_predictions': {
#         'xgboost': 7.9,
#         'lightgbm': 7.7,
#         'primary': 7.8
#     },
#     'feature_importance': {
#         'response_length': 0.15,
#         'engagement_score': 0.20,
#         ...
#     },
#     'features_used': 20
# }

# Train model on historical data
training_result = await quality_prediction_service.train_model([
    {
        'question': '...',
        'response': '...',
        'actual_score': 8.5,
        'candidate_context': {...},
        'job_context': {...}
    },
    # ... more training samples
])
```

### Integration Points
- Use as alternative/additional scoring method
- Compare ML predictions with rule-based scores
- Train model periodically on new interview data
- Use feature importance for explainability

---

## Integration into fastapi_app.py

### Example Integration in `submit_response()`:

```python
@app.post("/interviews/{session_id}/respond")
async def submit_response(session_id: str, response: InterviewResponse):
    """Submit candidate response with ML-enhanced analysis"""
    
    # ... existing code ...
    
    # 1. ML-based Quality Prediction
    try:
        candidate = candidates_db.get(session["candidate_id"], {})
        job = jobs_db.get(session["job_id"], {})
        
        ml_prediction = await quality_prediction_service.predict_quality_score(
            question=session.get("current_question", ""),
            response=response.response_text,
            candidate_context={
                'experience_years': candidate.get('experience_years', 0),
                'skills': candidate.get('skills', [])
            },
            job_context={
                'title': job.get('title', ''),
                'required_skills': job.get('required_skills', []),
                'experience_level': job.get('experience_level', 'mid')
            }
        )
        
        # Use ML prediction to enhance base score
        ml_score = ml_prediction.get('predicted_score', base_score)
        enhanced_score = (base_score * 0.6 + ml_score * 0.4)  # Weighted combination
    except Exception as e:
        log_warning(f"ML quality prediction failed: {e}")
        enhanced_score = base_score
    
    # 2. Behavioral Analysis
    try:
        previous_responses = session.get("response_history", [])
        behavioral_result = await behavioral_analysis_service.analyze_behavioral_patterns(
            response_text=response.response_text,
            interview_id=session_id,
            previous_responses=previous_responses,
            response_time_seconds=None,  # Can track this if available
            question_number=session["responses_received"]
        )
        
        # Add behavioral flags to warnings
        if behavioral_result.get('behavioral_flags'):
            warnings.extend(behavioral_result['behavioral_flags'])
        
        # Store behavioral data
        session['behavioral_analysis'] = behavioral_result
    except Exception as e:
        log_warning(f"Behavioral analysis failed: {e}")
    
    # 3. Bias Detection
    try:
        bias_result = await bias_detection_service.detect_bias_in_scoring(
            interview_id=session_id,
            candidate_id=session["candidate_id"],
            scores={
                'overall_score': enhanced_score,
                'technical_score': enhanced_score,
                'communication_score': enhanced_score
            },
            db=None  # Would use actual db session in production
        )
        
        # Log bias detection results
        if bias_result.get('bias_detected'):
            log_warning(f"Bias detected in interview {session_id}: {bias_result.get('bias_type')}")
            session['bias_detection'] = bias_result
    except Exception as e:
        log_warning(f"Bias detection failed: {e}")
    
    # ... rest of existing code ...
```

---

## Integration into interview_service.py

### Example Integration in `generate_interview_summary()`:

```python
async def generate_interview_summary(self, interview_id: str, db) -> Dict:
    """Generate comprehensive interview summary with ML insights"""
    
    # ... existing code ...
    
    # Add behavioral analysis summary
    try:
        behavioral_summary = self.behavioral_analysis_service.get_behavior_summary(interview_id)
        summary_data['behavioral_analysis'] = behavioral_summary
    except Exception as e:
        log_warning(f"Behavioral analysis summary failed: {e}")
    
    # Add bias detection summary
    try:
        bias_summary = self.bias_detection_service.get_bias_summary()
        summary_data['bias_analysis'] = bias_summary
    except Exception as e:
        log_warning(f"Bias detection summary failed: {e}")
    
    # ... rest of existing code ...
```

---

## Model Training

### Training Quality Prediction Model

```python
# Collect training data from historical interviews
training_data = []

# Example: Collect from database
interviews = db.query(Interview).filter(Interview.status == 'completed').all()
for interview in interviews:
    responses = db.query(InterviewResponse).filter(
        InterviewResponse.interview_id == interview.id
    ).all()
    
    for response in responses:
        question = db.query(InterviewQuestion).filter(
            InterviewQuestion.id == response.question_id
        ).first()
        
        candidate = db.query(Candidate).filter(
            Candidate.id == interview.candidate_id
        ).first()
        
        job = db.query(Job).filter(Job.id == interview.job_id).first()
        
        training_data.append({
            'question': question.question_text if question else '',
            'response': response.response_text,
            'actual_score': response.overall_score,
            'candidate_context': {
                'experience_years': candidate.experience_years,
                'skills': candidate.skills
            },
            'job_context': {
                'title': job.title,
                'required_skills': job.skills_required,
                'experience_level': job.experience_level
            }
        })

# Train model
result = await quality_prediction_service.train_model(training_data)
print(f"Model trained: {result['success']}")
print(f"Best model: {result['best_model']}")
print(f"R² score: {result['performance']['r2']}")
```

---

## Configuration

### Model Parameters

All services use default parameters but can be customized:

**Behavioral Analysis:**
- `contamination=0.1` (10% expected anomalies)
- `n_clusters=4` (4 behavior types)

**Bias Detection:**
- `demographic_parity_threshold=0.1` (10% difference)
- `equal_opportunity_threshold=0.15` (15% difference)
- `p_value_significance=0.05` (5% significance level)

**Quality Prediction:**
- `n_estimators=100` (tree count)
- `max_depth=6` (tree depth)
- `learning_rate=0.1` (learning rate)

---

## Performance Considerations

1. **Caching**: Behavioral analysis profiles are cached per interview
2. **Async Operations**: All services use async/await for non-blocking operations
3. **Fallback Mechanisms**: Services gracefully degrade if ML models fail
4. **Model Loading**: Models are loaded lazily on first use

---

## Testing

### Unit Tests

```python
# Test behavioral analysis
def test_behavioral_analysis():
    result = await behavioral_analysis_service.analyze_behavioral_patterns(
        response_text="Test response",
        interview_id="test_123",
        previous_responses=[],
        question_number=1
    )
    assert 'behavior_type' in result
    assert result['confidence'] >= 0.0

# Test bias detection
def test_bias_detection():
    result = await bias_detection_service.detect_bias_in_questions(
        question="What is your experience?",
        job_id="test_job",
        db=test_db
    )
    assert 'is_biased' in result

# Test quality prediction
def test_quality_prediction():
    result = await quality_prediction_service.predict_quality_score(
        question="Test question",
        response="Test response"
    )
    assert 'predicted_score' in result
    assert 0.0 <= result['predicted_score'] <= 10.0
```

---

## Next Steps

1. **Integrate into fastapi_app.py**: Add service calls in `submit_response()`
2. **Add API endpoints**: Create endpoints for model training and bias reports
3. **Collect training data**: Start collecting labeled data for model training
4. **Monitor performance**: Track prediction accuracy and bias detection rates
5. **Fine-tune models**: Adjust parameters based on real-world performance

---

**Last Updated:** December 2024

