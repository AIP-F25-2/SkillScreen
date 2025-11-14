"""
Model Performance Metrics Collection Module

Tracks and aggregates AI model performance metrics including:
- Transcription quality (Whisper)
- Diarization accuracy (pyannote)
- Scoring distributions (confidence, communication)
- Processing performance (time, success rate)
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, cast, Float, select, Table, MetaData
from datetime import datetime, timedelta, timezone as tz
from typing import Dict, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)

# Import table definitions from your repository
# These will be imported at module level
metadata = MetaData()


class MetricsCollector:
    """Collects and aggregates model performance metrics from database"""
    
    def __init__(self, db: Session):
        self.db = db
        # Import tables from repositories.audio_repository
        from repositories.audio_repository import (
            transcripts_table,
            ai_analysis_table,
            media_files_table,
            proctoring_events_table
        )
        self.transcripts_table = transcripts_table
        self.ai_analysis_table = ai_analysis_table
        self.media_files_table = media_files_table
        self.proctoring_events_table = proctoring_events_table
        
    def get_all_metrics(
        self, 
        days: int = 30,
        interview_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive model performance metrics
        
        Args:
            days: Number of days to look back (default: 30)
            interview_id: Optional filter by specific interview
            
        Returns:
            Dictionary containing all metrics
        """
        try:
            # Calculate date threshold - make it timezone-aware to match PostgreSQL
            from datetime import timezone as tz
            date_threshold = datetime.now(tz.utc) - timedelta(days=days)
            
            return {
                "metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "time_period_days": days,
                    "interview_id": interview_id
                },
                "transcription_metrics": self._get_transcription_metrics(date_threshold, interview_id),
                "diarization_metrics": self._get_diarization_metrics(date_threshold, interview_id),
                "scoring_metrics": self._get_scoring_metrics(date_threshold, interview_id),
                "performance_metrics": self._get_performance_metrics(date_threshold, interview_id),
                "error_metrics": self._get_error_metrics(date_threshold, interview_id)
            }
        except Exception as e:
            logger.error(f"Error collecting metrics: {str(e)}")
            raise
    
    def _get_transcription_metrics(
        self, 
        date_threshold: datetime,
        interview_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get Whisper transcription model metrics"""
        
        try:
            # Build base query using table
            query = select(self.transcripts_table).where(
                self.transcripts_table.c.created_at >= date_threshold
            )
            
            if interview_id:
                query = query.where(self.transcripts_table.c.interview_id == interview_id)
            
            # Execute query
            result = self.db.execute(query)
            transcripts = [dict(row._mapping) for row in result]
            
            if not transcripts:
                return self._empty_transcription_metrics()
            
            # Calculate metrics
            total_transcripts = len(transcripts)
            # Convert Decimal to float for calculations
            confidence_scores = [float(t['confidence_score']) for t in transcripts if t.get('confidence_score') is not None]
            word_counts = []
            language_distribution = {}
            
            # Aggregate word-level data
            for transcript in transcripts:
                # Count words
                if transcript.get('text'):
                    word_counts.append(len(transcript['text'].split()))
                
                # Parse word timestamps for detailed analysis
                if transcript.get('word_timestamps'):
                    try:
                        words = json.loads(transcript['word_timestamps']) if isinstance(transcript['word_timestamps'], str) else transcript['word_timestamps']
                        # Could add more word-level analysis here
                    except:
                        pass
            
            # Get language distribution from ai_analysis
            analysis_query = select(self.ai_analysis_table).where(
                and_(
                    self.ai_analysis_table.c.created_at >= date_threshold,
                    self.ai_analysis_table.c.service_name == 'audio-ai-service'
                )
            )
            
            if interview_id:
                analysis_query = analysis_query.where(self.ai_analysis_table.c.interview_id == interview_id)
            
            analysis_result = self.db.execute(analysis_query)
            
            for row in analysis_result:
                analysis = dict(row._mapping)
                if analysis.get('raw_results'):
                    try:
                        results = json.loads(analysis['raw_results']) if isinstance(analysis['raw_results'], str) else analysis['raw_results']
                        language = results.get('language', 'unknown')
                        language_distribution[language] = language_distribution.get(language, 0) + 1
                    except:
                        pass
            
            return {
                "total_interviews_processed": total_transcripts,
                "average_confidence_score": round(sum(confidence_scores) / len(confidence_scores), 3) if confidence_scores else None,
                "min_confidence_score": round(min(confidence_scores), 3) if confidence_scores else None,
                "max_confidence_score": round(max(confidence_scores), 3) if confidence_scores else None,
                "confidence_score_std_dev": round(self._calculate_std_dev(confidence_scores), 3) if len(confidence_scores) > 1 else None,
                "average_words_per_interview": round(sum(word_counts) / len(word_counts), 1) if word_counts else None,
                "total_words_transcribed": sum(word_counts) if word_counts else 0,
                "language_distribution": language_distribution,
                "low_confidence_count": len([c for c in confidence_scores if c < 0.7]) if confidence_scores else 0,
                "high_confidence_count": len([c for c in confidence_scores if c >= 0.9]) if confidence_scores else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting transcription metrics: {str(e)}")
            return self._empty_transcription_metrics()
    
    def _get_diarization_metrics(
        self,
        date_threshold: datetime,
        interview_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get pyannote diarization model metrics"""
        
        try:
            # Get speaker analysis from ai_analysis
            query = select(self.ai_analysis_table).where(
                and_(
                    self.ai_analysis_table.c.created_at >= date_threshold,
                    self.ai_analysis_table.c.service_name == 'audio-ai-service'
                )
            )
            
            if interview_id:
                query = query.where(self.ai_analysis_table.c.interview_id == interview_id)
            
            result = self.db.execute(query)
            analyses = [dict(row._mapping) for row in result]
            
            if not analyses:
                return self._empty_diarization_metrics()
            
            speaker_counts = []
            cheating_flags = []
            diarization_times = []
            
            for analysis in analyses:
                if analysis.get('raw_results'):
                    try:
                        results = json.loads(analysis['raw_results']) if isinstance(analysis['raw_results'], str) else analysis['raw_results']
                        
                        # Speaker analysis
                        if 'speaker_analysis' in results:
                            speaker_data = results['speaker_analysis']
                            speaker_counts.append(speaker_data.get('num_speakers', 1))
                            cheating_flags.append(speaker_data.get('cheating_flag', False))
                        
                        # Processing time breakdown (if available)
                        if 'processing_breakdown' in results:
                            breakdown = results['processing_breakdown']
                            if 'diarization_time' in breakdown:
                                diarization_times.append(breakdown['diarization_time'])
                        
                    except Exception as e:
                        logger.warning(f"Error parsing analysis results: {str(e)}")
            
            # Get proctoring events
            proctor_query = select(self.proctoring_events_table).where(
                self.proctoring_events_table.c.created_at >= date_threshold
            )
            
            if interview_id:
                proctor_query = proctor_query.where(self.proctoring_events_table.c.interview_id == interview_id)
            
            proctor_result = self.db.execute(proctor_query)
            proctor_events = [dict(row._mapping) for row in proctor_result]
            
            cheating_event_count = len([e for e in proctor_events if e.get('event_type') == 'multiple_speakers'])
            
            total_analyses = len(analyses)
            
            return {
                "total_diarizations": total_analyses,
                "single_speaker_rate": round(speaker_counts.count(1) / total_analyses, 3) if speaker_counts else None,
                "multi_speaker_rate": round(len([c for c in speaker_counts if c > 1]) / total_analyses, 3) if speaker_counts else None,
                "average_speakers_detected": round(sum(speaker_counts) / len(speaker_counts), 2) if speaker_counts else None,
                "cheating_detection_rate": round(sum(cheating_flags) / len(cheating_flags), 3) if cheating_flags else None,
                "cheating_flags_raised": sum(cheating_flags) if cheating_flags else 0,
                "proctoring_events_logged": len(proctor_events),
                "average_diarization_time_seconds": round(sum(diarization_times) / len(diarization_times), 2) if diarization_times else None,
                "speaker_distribution": {
                    "1_speaker": speaker_counts.count(1) if speaker_counts else 0,
                    "2_speakers": speaker_counts.count(2) if speaker_counts else 0,
                    "3+_speakers": len([c for c in speaker_counts if c >= 3]) if speaker_counts else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting diarization metrics: {str(e)}")
            return self._empty_diarization_metrics()
    
    def _get_scoring_metrics(
        self,
        date_threshold: datetime,
        interview_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get scoring model metrics (confidence, communication, filler)"""
        
        try:
            query = select(self.ai_analysis_table).where(
                and_(
                    self.ai_analysis_table.c.created_at >= date_threshold,
                    self.ai_analysis_table.c.service_name == 'audio-ai-service'
                )
            )
            
            if interview_id:
                query = query.where(self.ai_analysis_table.c.interview_id == interview_id)
            
            result = self.db.execute(query)
            analyses = [dict(row._mapping) for row in result]
            
            if not analyses:
                return self._empty_scoring_metrics()
            
            confidence_scores = []
            communication_scores = []
            filler_rates = []
            reading_detected = []
            
            # Distribution buckets
            confidence_distribution = {"0-3": 0, "4-6": 0, "7-10": 0}
            communication_distribution = {"0-3": 0, "4-6": 0, "7-10": 0}
            
            for analysis in analyses:
                if analysis.get('raw_results'):
                    try:
                        results = json.loads(analysis['raw_results']) if isinstance(analysis['raw_results'], str) else analysis['raw_results']
                        
                        # Confidence scores
                        if 'confidence_analysis' in results:
                            conf_score = results['confidence_analysis'].get('confidence_score')
                            if conf_score is not None:
                                confidence_scores.append(conf_score)
                                # Bucket
                                if conf_score <= 3:
                                    confidence_distribution["0-3"] += 1
                                elif conf_score <= 6:
                                    confidence_distribution["4-6"] += 1
                                else:
                                    confidence_distribution["7-10"] += 1
                        
                        # Communication scores
                        if 'communication_score' in results:
                            comm_score = results['communication_score'].get('communication_score')
                            if comm_score is not None:
                                communication_scores.append(comm_score)
                                # Bucket
                                if comm_score <= 3:
                                    communication_distribution["0-3"] += 1
                                elif comm_score <= 6:
                                    communication_distribution["4-6"] += 1
                                else:
                                    communication_distribution["7-10"] += 1
                        
                        # Filler analysis
                        if 'filler_analysis' in results:
                            filler_data = results['filler_analysis']
                            rate = filler_data.get('total_rate_per_minute', filler_data.get('filler_rate_per_minute'))
                            if rate is not None:
                                filler_rates.append(rate)
                        
                        # Reading detection
                        if 'reading_detection' in results:
                            reading_detected.append(results['reading_detection'].get('reading_detected', False))
                        
                    except Exception as e:
                        logger.warning(f"Error parsing scoring results: {str(e)}")
            
            return {
                "confidence_scoring": {
                    "average_score": round(sum(confidence_scores) / len(confidence_scores), 2) if confidence_scores else None,
                    "min_score": round(min(confidence_scores), 2) if confidence_scores else None,
                    "max_score": round(max(confidence_scores), 2) if confidence_scores else None,
                    "std_dev": round(self._calculate_std_dev(confidence_scores), 2) if len(confidence_scores) > 1 else None,
                    "distribution": confidence_distribution,
                    "total_scored": len(confidence_scores)
                },
                "communication_scoring": {
                    "average_score": round(sum(communication_scores) / len(communication_scores), 2) if communication_scores else None,
                    "min_score": round(min(communication_scores), 2) if communication_scores else None,
                    "max_score": round(max(communication_scores), 2) if communication_scores else None,
                    "std_dev": round(self._calculate_std_dev(communication_scores), 2) if len(communication_scores) > 1 else None,
                    "distribution": communication_distribution,
                    "total_scored": len(communication_scores)
                },
                "filler_detection": {
                    "average_filler_rate_per_minute": round(sum(filler_rates) / len(filler_rates), 2) if filler_rates else None,
                    "min_rate": round(min(filler_rates), 2) if filler_rates else None,
                    "max_rate": round(max(filler_rates), 2) if filler_rates else None,
                    "high_filler_count": len([r for r in filler_rates if r > 5]) if filler_rates else 0  # >5 fillers/min
                },
                "reading_detection": {
                    "reading_detected_count": sum(reading_detected) if reading_detected else 0,
                    "reading_detection_rate": round(sum(reading_detected) / len(reading_detected), 3) if reading_detected else None,
                    "total_analyzed": len(reading_detected)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting scoring metrics: {str(e)}")
            return self._empty_scoring_metrics()
    
    def _get_performance_metrics(
        self,
        date_threshold: datetime,
        interview_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get processing performance metrics"""
        
        try:
            # Get processing times from ai_analysis
            analysis_query = select(self.ai_analysis_table).where(
                and_(
                    self.ai_analysis_table.c.created_at >= date_threshold,
                    self.ai_analysis_table.c.service_name == 'audio-ai-service'
                )
            )
            
            if interview_id:
                analysis_query = analysis_query.where(self.ai_analysis_table.c.interview_id == interview_id)
            
            analysis_result = self.db.execute(analysis_query)
            analyses = [dict(row._mapping) for row in analysis_result]
            processing_times = [a['processing_time'] for a in analyses if a.get('processing_time')]
            
            # Get media file status
            media_query = select(self.media_files_table).where(
                self.media_files_table.c.created_at >= date_threshold
            )
            
            if interview_id:
                media_query = media_query.where(self.media_files_table.c.interview_id == interview_id)
            
            media_result = self.db.execute(media_query)
            media_files = [dict(row._mapping) for row in media_result]
            
            total_files = len(media_files)
            completed = len([f for f in media_files if f.get('status') == 'completed'])
            failed = len([f for f in media_files if f.get('status') == 'failed'])
            processing = len([f for f in media_files if f.get('status') == 'processing'])
            pending = len([f for f in media_files if f.get('status') == 'pending'])
            
            # Calculate retry statistics
            retry_counts = []
            for file in media_files:
                retry_count = 0
                if file.get('metadata'):
                    try:
                        metadata = json.loads(file['metadata']) if isinstance(file['metadata'], str) else file['metadata']
                        retry_count = metadata.get('retry_count', 0)
                    except:
                        retry_count = 0
                retry_counts.append(retry_count)
            
            # Categorize files by retry status and outcome
            succeeded_first_attempt = len([f for f in media_files if f.get('status') == 'completed' and (
                not f.get('metadata') or 
                (json.loads(f['metadata']) if isinstance(f.get('metadata'), str) else f.get('metadata', {})).get('retry_count', 0) == 0
            )])
            
            succeeded_after_retry = len([f for f in media_files if f.get('status') == 'completed' and (
                f.get('metadata') and 
                (json.loads(f['metadata']) if isinstance(f.get('metadata'), str) else f.get('metadata', {})).get('retry_count', 0) > 0
            )])
            
            still_failing = failed  # Already calculated above
            
            files_with_retries = [r for r in retry_counts if r > 0]
            retry_success_rate = None
            if len(files_with_retries) > 0:
                retry_success_rate = round(succeeded_after_retry / len(files_with_retries), 3)
            
            return {
                "total_processed": len(analyses),
                "processing_time": {
                    "average_seconds": round(sum(processing_times) / len(processing_times), 2) if processing_times else None,
                    "min_seconds": round(min(processing_times), 2) if processing_times else None,
                    "max_seconds": round(max(processing_times), 2) if processing_times else None,
                    "median_seconds": round(self._calculate_median(processing_times), 2) if processing_times else None,
                    "under_60s": len([t for t in processing_times if t < 60]) if processing_times else 0,
                    "60_to_120s": len([t for t in processing_times if 60 <= t < 120]) if processing_times else 0,
                    "over_120s": len([t for t in processing_times if t >= 120]) if processing_times else 0
                },
                "status_breakdown": {
                    "total": total_files,
                    "completed": completed,
                    "failed": failed,
                    "processing": processing,
                    "pending": pending,
                    "success_rate": round(completed / total_files, 3) if total_files > 0 else None,
                    "failure_rate": round(failed / total_files, 3) if total_files > 0 else None
                },
                "retry_statistics": {
                    "total_files": total_files,
                    "succeeded_first_attempt": succeeded_first_attempt,
                    "succeeded_after_retry": succeeded_after_retry,
                    "still_failing": still_failing,
                    "max_retries_needed": max(retry_counts) if retry_counts else 0,
                    "retry_success_rate": retry_success_rate
                },
                "throughput": {
                    "files_per_day": round(total_files / max(1, (datetime.now(tz.utc) - date_threshold).days), 2) if total_files > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return self._empty_performance_metrics()
    
    def _get_error_metrics(
        self,
        date_threshold: datetime,
        interview_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get error and failure metrics"""
        
        try:
            # Get failed media files
            media_query = select(self.media_files_table).where(
                and_(
                    self.media_files_table.c.created_at >= date_threshold,
                    self.media_files_table.c.status == 'failed'
                )
            )
            
            if interview_id:
                media_query = media_query.where(self.media_files_table.c.interview_id == interview_id)
            
            media_result = self.db.execute(media_query)
            failed_files = [dict(row._mapping) for row in media_result]
            
            # Parse error types from metadata
            error_types = {}
            for file in failed_files:
                if file.get('metadata'):
                    try:
                        metadata = json.loads(file['metadata']) if isinstance(file['metadata'], str) else file['metadata']
                        error_msg = metadata.get('error', 'Unknown error')
                        # Categorize errors
                        if 'timeout' in error_msg.lower():
                            error_types['timeout'] = error_types.get('timeout', 0) + 1
                        elif 'download' in error_msg.lower():
                            error_types['download_failed'] = error_types.get('download_failed', 0) + 1
                        elif 'transcription' in error_msg.lower():
                            error_types['transcription_failed'] = error_types.get('transcription_failed', 0) + 1
                        elif 'diarization' in error_msg.lower():
                            error_types['diarization_failed'] = error_types.get('diarization_failed', 0) + 1
                        else:
                            error_types['other'] = error_types.get('other', 0) + 1
                    except:
                        error_types['parse_error'] = error_types.get('parse_error', 0) + 1
            
            # Get total files for failure rate calculation
            total_query = select(func.count(self.media_files_table.c.id)).where(
                self.media_files_table.c.created_at >= date_threshold
            )
            total_count = self.db.execute(total_query).scalar() or 0
            
            return {
                "total_failures": len(failed_files),
                "error_type_breakdown": error_types,
                "failure_rate_percent": round(len(failed_files) / max(1, total_count) * 100, 2) if failed_files else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting error metrics: {str(e)}")
            return {"total_failures": 0, "error_type_breakdown": {}, "failure_rate_percent": 0}
    
    # Helper methods
    def _calculate_std_dev(self, values):
        """Calculate standard deviation"""
        if not values or len(values) < 2:
            return 0
        # Convert to float to handle Decimal types from PostgreSQL
        values = [float(v) if v is not None else 0 for v in values]
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def _calculate_median(self, values):
        """Calculate median"""
        if not values:
            return 0
        sorted_values = sorted(values)
        n = len(sorted_values)
        if n % 2 == 0:
            return (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
        else:
            return sorted_values[n//2]
    
    # Empty metric templates
    def _empty_transcription_metrics(self):
        return {
            "total_interviews_processed": 0,
            "average_confidence_score": None,
            "min_confidence_score": None,
            "max_confidence_score": None,
            "confidence_score_std_dev": None,
            "average_words_per_interview": None,
            "total_words_transcribed": 0,
            "language_distribution": {},
            "low_confidence_count": 0,
            "high_confidence_count": 0
        }
    
    def _empty_diarization_metrics(self):
        return {
            "total_diarizations": 0,
            "single_speaker_rate": None,
            "multi_speaker_rate": None,
            "average_speakers_detected": None,
            "cheating_detection_rate": None,
            "cheating_flags_raised": 0,
            "proctoring_events_logged": 0,
            "average_diarization_time_seconds": None,
            "speaker_distribution": {"1_speaker": 0, "2_speakers": 0, "3+_speakers": 0}
        }
    
    def _empty_scoring_metrics(self):
        return {
            "confidence_scoring": {
                "average_score": None,
                "min_score": None,
                "max_score": None,
                "std_dev": None,
                "distribution": {"0-3": 0, "4-6": 0, "7-10": 0},
                "total_scored": 0
            },
            "communication_scoring": {
                "average_score": None,
                "min_score": None,
                "max_score": None,
                "std_dev": None,
                "distribution": {"0-3": 0, "4-6": 0, "7-10": 0},
                "total_scored": 0
            },
            "filler_detection": {
                "average_filler_rate_per_minute": None,
                "min_rate": None,
                "max_rate": None,
                "high_filler_count": 0
            },
            "reading_detection": {
                "reading_detected_count": 0,
                "reading_detection_rate": None,
                "total_analyzed": 0
            }
        }
    
    def _empty_performance_metrics(self):
        return {
            "total_processed": 0,
            "processing_time": {
                "average_seconds": None,
                "min_seconds": None,
                "max_seconds": None,
                "median_seconds": None,
                "under_60s": 0,
                "60_to_120s": 0,
                "over_120s": 0
            },
            "status_breakdown": {
                "total": 0,
                "completed": 0,
                "failed": 0,
                "processing": 0,
                "pending": 0,
                "success_rate": None,
                "failure_rate": None
            },
            "retry_statistics": {
                "average_retries": 0,
                "max_retries": 0,
                "files_requiring_retry": 0
            },
            "throughput": {
                "files_per_day": 0
            }
        }