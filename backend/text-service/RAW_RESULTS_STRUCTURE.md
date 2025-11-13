# Raw Results Structure in AI Analysis Table

## Overview
The `raw_results` column in the `ai_analysis` table stores JSON analysis data (NOT the actual response text). The structure varies based on the `analysis_type`.

## Analysis Types

### 1. `text_analysis` (Individual Response Analysis)
Stored for each response during the interview.

```json
{
  "response_analysis": {
    "behavioral_analysis": {
      "behavior_type": "engaged|consistent|declining|erratic",
      "anomaly_score": 0.0-1.0,
      "engagement_trend": "increasing|stable|decreasing",
      "consistency_score": 0.0-1.0,
      "behavioral_flags": [],
      "engagement_score": 0.0-1.0
    },
    "quality_prediction": {
      "predicted_score": 1.0-10.0,
      "confidence": 0.0-1.0,
      "feature_importance": {
        "response_length": 0.2,
        "vocabulary_diversity": 0.15,
        "technical_keywords": 0.25
      },
      "model_used": "ensemble"
    },
    "bias_detection": {
      // Bias detection results if applicable
      // null if not enough data
    }
  },
  "metadata": {
    "question_number": 1,
    "response_length": 150,
    "response_time_seconds": 45,
    "timestamp": "2025-11-13T18:00:00+00:00"
  }
}
```

### 2. `interview_summary` (Final Interview Summary)
Stored once when the interview is completed. Contains **all data returned by the API**.

```json
{
  "interview_summary": {
    "executive_summary": "Interview completed for John Doe...",
    "overall_score": 7.5,
    "recommendation": "Hire|Strong Consider|Consider|Weak Consider|Reject",
    "recommendation_reason": "Based on responses with consistent performance.",
    "technical_assessment": {
      "score": 7.0,
      "summary": "Demonstrated strong technical knowledge..."
    },
    "communication_assessment": {
      "score": 8.0,
      "summary": "Communication skills were excellent..."
    },
    "cultural_fit": {
      "score": 7.5,
      "summary": "Cultural alignment appears strong..."
    },
    "strengths": [
      "Strong experience with Python",
      "5 years of professional experience",
      "Clear communication style"
    ],
    "areas_for_improvement": [
      "Could provide more specific examples",
      "Consider elaborating on technical details"
    ],
    "key_highlights": [
      "Completed interview with 5 responses",
      "Demonstrated knowledge in Python, FastAPI"
    ],
    "red_flags": [],
    "improvement_tips": [
      "Continue building technical depth",
      "Practice articulating complex concepts"
    ],
    "next_steps": [
      "Schedule follow-up interview",
      "Check references"
    ],
    "interviewer_notes": "Overall impression: Positive. Candidate showed strong potential."
  },
  "summary_type": "final_assessment",
  "metadata": {
    "interview_id": "uuid",
    "timestamp": "2025-11-13T18:00:00+00:00",
    "analysis_version": "v1.0"
  }
}
```

## Confidence Score
- **Range**: 1.0 to 10.0
- **For `text_analysis`**: Weighted average of quality prediction, behavioral consistency, and engagement
- **For `interview_summary`**: Uses the `overall_score` from the summary

## When Data is Stored

1. **Response-level analysis**: Automatically stored when a response is submitted via `/api/interviews/{session_id}/respond`
2. **Summary-level analysis**: Automatically stored when interview completes via `generate_interview_summary()`

## Querying the Data

```sql
-- Get all response analyses for an interview
SELECT raw_results, confidence_score 
FROM ai_analysis 
WHERE interview_id = '...' AND analysis_type = 'text_analysis';

-- Get the final interview summary
SELECT raw_results, confidence_score 
FROM ai_analysis 
WHERE interview_id = '...' AND analysis_type = 'interview_summary';

-- Get all analyses for an interview
SELECT analysis_type, confidence_score, raw_results 
FROM ai_analysis 
WHERE interview_id = '...' 
ORDER BY created_at;
```

