"""
Metrics API Controller

Exposes model performance metrics through REST API
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import logging

from db import UnitOfWork
from monitoring.metrics import MetricsCollector

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/audio/metrics")
async def get_metrics(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze (1-365)"),
    interview_id: Optional[str] = Query(default=None, description="Optional: Filter by specific interview ID")
):
    """
    Get comprehensive model performance metrics
    
    **Returns metrics for:**
    - Transcription quality (Whisper confidence scores)
    - Diarization accuracy (speaker detection, cheating rates)
    - Scoring distributions (confidence, communication, filler detection)
    - Processing performance (times, success rates, throughput)
    - Error analysis (failure types, retry statistics)
    
    **Parameters:**
    - days: Time period to analyze (default: 30 days)
    - interview_id: Optional filter by specific interview
    
    **Example response:**
    ```json
    {
      "metadata": {
        "generated_at": "2025-11-13T21:00:00",
        "time_period_days": 30
      },
      "transcription_metrics": {
        "total_interviews_processed": 156,
        "average_confidence_score": 0.887,
        "average_words_per_interview": 245
      },
      "diarization_metrics": {
        "cheating_detection_rate": 0.048,
        "single_speaker_rate": 0.952
      },
      "scoring_metrics": {
        "confidence_scoring": {
          "average_score": 6.8,
          "distribution": {"0-3": 5, "4-6": 45, "7-10": 106}
        }
      }
    }
    ```
    """
    try:
        logger.info(f"Fetching metrics for last {days} days" + (f" for interview {interview_id}" if interview_id else ""))
        
        # Use UnitOfWork pattern
        uow = UnitOfWork()
        collector = MetricsCollector(uow.session)
        metrics = collector.get_all_metrics(days=days, interview_id=interview_id)
        
        return {
            "status": "success",
            "data": metrics
        }
        
    except Exception as e:
        logger.error(f"Error fetching metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch metrics: {str(e)}"
        )


@router.get("/api/audio/metrics/summary")
async def get_metrics_summary(
    days: int = Query(default=7, ge=1, le=30, description="Number of days for quick summary (1-30)")
):
    """
    Get quick metrics summary (last 7 days by default)
    
    Provides a condensed view of key metrics for dashboards.
    Faster than full metrics endpoint.
    """
    try:
        uow = UnitOfWork()
        collector = MetricsCollector(uow.session)
        full_metrics = collector.get_all_metrics(days=days)
        
        # Extract key metrics only
        summary = {
            "time_period_days": days,
            "total_interviews": full_metrics["transcription_metrics"]["total_interviews_processed"],
            "avg_confidence_score": full_metrics["scoring_metrics"]["confidence_scoring"]["average_score"],
            "avg_communication_score": full_metrics["scoring_metrics"]["communication_scoring"]["average_score"],
            "success_rate": full_metrics["performance_metrics"]["status_breakdown"]["success_rate"],
            "avg_processing_time_seconds": full_metrics["performance_metrics"]["processing_time"]["average_seconds"],
            "cheating_detection_rate": full_metrics["diarization_metrics"]["cheating_detection_rate"],
            "total_failures": full_metrics["error_metrics"]["total_failures"]
        }
        
        return {
            "status": "success",
            "data": summary
        }
        
    except Exception as e:
        logger.error(f"Error fetching metrics summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch summary: {str(e)}"
        )


@router.get("/api/audio/metrics/health")
async def get_system_health():
    """
    Get real-time system health indicators
    
    Quick health check showing current system status
    """
    try:
        from repositories.audio_repository import media_files_table
        from sqlalchemy import select
        from datetime import datetime, timedelta, timezone as tz
        
        # Check last hour activity
        one_hour_ago = datetime.now(tz.utc) - timedelta(hours=1)
        
        uow = UnitOfWork()
        
        query = select(media_files_table).where(
            media_files_table.c.created_at >= one_hour_ago
        )
        
        result = uow.session.execute(query)
        recent_files = [dict(row._mapping) for row in result]
        
        processing = len([f for f in recent_files if f.get('status') == 'processing'])
        pending = len([f for f in recent_files if f.get('status') == 'pending'])
        completed = len([f for f in recent_files if f.get('status') == 'completed'])
        failed = len([f for f in recent_files if f.get('status') == 'failed'])
        
        # Calculate health score
        total = len(recent_files)
        health_score = "healthy"
        
        if total > 0:
            failure_rate = failed / total
            if failure_rate > 0.2:
                health_score = "unhealthy"
            elif failure_rate > 0.1:
                health_score = "degraded"
        
        return {
            "status": "success",
            "data": {
                "health_score": health_score,
                "last_hour_activity": {
                    "total": total,
                    "processing": processing,
                    "pending": pending,
                    "completed": completed,
                    "failed": failed
                },
                "timestamp": datetime.now(tz.utc).isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error checking system health: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )