from typing import Dict
from config import logger


class ConfidenceAnalyzer:
    """Analyzes speaking confidence based on vocal features"""
    
    def analyze(self, vocal_analytics: Dict, filler_analysis: Dict) -> Dict:
        """
        Analyze speaking confidence
        
        Confidence is calculated from:
        - Pitch stability (25%): Lower variance = more confident
        - Volume consistency (20%): Consistent energy = confident
        - Pause patterns (25%): Short, infrequent pauses = confident
        - Filler control (20%): Fewer fillers = more confident
        - Speaking rate (10%): Steady pace = confident
        
        Args:
            vocal_analytics: Results from VocalAnalyticsService
            filler_analysis: Results from FillerDetectionService
        
        Returns:
            Confidence analysis with score and breakdown
        """
        try:
            logger.info("Analyzing speaking confidence...")
            
            # Extract metrics
            pitch_std = vocal_analytics["pitch_analysis"]["std_hz"]
            energy_std = vocal_analytics["energy_analysis"]["std_db"]
            avg_pause = vocal_analytics["pause_analysis"]["avg_pause_duration"]
            pause_rate = vocal_analytics["pause_analysis"]["pause_rate_per_minute"]
            filler_rate = filler_analysis["total_rate_per_minute"]
            wpm = vocal_analytics["speaking_rate"]["words_per_minute"]
            
            # Calculate component scores (0-10)
            pitch_score = self._score_pitch_stability(pitch_std)
            volume_score = self._score_volume_consistency(energy_std)
            pause_score = self._score_pause_patterns(avg_pause, pause_rate)
            filler_score = self._score_filler_control(filler_rate)
            rate_score = self._score_speaking_rate(wpm)
            
            # Weighted average
            confidence_score = (
                pitch_score * 0.25 +
                volume_score * 0.20 +
                pause_score * 0.25 +
                filler_score * 0.20 +
                rate_score * 0.10
            )
            
            # Classification
            confidence_level = self._classify_confidence(confidence_score)
            
            # Identify key strengths and concerns
            strengths = self._identify_strengths(
                pitch_score, volume_score, pause_score, filler_score, rate_score
            )
            concerns = self._identify_concerns(
                pitch_score, volume_score, pause_score, filler_score, rate_score
            )
            
            logger.info(f"Confidence analysis complete: {confidence_score:.1f}/10 ({confidence_level})")
            
            return {
                "confidence_score": round(confidence_score, 1),
                "confidence_level": confidence_level,
                "breakdown": {
                    "pitch_stability": round(pitch_score, 1),
                    "volume_consistency": round(volume_score, 1),
                    "pause_patterns": round(pause_score, 1),
                    "filler_control": round(filler_score, 1),
                    "speaking_rate": round(rate_score, 1)
                },
                "indicators": {
                    "pitch_std_hz": round(pitch_std, 1),
                    "energy_std_db": round(energy_std, 1),
                    "avg_pause_sec": round(avg_pause, 2),
                    "pause_rate_per_min": round(pause_rate, 1),
                    "filler_rate_per_min": round(filler_rate, 2),
                    "words_per_minute": round(wpm, 1)
                },
                "strengths": strengths,
                "areas_for_improvement": concerns
            }
            
        except Exception as e:
            logger.error(f"Confidence analysis failed: {str(e)}")
            return {
                "confidence_score": 0,
                "confidence_level": "Unable to assess",
                "error": str(e)
            }
    
    def _score_pitch_stability(self, pitch_std: float) -> float:
        """
        Score pitch stability (0-10)
        
        Lower std = more stable = more confident
        Typical ranges:
        - 15-30 Hz std: Very confident (steady voice)
        - 30-50 Hz std: Confident
        - 50-80 Hz std: Moderate confidence
        - 80+ Hz std: Nervous/uncertain
        """
        if pitch_std <= 30:
            return 10
        elif pitch_std <= 50:
            return 10 - ((pitch_std - 30) / 4)  # 10 to 5
        elif pitch_std <= 80:
            return 5 - ((pitch_std - 50) / 6)   # 5 to 0
        else:
            return max(0, 5 - ((pitch_std - 80) / 10))
    
    def _score_volume_consistency(self, energy_std: float) -> float:
        """
        Score volume consistency (0-10)
        
        Lower std = more consistent = confident
        Typical ranges:
        - 5-10 dB std: Very consistent (confident)
        - 10-15 dB std: Moderately consistent
        - 15+ dB std: Inconsistent (nervous/fading)
        """
        if energy_std <= 10:
            return 10
        elif energy_std <= 15:
            return 10 - ((energy_std - 10) * 1)  # 10 to 5
        else:
            return max(0, 5 - ((energy_std - 15) * 0.5))
    
    def _score_pause_patterns(self, avg_pause: float, pause_rate: float) -> float:
        """
        Score pause patterns (0-10)
        
        Short, infrequent pauses = confident
        Long, frequent pauses = hesitant
        
        Ideal:
        - Avg pause: 0.5-1.5 seconds (thinking time)
        - Pause rate: 4-10 per minute (natural breaks)
        """
        # Score average pause duration
        if 0.5 <= avg_pause <= 1.5:
            pause_duration_score = 10
        elif avg_pause < 0.5:
            # Too short = rushing
            pause_duration_score = 10 - ((0.5 - avg_pause) * 8)
        elif avg_pause <= 2.5:
            # Slightly long
            pause_duration_score = 10 - ((avg_pause - 1.5) * 3)
        else:
            # Very long = hesitant
            pause_duration_score = max(0, 7 - ((avg_pause - 2.5) * 2))
        
        # Score pause frequency
        if 4 <= pause_rate <= 10:
            pause_freq_score = 10
        elif pause_rate < 4:
            # Too few pauses = rushing/reading
            pause_freq_score = 5 + (pause_rate * 1.25)
        elif pause_rate <= 15:
            # Slightly frequent
            pause_freq_score = 10 - ((pause_rate - 10) * 0.8)
        else:
            # Too frequent = very hesitant
            pause_freq_score = max(0, 6 - ((pause_rate - 15) * 0.5))
        
        # Average of both
        return (pause_duration_score + pause_freq_score) / 2
    
    def _score_filler_control(self, filler_rate: float) -> float:
        """
        Score filler control (0-10)
        
        Filler rate ranges:
        - 0-2/min: Excellent (may indicate reading)
        - 2-5/min: Very good
        - 5-8/min: Good/Average (natural speech)
        - 8-12/min: Below average (nervous)
        - 12+/min: Poor (very nervous)
        """
        if filler_rate <= 2:
            # Very few fillers - excellent but check if reading
            return 10
        elif filler_rate <= 5:
            # Very good range
            return 10 - ((filler_rate - 2) * 0.5)  # 10 to 8.5
        elif filler_rate <= 8:
            # Good/average range
            return 8.5 - ((filler_rate - 5) * 0.5)  # 8.5 to 7
        elif filler_rate <= 12:
            # Below average
            return 7 - ((filler_rate - 8) * 0.75)  # 7 to 4
        else:
            # Poor
            return max(0, 4 - ((filler_rate - 12) * 0.5))
    
    def _score_speaking_rate(self, wpm: float) -> float:
        """
        Score speaking rate (0-10)
        
        Ideal range: 120-150 WPM (calm, confident)
        - Too slow (< 100): Uncertain, struggling
        - Optimal (120-150): Confident, clear
        - Fast (150-180): Confident but rushing
        - Too fast (180+): Nervous, anxious
        """
        if 120 <= wpm <= 150:
            return 10
        elif 100 <= wpm < 120:
            # Slightly slow
            return 10 - ((120 - wpm) / 4)  # 10 to 5
        elif 150 < wpm <= 180:
            # Fast but manageable
            return 10 - ((wpm - 150) / 6)  # 10 to 5
        elif wpm < 100:
            # Very slow = uncertain
            return max(0, 5 - ((100 - wpm) / 5))
        else:
            # Very fast = nervous
            return max(0, 5 - ((wpm - 180) / 10))
    
    def _classify_confidence(self, score: float) -> str:
        """Classify confidence level from score"""
        if score >= 8.5:
            return "Very Confident"
        elif score >= 7.0:
            return "Confident"
        elif score >= 5.5:
            return "Moderately Confident"
        elif score >= 4.0:
            return "Low Confidence"
        else:
            return "Very Low Confidence"
    
    def _identify_strengths(self, pitch: float, volume: float, pause: float, 
                           filler: float, rate: float) -> list:
        """Identify confidence strengths (scores >= 7.5)"""
        strengths = []
        
        if pitch >= 7.5:
            strengths.append("Steady and stable voice tone")
        if volume >= 7.5:
            strengths.append("Consistent and clear volume")
        if pause >= 7.5:
            strengths.append("Natural pause patterns showing composure")
        if filler >= 7.5:
            strengths.append("Minimal filler words indicating preparation")
        if rate >= 7.5:
            strengths.append("Well-paced delivery")
        
        return strengths if strengths else ["Shows basic communication competence"]
    
    def _identify_concerns(self, pitch: float, volume: float, pause: float, 
                          filler: float, rate: float) -> list:
        """Identify areas needing improvement (scores < 6)"""
        concerns = []
        
        if pitch < 6:
            concerns.append("Voice tone shows uncertainty - practice to build confidence")
        if volume < 6:
            concerns.append("Inconsistent volume - work on projection and energy")
        if pause < 6:
            concerns.append("Pause patterns suggest hesitation - more preparation needed")
        if filler < 6:
            concerns.append("High filler word usage - practice reduces this naturally")
        if rate < 6:
            concerns.append("Speaking pace needs adjustment - aim for 120-150 words/minute")
        
        return concerns