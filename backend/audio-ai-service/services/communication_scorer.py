from typing import Dict, List
from config import logger


class CommunicationScorer:
    """Calculates overall communication effectiveness score"""
    
    def calculate(self, vocal_analytics: Dict, filler_analysis: Dict,
                  confidence_analysis: Dict, reading_detection: Dict) -> Dict:
        """
        Calculate overall communication score
        
        Components:
        - Clarity (40%): Volume, articulation, speaking rate
        - Fluency (30%): Pauses, fillers, flow
        - Confidence (20%): From confidence analysis
        - Engagement (10%): Pitch variety, energy dynamics
        
        Penalties:
        - Reading detected: -30% (high confidence) or -15% (medium confidence)
        
        Args:
            vocal_analytics: Vocal analysis results
            filler_analysis: Filler detection results
            confidence_analysis: Confidence analysis results
            reading_detection: Reading detection results
        
        Returns:
            Communication score with breakdown
        """
        try:
            logger.info("Calculating communication score...")
            
            # Calculate component scores
            clarity_score = self._score_clarity(vocal_analytics)
            fluency_score = self._score_fluency(vocal_analytics, filler_analysis)
            confidence_score = confidence_analysis["confidence_score"]
            engagement_score = self._score_engagement(vocal_analytics)
            
            # Weighted total (before penalties)
            total_score = (
                clarity_score * 0.40 +
                fluency_score * 0.30 +
                confidence_score * 0.20 +
                engagement_score * 0.10
            )
            
            # Apply reading penalty
            penalty_applied = None
            original_score = total_score
            
            if reading_detection["reading_detected"]:
                if reading_detection["confidence"] == "high":
                    total_score *= 0.70  # 30% penalty
                    penalty_applied = f"30% penalty: {reading_detection['cheating_reason']}"
                elif reading_detection["confidence"] == "medium":
                    total_score *= 0.85  # 15% penalty
                    penalty_applied = f"15% penalty: {reading_detection['cheating_reason']}"
            
            # Classification
            rating = self._classify_score(total_score)
            
            # Identify strengths and weaknesses
            strengths = self._identify_strengths(
                clarity_score, fluency_score, confidence_score, engagement_score
            )
            improvements = self._identify_improvements(
                clarity_score, fluency_score, confidence_score, engagement_score
            )
            
            logger.info(f"Communication score: {total_score:.1f}/10 ({rating})")
            if penalty_applied:
                logger.warning(f"Penalty applied: {penalty_applied}")
            
            return {
                "communication_score": round(total_score, 1),
                "original_score": round(original_score, 1) if penalty_applied else None,
                "rating": rating,
                "component_scores": {
                    "clarity": round(clarity_score, 1),
                    "fluency": round(fluency_score, 1),
                    "confidence": round(confidence_score, 1),
                    "engagement": round(engagement_score, 1)
                },
                "strengths": strengths,
                "areas_for_improvement": improvements,
                "penalty_applied": penalty_applied
            }
            
        except Exception as e:
            logger.error(f"Communication scoring failed: {str(e)}")
            return {
                "communication_score": 0,
                "rating": "Unable to assess",
                "error": str(e)
            }
    
    def _score_clarity(self, vocal_analytics: Dict) -> float:
        """Score clarity (0-10) - volume and speaking rate"""
        wpm = vocal_analytics["speaking_rate"]["words_per_minute"]
        mean_energy = vocal_analytics["energy_analysis"]["mean_db"]
        
        # Speaking rate score
        if 120 <= wpm <= 160:
            pace_score = 10
        elif 100 <= wpm < 120 or 160 < wpm <= 180:
            pace_score = 7
        elif 90 <= wpm < 100 or 180 < wpm <= 200:
            pace_score = 5
        else:
            pace_score = 3
        
        # Volume score
        if mean_energy > -25:
            volume_score = 10
        elif mean_energy > -35:
            volume_score = 7
        elif mean_energy > -45:
            volume_score = 5
        else:
            volume_score = 3
        
        return (pace_score + volume_score) / 2
    
    def _score_fluency(self, vocal_analytics: Dict, filler_analysis: Dict) -> float:
        """Score fluency (0-10) - pauses and fillers"""
        filler_rate = filler_analysis["total_rate_per_minute"]
        pause_rate = vocal_analytics["pause_analysis"]["pause_rate_per_minute"]
        avg_pause = vocal_analytics["pause_analysis"]["avg_pause_duration"]
        
        # Filler score (moderate is normal)
        if 2 <= filler_rate <= 5:
            filler_score = 10
        elif filler_rate < 2:
            filler_score = 8  # Too few might indicate reading
        elif 5 < filler_rate <= 8:
            filler_score = 7
        elif 8 < filler_rate <= 12:
            filler_score = 4
        else:
            filler_score = 2
        
        # Pause score
        if 4 <= pause_rate <= 10 and avg_pause < 1.5:
            pause_score = 10
        elif pause_rate > 15 or avg_pause > 2.5:
            pause_score = 5
        elif pause_rate < 3:
            pause_score = 7  # Too few pauses
        else:
            pause_score = 7
        
        return (filler_score + pause_score) / 2
    
    def _score_engagement(self, vocal_analytics: Dict) -> float:
        """Score engagement (0-10) - pitch and energy variety"""
        pitch_range = vocal_analytics["pitch_analysis"]["range_hz"]
        dynamic_range = vocal_analytics["energy_analysis"]["dynamic_range_db"]
        
        # Pitch variety score
        if pitch_range > 150:
            pitch_score = 10
        elif pitch_range > 100:
            pitch_score = 7
        elif pitch_range > 50:
            pitch_score = 5
        else:
            pitch_score = 3
        
        # Energy dynamics score
        if dynamic_range > 40:
            energy_score = 10
        elif dynamic_range > 25:
            energy_score = 7
        elif dynamic_range > 15:
            energy_score = 5
        else:
            energy_score = 3
        
        return (pitch_score + energy_score) / 2
    
    def _classify_score(self, score: float) -> str:
        """Classify communication score"""
        if score >= 8.5:
            return "Excellent"
        elif score >= 7.0:
            return "Good"
        elif score >= 5.5:
            return "Average"
        elif score >= 4.0:
            return "Below Average"
        else:
            return "Poor"
    
    def _identify_strengths(self, clarity: float, fluency: float,
                           confidence: float, engagement: float) -> List[str]:
        """Identify communication strengths"""
        strengths = []
        
        if clarity >= 8:
            strengths.append("Clear and well-paced delivery")
        if fluency >= 8:
            strengths.append("Smooth and fluent speech")
        if confidence >= 8:
            strengths.append("Confident communication style")
        if engagement >= 8:
            strengths.append("Engaging and dynamic presentation")
        
        if not strengths:
            # Find best component
            scores = {
                "clarity": clarity,
                "fluency": fluency,
                "confidence": confidence,
                "engagement": engagement
            }
            best = max(scores.items(), key=lambda x: x[1])
            if best[1] >= 6:
                strengths.append(f"Adequate {best[0]}")
            else:
                strengths.append("Shows basic communication competence")
        
        return strengths
    
    def _identify_improvements(self, clarity: float, fluency: float,
                               confidence: float, engagement: float) -> List[str]:
        """Identify areas needing improvement"""
        improvements = []
        
        if clarity < 6:
            improvements.append("Improve speaking pace and volume projection")
        if fluency < 6:
            improvements.append("Reduce filler words and manage pauses better")
        if confidence < 6:
            improvements.append("Build confidence through practice and preparation")
        if engagement < 6:
            improvements.append("Add more vocal variety and energy to engage listeners")
        
        return improvements if improvements else []