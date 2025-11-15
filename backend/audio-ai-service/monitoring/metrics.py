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
            date_threshold = self._get_date_threshold(days)
            return self._build_metrics_response(date_threshold, days, interview_id)
        except Exception as e:
            logger.error(f"Error collecting metrics: {str(e)}")
            raise

    def _get_date_threshold(self, days: int) -> datetime:
        """Calculate date threshold for metrics queries"""
        return datetime.now(tz.utc) - timedelta(days=days)

    def _build_metrics_response(self, date_threshold: datetime, days: int, interview_id: Optional[str]) -> Dict[str, Any]:
        """Build the complete metrics response dictionary"""
        return {
            "metadata": {
                "generated_at": datetime.now(tz.utc).isoformat(),
                "time_period_days": days,
                "interview_id": interview_id
            },
            "transcription_metrics": self._get_transcription_metrics(date_threshold, interview_id),
            "diarization_metrics": self._get_diarization_metrics(date_threshold, interview_id),
            "scoring_metrics": self._get_scoring_metrics(date_threshold, interview_id),
            "performance_metrics": self._get_performance_metrics(date_threshold, interview_id),
            "error_metrics": self._get_error_metrics(date_threshold, interview_id)
        }
    
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
            confidence_scores = self._extract_confidence_scores(transcripts)
            word_counts = self._aggregate_word_data(transcripts)
            language_distribution = self._get_language_distribution(date_threshold, interview_id)

            return self._build_transcription_response(
                total_transcripts, confidence_scores, word_counts, language_distribution
            )

        except Exception as e:
            logger.error(f"Error getting transcription metrics: {str(e)}")
            return self._empty_transcription_metrics()

    def _extract_confidence_scores(self, transcripts: list) -> list:
        """Extract and convert confidence scores from transcripts"""
        return [float(t['confidence_score']) for t in transcripts if t.get('confidence_score') is not None]

    def _aggregate_word_data(self, transcripts: list) -> list:
        """Aggregate word count data from transcripts"""
        word_counts = []
        for transcript in transcripts:
            if transcript.get('text'):
                word_counts.append(len(transcript['text'].split()))
        return word_counts

    def _get_language_distribution(self, date_threshold: datetime, interview_id: Optional[str]) -> dict:
        """Get language distribution from ai_analysis"""
        language_distribution = {}
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
                except json.JSONDecodeError:
                    pass
        return language_distribution

    def _build_transcription_response(self, total_transcripts: int, confidence_scores: list, word_counts: list, language_distribution: dict) -> dict:
        """Build the transcription metrics response"""
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

            speaker_counts, cheating_flags, diarization_times = self._parse_diarization_results(analyses)
            proctor_events = self._get_proctoring_events(date_threshold, interview_id)
            total_analyses = len(analyses)

            return self._build_diarization_response(
                total_analyses, speaker_counts, cheating_flags, diarization_times, proctor_events
            )

        except Exception as e:
            logger.error(f"Error getting diarization metrics: {str(e)}")
            return self._empty_diarization_metrics()

    def _parse_diarization_results(self, analyses: list) -> tuple:
        """Parse speaker analysis and diarization times from raw results"""
        speaker_counts = []
        cheating_flags = []
        diarization_times = []

        for analysis in analyses:
            if analysis.get('raw_results'):
                try:
                    results = json.loads(analysis['raw_results']) if isinstance(analysis['raw_results'], str) else analysis['raw_results']
                    self._extract_speaker_analysis(results, speaker_counts, cheating_flags)
                    self._extract_diarization_time(results, diarization_times)
                except Exception as e:
                    logger.warning(f"Error parsing analysis results: {str(e)}")

        return speaker_counts, cheating_flags, diarization_times

    def _extract_speaker_analysis(self, results: dict, speaker_counts: list, cheating_flags: list) -> None:
        """Extract speaker analysis data from results"""
        if 'speaker_analysis' in results:
            speaker_data = results['speaker_analysis']
            speaker_counts.append(speaker_data.get('num_speakers', 1))
            cheating_flags.append(speaker_data.get('cheating_flag', False))

    def _extract_diarization_time(self, results: dict, diarization_times: list) -> None:
        """Extract diarization processing time from results"""
        if 'processing_breakdown' in results:
            breakdown = results['processing_breakdown']
            if 'diarization_time' in breakdown:
                diarization_times.append(breakdown['diarization_time'])

    def _get_proctoring_events(self, date_threshold: datetime, interview_id: Optional[str]) -> list:
        """Retrieve proctoring events from database"""
        proctor_query = select(self.proctoring_events_table).where(
            self.proctoring_events_table.c.created_at >= date_threshold
        )

        if interview_id:
            proctor_query = proctor_query.where(self.proctoring_events_table.c.interview_id == interview_id)

        proctor_result = self.db.execute(proctor_query)
        return [dict(row._mapping) for row in proctor_result]

    def _build_diarization_response(self, total_analyses: int, speaker_counts: list, cheating_flags: list, diarization_times: list, proctor_events: list) -> dict:
        """Build the diarization metrics response"""
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

            confidence_scores, confidence_distribution, communication_scores, communication_distribution, filler_rates, reading_detected = self._parse_scoring_results(analyses)

            return self._build_scoring_response(
                confidence_scores, confidence_distribution,
                communication_scores, communication_distribution,
                filler_rates, reading_detected
            )

        except Exception as e:
            logger.error(f"Error getting scoring metrics: {str(e)}")
            return self._empty_scoring_metrics()

    def _parse_scoring_results(self, analyses: list) -> tuple:
        """Parse all scoring results from analyses"""
        confidence_scores = []
        communication_scores = []
        filler_rates = []
        reading_detected = []
        confidence_distribution = {"0-3": 0, "4-6": 0, "7-10": 0}
        communication_distribution = {"0-3": 0, "4-6": 0, "7-10": 0}

        for analysis in analyses:
            if analysis.get('raw_results'):
                try:
                    results = json.loads(analysis['raw_results']) if isinstance(analysis['raw_results'], str) else analysis['raw_results']
                    self._extract_confidence_score(results, confidence_scores, confidence_distribution)
                    self._extract_communication_score(results, communication_scores, communication_distribution)
                    self._extract_filler_analysis(results, filler_rates)
                    self._extract_reading_detection(results, reading_detected)
                except Exception as e:
                    logger.warning(f"Error parsing scoring results: {str(e)}")

        return confidence_scores, confidence_distribution, communication_scores, communication_distribution, filler_rates, reading_detected

    def _extract_confidence_score(self, results: dict, confidence_scores: list, confidence_distribution: dict) -> None:
        """Extract confidence score and update distribution"""
        if 'confidence_analysis' in results:
            conf_score = results['confidence_analysis'].get('confidence_score')
            if conf_score is not None:
                confidence_scores.append(conf_score)
                self._bucket_score(conf_score, confidence_distribution)

    def _extract_communication_score(self, results: dict, communication_scores: list, communication_distribution: dict) -> None:
        """Extract communication score and update distribution"""
        if 'communication_score' in results:
            comm_score = results['communication_score'].get('communication_score')
            if comm_score is not None:
                communication_scores.append(comm_score)
                self._bucket_score(comm_score, communication_distribution)

    def _bucket_score(self, score: float, distribution: dict) -> None:
        """Bucket a score into distribution ranges"""
        if score <= 3:
            distribution["0-3"] += 1
        elif score <= 6:
            distribution["4-6"] += 1
        else:
            distribution["7-10"] += 1

    def _extract_filler_analysis(self, results: dict, filler_rates: list) -> None:
        """Extract filler analysis data"""
        if 'filler_analysis' in results:
            filler_data = results['filler_analysis']
            rate = filler_data.get('total_rate_per_minute', filler_data.get('filler_rate_per_minute'))
            if rate is not None:
                filler_rates.append(rate)

    def _extract_reading_detection(self, results: dict, reading_detected: list) -> None:
        """Extract reading detection data"""
        if 'reading_detection' in results:
            reading_detected.append(results['reading_detection'].get('reading_detected', False))

    def _build_scoring_response(self, confidence_scores: list, confidence_distribution: dict, communication_scores: list, communication_distribution: dict, filler_rates: list, reading_detected: list) -> dict:
        """Build the scoring metrics response"""
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
                "high_filler_count": len([r for r in filler_rates if r > 5]) if filler_rates else 0
            },
            "reading_detection": {
                "reading_detected_count": sum(reading_detected) if reading_detected else 0,
                "reading_detection_rate": round(sum(reading_detected) / len(reading_detected), 3) if reading_detected else None,
                "total_analyzed": len(reading_detected)
            }
        }
    
    def _get_performance_metrics(
        self,
        date_threshold: datetime,
        interview_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get processing performance metrics"""

        try:
            analyses = self._get_analyses(date_threshold, interview_id)
            processing_times = [a['processing_time'] for a in analyses if a.get('processing_time')]

            media_files = self._get_media_files(date_threshold, interview_id)
            total_files = len(media_files)
            status_counts = self._count_files_by_status(media_files)
            retry_counts = self._extract_retry_counts(media_files)
            succeeded_first_attempt, succeeded_after_retry = self._calculate_retry_categories(media_files)

            files_with_retries = [r for r in retry_counts if r > 0]
            retry_success_rate = None
            if len(files_with_retries) > 0:
                retry_success_rate = round(succeeded_after_retry / len(files_with_retries), 3)

            return self._build_performance_response(
                analyses, processing_times, total_files, status_counts,
                succeeded_first_attempt, succeeded_after_retry, status_counts.get('failed', 0),
                retry_counts, retry_success_rate, date_threshold
            )

        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return self._empty_performance_metrics()

    def _get_analyses(self, date_threshold: datetime, interview_id: Optional[str]) -> list:
        """Get analyses from ai_analysis table"""
        analysis_query = select(self.ai_analysis_table).where(
            and_(
                self.ai_analysis_table.c.created_at >= date_threshold,
                self.ai_analysis_table.c.service_name == 'audio-ai-service'
            )
        )

        if interview_id:
            analysis_query = analysis_query.where(self.ai_analysis_table.c.interview_id == interview_id)

        analysis_result = self.db.execute(analysis_query)
        return [dict(row._mapping) for row in analysis_result]

    def _get_media_files(self, date_threshold: datetime, interview_id: Optional[str]) -> list:
        """Get media files from media_files table"""
        media_query = select(self.media_files_table).where(
            self.media_files_table.c.created_at >= date_threshold
        )

        if interview_id:
            media_query = media_query.where(self.media_files_table.c.interview_id == interview_id)

        media_result = self.db.execute(media_query)
        return [dict(row._mapping) for row in media_result]

    def _count_files_by_status(self, media_files: list) -> dict:
        """Count files grouped by status"""
        return {
            'completed': len([f for f in media_files if f.get('status') == 'completed']),
            'failed': len([f for f in media_files if f.get('status') == 'failed']),
            'processing': len([f for f in media_files if f.get('status') == 'processing']),
            'pending': len([f for f in media_files if f.get('status') == 'pending'])
        }

    def _extract_retry_counts(self, media_files: list) -> list:
        """Extract retry counts from file metadata"""
        retry_counts = []
        for file in media_files:
            retry_count = self._extract_retry_count_from_file(file)
            retry_counts.append(retry_count)
        return retry_counts

    def _extract_retry_count_from_file(self, file: dict) -> int:
        """Extract single retry count from file metadata"""
        if file.get('metadata'):
            try:
                metadata = json.loads(file['metadata']) if isinstance(file['metadata'], str) else file['metadata']
                return metadata.get('retry_count', 0)
            except json.JSONDecodeError:
                return 0
        return 0

    def _calculate_retry_categories(self, media_files: list) -> tuple:
        """Categorize files by retry status and outcome"""
        succeeded_first_attempt = 0
        succeeded_after_retry = 0

        for file in media_files:
            if file.get('status') == 'completed':
                retry_count = self._extract_retry_count_from_file(file)
                if retry_count == 0:
                    succeeded_first_attempt += 1
                else:
                    succeeded_after_retry += 1

        return succeeded_first_attempt, succeeded_after_retry

    def _build_performance_response(self, analyses: list, processing_times: list, total_files: int, status_counts: dict, succeeded_first_attempt: int, succeeded_after_retry: int, failed: int, retry_counts: list, retry_success_rate: Optional[float], date_threshold: datetime) -> dict:
        """Build the performance metrics response"""
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
                "completed": status_counts['completed'],
                "failed": failed,
                "processing": status_counts['processing'],
                "pending": status_counts['pending'],
                "success_rate": round(status_counts['completed'] / total_files, 3) if total_files > 0 else None,
                "failure_rate": round(failed / total_files, 3) if total_files > 0 else None
            },
            "retry_statistics": {
                "total_files": total_files,
                "succeeded_first_attempt": succeeded_first_attempt,
                "succeeded_after_retry": succeeded_after_retry,
                "still_failing": failed,
                "max_retries_needed": max(retry_counts) if retry_counts else 0,
                "retry_success_rate": retry_success_rate
            },
            "throughput": {
                "files_per_day": round(total_files / max(1, (datetime.now(tz.utc) - date_threshold).days), 2) if total_files > 0 else 0
            }
        }
    
    def _get_error_metrics(
        self,
        date_threshold: datetime,
        interview_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get error and failure metrics"""

        try:
            failed_files = self._get_failed_files(date_threshold, interview_id)
            error_types = self._categorize_error_types(failed_files)
            total_count = self._get_total_file_count(date_threshold)

            return self._build_error_metrics_response(failed_files, error_types, total_count)

        except Exception as e:
            logger.error(f"Error getting error metrics: {str(e)}")
            return {"total_failures": 0, "error_type_breakdown": {}, "failure_rate_percent": 0}

    def _get_failed_files(self, date_threshold: datetime, interview_id: Optional[str]) -> list:
        """Get failed media files from database"""
        media_query = select(self.media_files_table).where(
            and_(
                self.media_files_table.c.created_at >= date_threshold,
                self.media_files_table.c.status == 'failed'
            )
        )

        if interview_id:
            media_query = media_query.where(self.media_files_table.c.interview_id == interview_id)

        media_result = self.db.execute(media_query)
        return [dict(row._mapping) for row in media_result]

    def _categorize_error_types(self, failed_files: list) -> dict:
        """Categorize errors from failed files metadata"""
        error_types = {}
        for file in failed_files:
            if file.get('metadata'):
                try:
                    metadata = json.loads(file['metadata']) if isinstance(file['metadata'], str) else file['metadata']
                    error_msg = metadata.get('error', 'Unknown error')
                    self._categorize_single_error(error_msg, error_types)
                except (json.JSONDecodeError, AttributeError):
                    error_types['parse_error'] = error_types.get('parse_error', 0) + 1
        return error_types

    def _categorize_single_error(self, error_msg: str, error_types: dict) -> None:
        """Categorize a single error message"""
        error_lower = error_msg.lower()
        if 'timeout' in error_lower:
            error_types['timeout'] = error_types.get('timeout', 0) + 1
        elif 'download' in error_lower:
            error_types['download_failed'] = error_types.get('download_failed', 0) + 1
        elif 'transcription' in error_lower:
            error_types['transcription_failed'] = error_types.get('transcription_failed', 0) + 1
        elif 'diarization' in error_lower:
            error_types['diarization_failed'] = error_types.get('diarization_failed', 0) + 1
        else:
            error_types['other'] = error_types.get('other', 0) + 1

    def _get_total_file_count(self, date_threshold: datetime) -> int:
        """Get total file count for failure rate calculation"""
        total_query = select(func.count(self.media_files_table.c.id)).where(
            self.media_files_table.c.created_at >= date_threshold
        )
        return self.db.execute(total_query).scalar() or 0

    def _build_error_metrics_response(self, failed_files: list, error_types: dict, total_count: int) -> dict:
        """Build the error metrics response"""
        return {
            "total_failures": len(failed_files),
            "error_type_breakdown": error_types,
            "failure_rate_percent": round(len(failed_files) / max(1, total_count) * 100, 2) if failed_files else 0
        }
    
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