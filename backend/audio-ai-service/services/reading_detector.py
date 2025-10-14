from typing import Dict
from config import logger


class ReadingDetector:
    """Detects if candidate is reading from script instead of speaking naturally"""
    
    def detect(self, vocal_analytics: Dict, filler_analysis: Dict) -> Dict:
        """
        Detect reading behavior based on speech patterns
        
        Reading indicators:
        - Very low filler count (< 1/min) - scripted speech has no fillers
        - Low pitch variance (monotone) - reading lacks natural prosody
        - Very consistent pace - no thinking pauses
        - No acoustic fillers - natural speech has um/uh
        - Very short or very few pauses - continuous reading flow
        
        Args:
            vocal_analytics: Vocal analysis results
            filler_analysis: Filler detection results
        
        Returns:
            Reading detection analysis with cheating flag
        """
        try:
            logger.info("Analyzing for reading behavior...")
            
            # Extract metrics
            pitch_std = vocal_analytics["pitch_analysis"]["std_hz"]
            pitch_range = vocal_analytics["pitch_analysis"]["range_hz"]
            avg_pause = vocal_analytics["pause_analysis"]["avg_pause_duration"]
            pause_rate = vocal_analytics["pause_analysis"]["pause_rate_per_minute"]
            filler_rate = filler_analysis["total_rate_per_minute"]
            acoustic_filler_count = filler_analysis["acoustic_count"]
            linguistic_filler_count = filler_analysis["linguistic_count"]
            wpm = vocal_analytics["speaking_rate"]["words_per_minute"]
            pace = vocal_analytics["speaking_rate"]["pace"]
            
            # Initialize
            reading_score = 0  # 0 = natural, 10 = definitely reading
            indicators = []
            confidence_level = "low"

            # Track individual category scores
            filler_score = 0
            pitch_score = 0
            pause_score = 0
            pace_score = 0

            # 1. Filler Rate Analysis (40% weight - 4 points max)
            if filler_rate < 1.0:
                filler_score += 2
                reading_score += 2
                indicators.append(f"Very low filler rate ({filler_rate:.2f}/min) - scripted speech typically has minimal fillers")

            if acoustic_filler_count == 0:
                filler_score += 1
                reading_score += 1
                indicators.append("No acoustic fillers (um/uh) detected - natural speech contains these disfluencies")

            if linguistic_filler_count == 0:
                filler_score += 1
                reading_score += 1
                indicators.append("No linguistic fillers - unnaturally clean speech")

            # 2. Pitch Monotony Analysis (30% weight - 3 points max)
            if pitch_std < 30:
                pitch_score += 2
                reading_score += 2
                indicators.append(f"Monotone delivery (pitch std: {pitch_std:.1f}Hz) - reading lacks natural pitch variation")

            if pitch_range < 100:
                pitch_score += 1
                reading_score += 1
                indicators.append(f"Very narrow pitch range ({pitch_range:.1f}Hz) - indicates flat, scripted delivery")

            # 3. Pause Pattern Analysis (20% weight - 2 points max)
            if avg_pause < 0.5:
                pause_score += 1
                reading_score += 1
                indicators.append(f"Very short pauses ({avg_pause:.2f}s avg) - no thinking time, continuous reading flow")

            if pause_rate < 3:
                pause_score += 1
                reading_score += 1
                indicators.append(f"Very few pauses ({pause_rate:.1f}/min) - unusually continuous speech")

            # 4. Speaking Rate Consistency (10% weight - 1 point max)
            # Reading often results in consistent moderate pace or very slow deliberate pace
            if pace == "moderate" and 130 <= wpm <= 145:
                pace_score += 1
                reading_score += 1
                indicators.append(f"Consistent reading pace detected ({wpm:.1f} WPM)")
            elif pace == "slow" and wpm < 100:
                pace_score += 1
                reading_score += 1
                indicators.append(f"Slow, deliberate pace ({wpm:.1f} WPM) - may indicate reading unfamiliar text")
            
            # Calculate reading probability (0-100%)
            reading_probability = min(100, reading_score * 10)
            
            # Determine assessment and cheating flag
            if reading_probability >= 70:
                assessment = "Highly likely reading from script"
                is_cheating = True
                confidence_level = "high"
                cheating_reason = "Strong evidence of scripted responses - monotone delivery, absence of natural speech disfluencies, and unusual pause patterns"
            elif reading_probability >= 50:
                assessment = "Likely reading or heavily rehearsed"
                is_cheating = True
                confidence_level = "medium"
                cheating_reason = "Multiple indicators suggest pre-written responses - limited pitch variation and unnatural speech flow"
            elif reading_probability >= 30:
                assessment = "Possibly over-rehearsed or reading portions"
                is_cheating = False  # Not severe enough to flag as cheating
                confidence_level = "low"
                cheating_reason = None
            else:
                assessment = "Natural spontaneous speech"
                is_cheating = False
                confidence_level = "low"
                cheating_reason = None
            
            logger.info(f"Reading detection: {reading_probability}% probability ({assessment})")
            if is_cheating:
                logger.warning(f"READING DETECTED: Flagged as cheating with {confidence_level} confidence")
            
            return {
                "reading_detected": is_cheating,
                "reading_probability": round(reading_probability, 1),
                "assessment": assessment,
                "confidence": confidence_level,
                "cheating_reason": cheating_reason,
                "indicators": indicators,
                "evidence": {
                    "filler_rate_per_min": round(filler_rate, 2),
                    "acoustic_fillers": acoustic_filler_count,
                    "linguistic_fillers": linguistic_filler_count,
                    "pitch_std_hz": round(pitch_std, 1),
                    "pitch_range_hz": round(pitch_range, 1),
                    "avg_pause_sec": round(avg_pause, 2),
                    "pause_rate_per_min": round(pause_rate, 1),
                    "speaking_pace": pace,
                    "words_per_minute": round(wpm, 1)
                },
                "score_breakdown": {
                    "filler_score": filler_score,
                    "pitch_score": pitch_score,
                    "pause_score": pause_score,
                    "pace_score": pace_score,
                    "total_score": reading_score,
                    "max_possible_score": 10
                }
            }
            
        except Exception as e:
            logger.error(f"Reading detection failed: {str(e)}")
            return {
                "reading_detected": False,
                "reading_probability": 0,
                "assessment": "Unable to assess",
                "confidence": "low",
                "error": str(e)
            }