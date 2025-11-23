import sys
sys.path.append('/common-service')

from db import UnitOfWork
from repositories.assessment_repository import AssessmentRepository
from services.llm_service import LLMService
from typing import Dict, List, Optional
from datetime import datetime, timezone
from config.settings import settings
import uuid
from config.logger import logger, log_assessment_started, log_assessment_completed, log_assessment_failed


UNKNOWN_TIME = 'Unknown time'


class AssessmentService:
    """Core service for assessment orchestration"""
    
    def __init__(self):
        """Initialize services"""
        self.llm_service = LLMService()
    
    def _determine_weights(
        self,
        interview_id: str,
        custom_weights: Optional[Dict[str, float]],
        interview: Dict,
        repo: AssessmentRepository,
        has_coding: bool
    ) -> tuple[Dict[str, float], str]:
        """Determine weights from custom, LLM, or defaults"""
        if custom_weights:
            logger.info("using_custom_weights", interview_id=interview_id, weights=custom_weights)
            return custom_weights, "custom"

        if not settings.use_llm_weights:
            weights = self._get_default_weights(has_coding)
            logger.info("using_default_weights_llm_disabled", interview_id=interview_id, weights=weights)
            return weights, "default"

        job_position_id = interview.get('job_position_id')
        if not job_position_id:
            weights = self._get_default_weights(has_coding)
            logger.info("using_default_weights", interview_id=interview_id, weights=weights)
            return weights, "default"

        job_position = repo.get_job_position(str(job_position_id))
        if not job_position:
            weights = self._get_default_weights(has_coding)
            logger.info("using_default_weights_no_job", interview_id=interview_id, weights=weights)
            return weights, "default"

        weights = self.llm_service.determine_weights_from_job_description(
            job_description=job_position.get('description', ''),
            job_title=job_position.get('title', ''),
            required_skills=job_position.get('required_skills', []),
            has_coding=has_coding
        )

        default_weights = self._get_default_weights(has_coding)
        if weights == default_weights:
            logger.info("using_default_weights_llm_failed", interview_id=interview_id, weights=weights)
            return weights, "default"

        logger.info("llm_determined_weights", interview_id=interview_id, weights=weights)
        return weights, "llm_determined"

    def _process_partial_assessment(
        self,
        interview_id: str,
        repo: AssessmentRepository,
        stuck_session_ids: list,
        llm_result: Dict
    ) -> Dict:
        """Process partial assessment when some sessions timed out"""
        sessions = repo.get_all_sessions_for_interview(interview_id)
        stuck_question_ids = [
            session.get('question_id', 'unknown')
            for session in sessions
            if str(session['id']) in stuck_session_ids
        ]

        llm_result['recommendation'] = 'Needs Review'
        partial_note = f"\n\n⚠️ INCOMPLETE ASSESSMENT: AI analysis timed out for question(s): {', '.join(stuck_question_ids)}. This assessment is based on partial data only. Manual review required."
        llm_result['reasoning'] = llm_result.get('reasoning', '') + partial_note

        logger.warning(
            "partial_assessment_generated",
            interview_id=interview_id,
            stuck_questions=stuck_question_ids
        )
        return llm_result

    def _build_assessment_data(
        self,
        interview_id: str,
        scores: Dict[str, float],
        llm_result: Dict,
        analyses: Dict[str, List[Dict]],
        weights: Dict[str, float],
        weights_source: str,
        is_partial_assessment: bool,
        stuck_session_ids: list,
        repo: AssessmentRepository
    ) -> Dict:
        """Build complete assessment data structure

        Args:
            interview_id: Interview UUID
            scores: Dict with overall, soft_skills, communication, technical, proctoring_risk
            llm_result: LLM recommendation and summary
            analyses: Dict with audio, video, text, coding lists
            weights: Scoring weights
            weights_source: Source of weights (custom/llm/default)
            is_partial_assessment: Whether assessment is partial
            stuck_session_ids: List of timed-out session IDs
            repo: AssessmentRepository for proctoring events
        """
        service_raw_results = {
            'audio': [a.get('raw_results', {}) for a in analyses['audio']],
            'video': [v.get('raw_results', {}) for v in analyses['video']],
            'text': [t.get('raw_results', {}) for t in analyses['text']],
            'coding': [c.get('raw_results', {}) for c in analyses['coding']]
        }

        evidence_clips = self._collect_evidence_clips(analyses['video'])

        return {
            'id': uuid.uuid4(),
            'interview_id': uuid.UUID(interview_id),
            'overall_score': round(scores['overall'], 2),
            'hard_skills_score': round(scores['technical'], 2) if scores.get('technical') else None,
            'soft_skills_score': round(scores['soft_skills'], 2),
            'communication_score': round(scores['communication'], 2),
            'technical_score': round(scores['technical'], 2) if scores.get('technical') else None,
            'proctoring_risk_score': round(scores['proctoring_risk'], 2),
            'recommendation': llm_result['recommendation'].lower().replace(' ', '_'),
            'evidence_clips': {
                'video_clips': evidence_clips,
                'proctoring_events': self._collect_proctoring_events(interview_id, repo),
                'service_results': service_raw_results,
                'scoring_weights': weights,
                'weights_source': weights_source,
                'is_partial_assessment': is_partial_assessment,
                'stuck_session_ids': stuck_session_ids if is_partial_assessment else []
            },
            'summary': llm_result['summary'],
            'reviewer_notes': llm_result['reasoning'],
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }

    async def generate_assessment(self, interview_id: str, custom_weights: Optional[Dict[str, float]] = None) -> Dict:
        """
        Generate final assessment for a completed interview

        Args:
            interview_id: Interview UUID
            custom_weights: Optional custom weights override

        Returns:
            Assessment data or error
        """

        log_assessment_started(interview_id)

        try:
            with UnitOfWork() as uow:
                repo = AssessmentRepository(uow)

                # 1. Check if assessment already exists
                if repo.assessment_exists(interview_id):
                    logger.warning("assessment_already_exists", interview_id=interview_id)
                    return {"status": "already_exists", "interview_id": interview_id}

                # 2. Verify all AI services completed
                completion_status = repo.check_sessions_with_timeout(interview_id, timeout_minutes=30)

            # Handle incomplete services
            if not completion_status['all_complete']:
                if not completion_status['stuck_sessions']:
                    logger.info("services_incomplete", interview_id=interview_id)
                    return {"status": "incomplete", "interview_id": interview_id}

                is_partial_assessment = True
                stuck_session_ids = completion_status['stuck_sessions']
                logger.warning(
                    "generating_partial_assessment_timeout",
                    interview_id=interview_id,
                    stuck_sessions=stuck_session_ids
                )
            else:
                is_partial_assessment = False
                stuck_session_ids = []

            # 3. Get interview info
            interview = repo.get_interview_info(interview_id)
            if not interview:
                logger.error("interview_not_found", interview_id=interview_id)
                return {"status": "error", "message": "Interview not found"}

            # 4. Get all AI analysis results
            all_analyses = repo.get_all_ai_analysis_for_interview(interview_id)
            if is_partial_assessment:
                all_analyses = [
                    a for a in all_analyses
                    if str(a.get('session_id')) not in stuck_session_ids
                ]

            # 5. Group analyses by service
            audio_analyses = [a for a in all_analyses if a['service_name'] == 'audio-ai-service']
            video_analyses = [a for a in all_analyses if a['service_name'] == 'video-ai-service']
            text_analyses = [a for a in all_analyses if a['service_name'] == 'text-service']
            coding_analyses = [a for a in all_analyses if a['service_name'] == 'coding-service']
            has_coding = len(coding_analyses) > 0

            # Check for cheating BEFORE calculating scores
            cheating_detected, cheating_evidence = self._detect_cheating_violations(
                audio_analyses, video_analyses
            )

            if cheating_detected:
                logger.error(
                    "cheating_detected_auto_reject",
                    interview_id=interview_id,
                    evidence_count=len(cheating_evidence)
                )
                return self._generate_cheating_rejection_assessment(
                    interview_id=interview_id,
                    cheating_evidence=cheating_evidence,
                    repo=repo
                )

            # 6. Determine weights
            weights, weights_source = self._determine_weights(
                interview_id, custom_weights, interview, repo, has_coding
            )

            # 7. Aggregate scores from each service
            audio_score = self._aggregate_audio_scores(audio_analyses)
            video_score = self._aggregate_video_scores(video_analyses)
            text_score = self._aggregate_text_scores(text_analyses)
            coding_score = self._aggregate_coding_scores(coding_analyses) if has_coding else None

            # 8-10. Calculate scores
            overall_score = self._calculate_overall_score(
                audio_score, video_score, text_score, coding_score, weights
            )
            soft_skills_score = self._calculate_soft_skills_score(audio_score, video_score)
            communication_score = self._calculate_communication_score(audio_score, text_score)
            technical_score = self._calculate_technical_score(text_score, coding_score)
            proctoring_risk_score = self._calculate_proctoring_risk_from_video_audio(
                audio_analyses, video_analyses
            )

            # 11. Prepare highlights and get LLM recommendation
            audio_highlights = self._extract_audio_highlights(audio_analyses)
            video_highlights = self._extract_video_highlights(video_analyses)
            text_highlights = self._extract_text_highlights(text_analyses)
            coding_highlights = self._extract_coding_highlights(coding_analyses) if has_coding else None

            llm_result = self.llm_service.generate_final_recommendation(
                interview_id=interview_id,
                overall_score=overall_score,
                soft_skills_score=soft_skills_score,
                communication_score=communication_score,
                technical_score=technical_score,
                proctoring_risk_score=proctoring_risk_score,
                audio_highlights=audio_highlights,
                video_highlights=video_highlights,
                text_highlights=text_highlights,
                coding_highlights=coding_highlights
            )

            # Handle partial assessment
            if is_partial_assessment:
                llm_result = self._process_partial_assessment(
                    interview_id, repo, stuck_session_ids, llm_result
                )

            # Build and save assessment
            assessment_data = self._build_assessment_data(
                interview_id=interview_id,
                scores={
                    'overall': overall_score,
                    'soft_skills': soft_skills_score,
                    'communication': communication_score,
                    'technical': technical_score,
                    'proctoring_risk': proctoring_risk_score
                },
                llm_result=llm_result,
                analyses={
                    'audio': audio_analyses,
                    'video': video_analyses,
                    'text': text_analyses,
                    'coding': coding_analyses
                },
                weights=weights,
                weights_source=weights_source,
                is_partial_assessment=is_partial_assessment,
                stuck_session_ids=stuck_session_ids,
                repo=repo
            )

            assessment_id = repo.save_assessment(assessment_data)

            log_assessment_completed(
                interview_id=interview_id,
                assessment_id=str(assessment_id),
                overall_score=overall_score,
                recommendation=llm_result['recommendation']
            )

            return {
                "status": "success",
                "interview_id": interview_id,
                "assessment_id": str(assessment_id),
                "overall_score": overall_score,
                "recommendation": llm_result['recommendation']
            }

        except Exception as e:
            logger.error(
                "assessment_generation_failed",
                interview_id=interview_id,
                error=str(e),
                error_type=type(e).__name__
            )
            log_assessment_failed(interview_id, str(e))

            return {
                "status": "error",
                "interview_id": interview_id,
                "message": f"Assessment generation failed: {str(e)}"
            }
    
    def _detect_cheating_violations(
        self, 
        audio_analyses: List[Dict], 
        video_analyses: List[Dict]
    ) -> tuple[bool, List[Dict]]:
        """
        Detect hard cheating violations that trigger automatic rejection
        
        Returns:
            (cheating_detected: bool, evidence: List[Dict])
        """
        evidence = []
        
        # Check audio analyses for cheating
        for idx, analysis in enumerate(audio_analyses):
            raw_results = analysis.get('raw_results', {})
            session_id = analysis.get('session_id')
            question_id = analysis.get('question_id', f'Question {idx + 1}')
            
            cheating_detection = raw_results.get('cheating_detection', {})
            
            # HARD VIOLATION: Audio explicitly detected cheating
            if cheating_detection.get('cheating_detected', False):
                evidence.append({
                    'source': 'audio-ai-service',
                    'session_id': str(session_id),
                    'question_id': question_id,
                    'violation_type': 'audio_cheating_detected',
                    'severity': 'critical',
                    'description': 'Multiple speakers or external assistance detected in audio',
                    'risk_level': cheating_detection.get('risk_level', 'high'),
                    'timestamp_range': str(analysis.get('created_at', UNKNOWN_TIME)),
                    'details': cheating_detection
                })
                
                logger.critical(
                    "audio_cheating_detected",
                    session_id=session_id,
                    question_id=question_id,
                    risk_level=cheating_detection.get('risk_level')
                )
            
            # HARD VIOLATION: Critical risk level
            if cheating_detection.get('risk_level') == 'critical':
                evidence.append({
                    'source': 'audio-ai-service',
                    'session_id': str(session_id),
                    'question_id': question_id,
                    'violation_type': 'critical_audio_risk',
                    'severity': 'critical',
                    'description': 'Critical risk level detected in audio analysis',
                    'risk_level': 'critical',
                    'timestamp_range': str(analysis.get('created_at', UNKNOWN_TIME)),
                    'details': cheating_detection
                })
        
        # Check video analyses for cheating
        for idx, analysis in enumerate(video_analyses):
            raw_results = analysis.get('raw_results', {})
            session_id = analysis.get('session_id')
            question_id = analysis.get('question_id', f'Question {idx + 1}')
            
            # HARD VIOLATION: Multiple people detected
            multi_person_ratio = raw_results.get('multi_person_ratio', 0)
            if multi_person_ratio > 0:
                evidence.append({
                    'source': 'video-ai-service',
                    'session_id': str(session_id),
                    'question_id': question_id,
                    'violation_type': 'multiple_people_detected',
                    'severity': 'critical',
                    'description': f'Multiple people detected in {multi_person_ratio * 100:.1f}% of video frames',
                    'multi_person_ratio': multi_person_ratio,
                    'timestamp_range': str(analysis.get('created_at', UNKNOWN_TIME)),
                    'details': {
                        'multi_person_ratio': multi_person_ratio,
                        'face_presence': raw_results.get('face_presence', 0)
                    }
                })
                
                logger.critical(
                    "multiple_people_detected",
                    session_id=session_id,
                    question_id=question_id,
                    multi_person_ratio=multi_person_ratio
                )
            
            # HARD VIOLATION: Very high cheating probability (>0.7 = 70%)
            cheating_prob = raw_results.get('cheating_probability', 0)
            if cheating_prob > 0.7:
                evidence.append({
                    'source': 'video-ai-service',
                    'session_id': str(session_id),
                    'question_id': question_id,
                    'violation_type': 'high_cheating_probability',
                    'severity': 'critical',
                    'description': f'High cheating probability detected: {cheating_prob * 100:.1f}%',
                    'cheating_probability': cheating_prob,
                    'timestamp_range': str(analysis.get('created_at', UNKNOWN_TIME)),
                    'details': {
                        'cheating_probability': cheating_prob,
                        'performance_score': raw_results.get('performance', {}).get('score', 0)
                    }
                })
                
                logger.critical(
                    "high_cheating_probability",
                    session_id=session_id,
                    question_id=question_id,
                    cheating_probability=cheating_prob
                )
        
        # Return True if ANY hard violations found
        return (len(evidence) > 0, evidence)
    
    def _generate_cheating_rejection_assessment(
        self,
        interview_id: str,
        cheating_evidence: List[Dict],
        repo: AssessmentRepository
    ) -> Dict:
        """
        Generate automatic rejection assessment when cheating is detected
        
        This creates a special assessment with:
        - Recommendation: "No Hire" (auto-reject)
        - Overall Score: 0
        - Proctoring Risk: 100
        - Detailed evidence of violations
        - Red flag status
        """
        
        # Build evidence summary
        violation_summary = []
        for ev in cheating_evidence:
            violation_summary.append(
                f"- [{ev['severity'].upper()}] {ev['violation_type']}: {ev['description']} "
                f"(Question: {ev['question_id']}, Session: {ev['session_id'][:8]}...)"
            )
        
        evidence_text = "\n".join(violation_summary)
        
        # Build detailed summary
        summary = f"""🚨 AUTOMATIC REJECTION - CHEATING DETECTED

The candidate has been automatically disqualified due to {len(cheating_evidence)} critical integrity violation(s) detected by our AI proctoring systems.

**Violations Detected:**
{evidence_text}

This interview has been flagged for manual review. The candidate is NOT recommended for hire due to confirmed cheating behavior."""
        
        # Build reviewer notes with evidence
        reviewer_notes = f"""⛔ AUTOMATIC REJECTION - INTEGRITY VIOLATION

This assessment was automatically generated due to critical cheating violations detected during the interview.

**Total Violations:** {len(cheating_evidence)}

**Evidence Details:**
{evidence_text}

**Proctoring Systems:**
- Audio AI: Detected multiple speakers / external assistance
- Video AI: Detected unauthorized persons or suspicious behavior

**Recommendation:** DO NOT HIRE - Integrity violation confirmed

**Next Steps:** 
1. Review attached evidence clips and timestamps
2. Flag candidate profile as high-risk
3. Do NOT proceed with hiring process
4. Consider blacklisting if company policy allows

**Legal Note:** All evidence is timestamped and stored for audit purposes.
"""
        
        # Save assessment with cheating flag
        assessment_data = {
            'id': uuid.uuid4(),
            'interview_id': uuid.UUID(interview_id),
            'overall_score': 0.0,
            'hard_skills_score': 0.0,
            'soft_skills_score': 0.0,
            'communication_score': 0.0,
            'technical_score': 0.0,
            'proctoring_risk_score': 100.0,
            'recommendation': 'no_hire',
            'evidence_clips': {
                'cheating_detected': True,
                'auto_rejected': True,
                'violation_count': len(cheating_evidence),
                'violations': cheating_evidence,
                'proctoring_events': self._collect_proctoring_events(interview_id, repo),
                'red_flag': True,
                'requires_manual_review': True
            },
            'summary': summary,
            'reviewer_notes': reviewer_notes,
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }
        
        assessment_id = repo.save_assessment(assessment_data)
        
        logger.error(
            "cheating_rejection_assessment_created",
            interview_id=interview_id,
            assessment_id=str(assessment_id),
            violation_count=len(cheating_evidence)
        )
        
        return {
            "status": "rejected_cheating",
            "interview_id": interview_id,
            "assessment_id": str(assessment_id),
            "overall_score": 0.0,
            "recommendation": "No Hire",
            "reason": "Cheating detected",
            "violation_count": len(cheating_evidence),
            "red_flag": True
        }
    
    def _get_default_weights(self, has_coding: bool) -> Dict[str, float]:
        """Get default weights from settings"""
        if has_coding:
            return settings.default_weights_with_coding
        else:
            return settings.default_weights_without_coding
    
    def _aggregate_audio_scores(self, audio_analyses: List[Dict]) -> Dict:
        """Aggregate scores from audio-ai-service"""
        if not audio_analyses:
            return {"overall": 0, "communication": 0, "confidence": 0, "fluency": 0}
        
        communication_scores = []
        confidence_scores = []
        
        for analysis in audio_analyses:
            raw_results = analysis.get('raw_results', {})
            
            # Communication score
            comm_data = raw_results.get('communication_score', {})
            if comm_data.get('communication_score'):
                communication_scores.append(float(comm_data['communication_score']) * 10)
            
            # Confidence score
            conf_data = raw_results.get('confidence_analysis', {})
            if conf_data.get('confidence_score'):
                confidence_scores.append(float(conf_data['confidence_score']) * 10)
        
        return {
            "overall": sum(communication_scores) / len(communication_scores) if communication_scores else 0,
            "communication": sum(communication_scores) / len(communication_scores) if communication_scores else 0,
            "confidence": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0,
            "fluency": sum(communication_scores) / len(communication_scores) if communication_scores else 0
        }
    
    def _aggregate_video_scores(self, video_analyses: List[Dict]) -> Dict:
        """Aggregate scores from video-ai-service"""
        if not video_analyses:
            return {"overall": 0, "engagement": 0, "attention": 0, "professionalism": 0}
        
        overall_scores = []
        engagement_scores = []
        attention_scores = []
        professionalism_scores = []
        
        for analysis in video_analyses:
            raw_results = analysis.get('raw_results', {})
            
            performance = raw_results.get('performance', {})
            if performance.get('score'):
                overall_scores.append(float(performance['score']))
            
            subscores = performance.get('subscores', {})
            if subscores.get('Engagement'):
                engagement_scores.append(float(subscores['Engagement']))
            if subscores.get('Attention'):
                attention_scores.append(float(subscores['Attention']))
            if subscores.get('Professionalism'):
                professionalism_scores.append(float(subscores['Professionalism']))
        
        return {
            "overall": sum(overall_scores) / len(overall_scores) if overall_scores else 0,
            "engagement": sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0,
            "attention": sum(attention_scores) / len(attention_scores) if attention_scores else 0,
            "professionalism": sum(professionalism_scores) / len(professionalism_scores) if professionalism_scores else 0
        }
    
    def _aggregate_text_scores(self, text_analyses: List[Dict]) -> Dict:
        """Aggregate scores from text-ai-service"""
        if not text_analyses:
            return {"overall": 0, "technical": 0, "communication": 0}
        
        technical_scores = []
        communication_scores = []
        
        for analysis in text_analyses:
            raw_results = analysis.get('raw_results', {})
            
            # Try to get from interview_summary first, then fall back to root level
            summary = raw_results.get('interview_summary', raw_results)
            
            tech_assessment = summary.get('technical_assessment', {})
            if tech_assessment.get('score'):
                technical_scores.append(float(tech_assessment['score']) * 10)
            
            comm_assessment = summary.get('communication_assessment', {})
            if comm_assessment.get('score'):
                communication_scores.append(float(comm_assessment['score']) * 10)
        
        overall = []
        if technical_scores:
            overall.extend(technical_scores)
        if communication_scores:
            overall.extend(communication_scores)
        
        return {
            "overall": sum(overall) / len(overall) if overall else 0,
            "technical": sum(technical_scores) / len(technical_scores) if technical_scores else 0,
            "communication": sum(communication_scores) / len(communication_scores) if communication_scores else 0
        }
    
    def _aggregate_coding_scores(self, coding_analyses: List[Dict]) -> Dict:
        """Aggregate scores from coding-service"""
        if not coding_analyses:
            return {"overall": 0, "correctness": 0}
        
        correctness_scores = []
        
        for analysis in coding_analyses:
            raw_results = analysis.get('raw_results', {})
            
            exec_results = raw_results.get('execution_results', {})
            if exec_results.get('correctness_score'):
                correctness_scores.append(float(exec_results['correctness_score']))
        
        return {
            "overall": sum(correctness_scores) / len(correctness_scores) if correctness_scores else 0,
            "correctness": sum(correctness_scores) / len(correctness_scores) if correctness_scores else 0
        }
    
    def _calculate_overall_score(
        self, 
        audio_score: Dict, 
        video_score: Dict, 
        text_score: Dict, 
        coding_score: Optional[Dict],
        weights: Dict[str, float]
    ) -> float:
        """Calculate weighted overall score"""
        
        total = 0.0
        
        if 'audio' in weights:
            total += audio_score['overall'] * weights['audio']
        
        if 'video' in weights:
            total += video_score['overall'] * weights['video']
        
        if 'text' in weights:
            total += text_score['overall'] * weights['text']
        
        if 'coding' in weights and coding_score:
            total += coding_score['overall'] * weights['coding']
        
        return total
    
    def _calculate_soft_skills_score(self, audio_score: Dict, video_score: Dict) -> float:
        """Calculate soft skills score (confidence + engagement)"""
        return (audio_score['confidence'] + video_score['engagement']) / 2
    
    def _calculate_communication_score(self, audio_score: Dict, text_score: Dict) -> float:
        """Calculate communication score"""
        return (audio_score['communication'] + text_score['communication']) / 2
    
    def _calculate_technical_score(self, text_score: Dict, coding_score: Optional[Dict]) -> float:
        """Calculate technical score"""
        if coding_score:
            return (text_score['technical'] * 0.4 + coding_score['overall'] * 0.6)
        else:
            return text_score['technical']
    
    def _calculate_proctoring_risk_from_video_audio(
        self, 
        audio_analyses: List[Dict], 
        video_analyses: List[Dict]
    ) -> float:
        """
        Calculate proctoring risk score from audio and video cheating detection
        
        Returns: 0-100 (higher = more risk)
        
        Combines:
        - Video: cheating_probability (0-1 scale)
        - Video: multi_person_ratio (0-1 scale)
        - Audio: cheating_detected (boolean)
        - Audio: risk_level (low/medium/high)
        """
        risk_scores = []
        
        # Process video analyses
        for analysis in video_analyses:
            raw_results = analysis.get('raw_results', {})
            
            # Cheating probability (0-1) → convert to 0-100
            cheating_prob = raw_results.get('cheating_probability', 0)
            risk_scores.append(float(cheating_prob) * 100)
            
            # Multi-person ratio → multiply by 100 for severity
            multi_person = raw_results.get('multi_person_ratio', 0)
            if multi_person > 0:
                risk_scores.append(float(multi_person) * 100)
        
        # Process audio analyses
        for analysis in audio_analyses:
            raw_results = analysis.get('raw_results', {})
            
            cheating_detection = raw_results.get('cheating_detection', {})
            
            # Check if cheating detected
            if cheating_detection.get('cheating_detected', False):
                risk_scores.append(80.0)
            
            # Map risk level to score
            risk_level = cheating_detection.get('risk_level', 'low')
            risk_mapping = {
                'low': 10,
                'medium': 50,
                'high': 80,
                'critical': 100
            }
            risk_scores.append(risk_mapping.get(risk_level, 10))
        
        # Average all risk scores
        if risk_scores:
            avg_risk = sum(risk_scores) / len(risk_scores)
            return min(100.0, avg_risk)
        
        return 10.0
    
    def _extract_audio_highlights(self, audio_analyses: List[Dict]) -> Dict:
        """Extract key highlights from audio analysis for LLM"""
        if not audio_analyses:
            return {}
        
        first = audio_analyses[0].get('raw_results', {})
        
        comm_score = first.get('communication_score', {})
        conf_analysis = first.get('confidence_analysis', {})
        filler_analysis = first.get('filler_analysis', {})
        cheating = first.get('cheating_detection', {})
        
        return {
            "communication_rating": comm_score.get('rating', 'N/A'),
            "confidence_level": conf_analysis.get('confidence_level', 'N/A'),
            "filler_rate": filler_analysis.get('total_rate_per_minute', 0),
            "cheating_risk": cheating.get('risk_level', 'low')
        }
    
    def _extract_video_highlights(self, video_analyses: List[Dict]) -> Dict:
        """Extract key highlights from video analysis for LLM"""
        if not video_analyses:
            return {}
        
        first = video_analyses[0].get('raw_results', {})
        performance = first.get('performance', {})
        subscores = performance.get('subscores', {})
        
        return {
            "engagement_score": subscores.get('Engagement', 0),
            "attention_score": subscores.get('Attention', 0),
            "professionalism": subscores.get('Professionalism', 0),
            "concerns": performance.get('concerns', []),
            "cheating_probability": first.get('cheating_probability', 0)
        }
    
    def _extract_text_highlights(self, text_analyses: List[Dict]) -> Dict:
        """Extract key highlights from text analysis for LLM"""
        if not text_analyses:
            return {}
        
        first = text_analyses[0].get('raw_results', {})
        summary = first.get('interview_summary', {})
        
        tech_assessment = summary.get('technical_assessment', {})
        comm_assessment = summary.get('communication_assessment', {})
        
        return {
            "technical_summary": tech_assessment.get('summary', ''),
            "communication_summary": comm_assessment.get('summary', ''),
            "strengths": summary.get('strengths', []),
            "red_flags": summary.get('red_flags', [])
        }
    
    def _extract_coding_highlights(self, coding_analyses: List[Dict]) -> Dict:
        """Extract key highlights from coding analysis for LLM"""
        if not coding_analyses:
            return {}
        
        first = coding_analyses[0].get('raw_results', {})
        exec_results = first.get('execution_results', {})
        code_quality = first.get('code_quality', {})
        
        return {
            "correctness_score": exec_results.get('correctness_score', 0),
            "test_cases_passed": exec_results.get('test_cases_passed', 0),
            "test_cases_total": exec_results.get('test_cases_total', 0),
            "time_complexity": exec_results.get('time_complexity', 'N/A'),
            "code_quality_score": code_quality.get('readability_score', 0)
        }
    
    def _collect_evidence_clips(self, video_analyses: List[Dict]) -> List[str]:
        """Collect evidence clip URLs from video analysis"""
        clips = []
        
        for analysis in video_analyses:
            raw_results = analysis.get('raw_results', {})
            thumbnail_blobs = raw_results.get('thumbnail_blobs', [])
            if thumbnail_blobs:
                clips.extend(thumbnail_blobs)
        
        return clips
    
    def _collect_proctoring_events(self, interview_id: str, repo: AssessmentRepository) -> List[Dict]:
        """
        Collect all proctoring events with timestamps and evidence
        
        Args:
            interview_id: Interview UUID
            repo: AssessmentRepository with active session
        
        Returns list of events with:
        - event_type
        - severity
        - description
        - timestamp (event_time_ms)
        - evidence (JSONB data)
        """
        from sqlalchemy import Table, Column, Text, Integer, String, Boolean, DateTime, MetaData, select
        from sqlalchemy.dialects.postgresql import UUID, JSONB
        
        metadata = MetaData()
        proctoring_events_table = Table(
            "proctoring_events",
            metadata,
            Column("id", UUID, primary_key=True),
            Column("interview_id", UUID),
            Column("session_id", UUID),
            Column("event_type", String),
            Column("severity", String),
            Column("description", Text),
            Column("rule_id", String),
            Column("event_time_ms", Integer),
            Column("evidence", JSONB),
            Column("flagged_for_review", Boolean),
            Column("reviewed_by", UUID),
            Column("reviewed_at", DateTime),
            Column("created_at", DateTime),
        )
        
        query = select(proctoring_events_table).where(
            proctoring_events_table.c.interview_id == interview_id
        ).order_by(proctoring_events_table.c.event_time_ms)
        
        result = repo.session.execute(query)
        events = []
        
        for row in result:
            event_dict = dict(row._mapping)
            events.append({
                'event_type': event_dict['event_type'],
                'severity': event_dict['severity'],
                'description': event_dict['description'],
                'timestamp_ms': event_dict['event_time_ms'],
                'timestamp_formatted': f"{event_dict['event_time_ms'] // 60000}:{(event_dict['event_time_ms'] % 60000) // 1000:02d}",
                'evidence': event_dict.get('evidence', {}),
                'flagged_for_review': event_dict.get('flagged_for_review', False)
            })
        
        return events