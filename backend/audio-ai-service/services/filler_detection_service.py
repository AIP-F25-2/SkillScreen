import re
from typing import Dict, List
from config import logger
import librosa
import numpy as np


class FillerDetectionService:
    """Detects both linguistic and acoustic filler words"""
    
    def __init__(self):
        # Linguistic filler patterns (detected from transcript)
        self.filler_patterns = {
            'um': r'\bum+\b',
            'uh': r'\buh+\b',
            'er': r'\ber+\b',
            'ah': r'\bah+\b',
            'like': r'\blike\b',
            'you know': r'\byou know\b',
            'i mean': r'\bi mean\b',
            'so': r'\bso\b',
            'well': r'\bwell\b',
            'basically': r'\bbasically\b',
            'actually': r'\bactually\b',
            'literally': r'\bliterally\b',
            'kind of': r'\bkind of\b',
            'sort of': r'\bsort of\b'
        }
    
    def detect_from_words(self, words: List[Dict]) -> Dict:
        """
        Detect linguistic filler words from transcript
        
        Args:
            words: List of word dictionaries with 'word', 'start', 'end' keys
        
        Returns:
            Dictionary with filler analysis
        """
        filler_words = {}
        
        for word_obj in words:
            word = word_obj.get('word', '').lower().strip()
            
            # Check against each filler pattern
            for filler_type, pattern in self.filler_patterns.items():
                if re.match(pattern, word, re.IGNORECASE):
                    if filler_type not in filler_words:
                        filler_words[filler_type] = {
                            'count': 0,
                            'timestamps': []
                        }
                    
                    filler_words[filler_type]['count'] += 1
                    filler_words[filler_type]['timestamps'].append({
                        'start': word_obj.get('start'),
                        'end': word_obj.get('end'),
                        'text': word
                    })
        
        total_fillers = sum(f['count'] for f in filler_words.values())
        
        logger.info(f"Detected {total_fillers} linguistic filler words")
        
        return {
            'filler_words': filler_words,
            'total_fillers': total_fillers
        }
    
    def detect_acoustic_fillers(self, audio_path: str, word_timestamps: List[Dict]) -> Dict:
        """
        Detect acoustic fillers (um, uh, er, ah) from audio gaps between words
        
        Strategy:
        1. Find gaps between words (0.2-1.0 seconds)
        2. Check if there's speech energy in the gap
        3. If yes, likely an acoustic filler that Whisper removed
        
        Args:
            audio_path: Path to audio file
            word_timestamps: Word timestamps from transcription
        
        Returns:
            Dictionary with acoustic filler detection results
        """
        try:
            logger.info("Starting acoustic filler detection...")
            
            # Load audio
            audio, sr = librosa.load(audio_path, sr=16000)
            
            # Calculate RMS energy for voice activity detection
            frame_length = int(0.025 * sr)  # 25ms frames
            hop_length = int(0.010 * sr)    # 10ms hop
            
            rms = librosa.feature.rms(
                y=audio, 
                frame_length=frame_length,
                hop_length=hop_length
            )[0]
            
            # Calculate energy threshold (20th percentile = silence level)
            silence_threshold = np.percentile(rms, 20)
            speech_threshold = silence_threshold * 2  # Speech is 2x silence energy
            
            # Detect speech activity
            is_speech = rms > speech_threshold
            
            # Find acoustic fillers in gaps between words
            acoustic_fillers = []
            
            for i in range(len(word_timestamps) - 1):
                word_end = word_timestamps[i].get("end", 0)
                next_word_start = word_timestamps[i + 1].get("start", 0)
                
                gap_duration = next_word_start - word_end
                
                # Check gaps between 0.2 and 1.0 seconds (typical filler duration)
                if 0.2 <= gap_duration <= 1.0:
                    # Convert time to frame indices
                    gap_start_frame = int(word_end * sr / hop_length)
                    gap_end_frame = int(next_word_start * sr / hop_length)
                    
                    # Ensure indices are within bounds
                    if gap_start_frame < len(is_speech) and gap_end_frame <= len(is_speech):
                        gap_speech = is_speech[gap_start_frame:gap_end_frame]
                        
                        # Calculate speech activity ratio in gap
                        if len(gap_speech) > 0:
                            speech_ratio = np.sum(gap_speech) / len(gap_speech)
                            
                            # If >30% of gap contains speech, likely a filler
                            if speech_ratio > 0.3:
                                # Calculate average energy in gap
                                gap_energy = np.mean(rms[gap_start_frame:gap_end_frame])
                                
                                # Confidence based on speech ratio and energy
                                if speech_ratio > 0.6 and gap_energy > speech_threshold * 1.5:
                                    confidence = "high"
                                elif speech_ratio > 0.4:
                                    confidence = "medium"
                                else:
                                    confidence = "low"
                                
                                acoustic_fillers.append({
                                    "start": round(word_end, 2),
                                    "end": round(next_word_start, 2),
                                    "duration": round(gap_duration, 2),
                                    "type": "acoustic_filler",
                                    "confidence": confidence,
                                    "speech_ratio": round(speech_ratio, 2)
                                })
            
            logger.info(f"Detected {len(acoustic_fillers)} acoustic fillers")
            
            return {
                "count": len(acoustic_fillers),
                "timestamps": acoustic_fillers
            }
            
        except Exception as e:
            logger.error(f"Acoustic filler detection failed: {str(e)}")
            return {
                "count": 0,
                "timestamps": [],
                "error": str(e)
            }
    
    def detect_combined(self, audio_path: str, word_timestamps: List[Dict], 
                       duration: float) -> Dict:
        """
        Detect both linguistic and acoustic fillers
        
        Args:
            audio_path: Path to audio file
            word_timestamps: Word timestamps from transcription
            duration: Audio duration in seconds
        
        Returns:
            Combined filler analysis
        """
        # Linguistic fillers from transcript
        linguistic_result = self.detect_from_words(word_timestamps)
        
        # Acoustic fillers from audio analysis
        acoustic_result = self.detect_acoustic_fillers(audio_path, word_timestamps)
        
        # Combined totals
        linguistic_count = linguistic_result["total_fillers"]
        acoustic_count = acoustic_result["count"]
        total_fillers = linguistic_count + acoustic_count
        
        # Calculate rates
        duration_minutes = duration / 60.0
        linguistic_rate = round(linguistic_count / duration_minutes, 2) if duration_minutes > 0 else 0
        acoustic_rate = round(acoustic_count / duration_minutes, 2) if duration_minutes > 0 else 0
        total_rate = round(total_fillers / duration_minutes, 2) if duration_minutes > 0 else 0
        
        logger.info(f"Total fillers: {total_fillers} ({linguistic_count} linguistic + {acoustic_count} acoustic)")
        logger.info(f"Combined filler rate: {total_rate} per minute")
        
        return {
            "linguistic_fillers": linguistic_result["filler_words"],
            "linguistic_count": linguistic_count,
            "linguistic_rate_per_minute": linguistic_rate,
            
            "acoustic_fillers": acoustic_result["timestamps"],
            "acoustic_count": acoustic_count,
            "acoustic_rate_per_minute": acoustic_rate,
            
            "total_fillers": total_fillers,
            "total_rate_per_minute": total_rate,
            
            "summary": {
                "linguistic": f"{linguistic_count} words (like, so, well, etc.)",
                "acoustic": f"{acoustic_count} sounds (um, uh, er, ah)",
                "total": f"{total_fillers} total fillers",
                "rate": f"{total_rate} per minute"
            }
        }
    
    def get_filler_summary(self, filler_results: Dict, duration: float) -> Dict:
        """
        Generate summary statistics for filler words
        
        Args:
            filler_results: Results from detect_from_words or detect_combined
            duration: Audio duration in seconds
        
        Returns:
            Summary statistics
        """
        # Handle both old format (detect_from_words) and new format (detect_combined)
        if "linguistic_fillers" in filler_results:
            # New combined format
            filler_words = filler_results["linguistic_fillers"]
            total_fillers = filler_results["total_fillers"]
        else:
            # Old format
            filler_words = filler_results.get("filler_words", {})
            total_fillers = filler_results.get("total_fillers", 0)
        
        duration_minutes = duration / 60.0
        filler_rate = round(total_fillers / duration_minutes, 2) if duration_minutes > 0 else 0
        
        # Sort fillers by count
        filler_counts = [
            {'type': ftype, 'count': data['count']} 
            for ftype, data in filler_words.items()
        ]
        filler_counts.sort(key=lambda x: x['count'], reverse=True)
        
        return {
            'filler_rate_per_minute': filler_rate,
            'most_common_fillers': filler_counts[:5],
            'filler_percentage': 0  # Could calculate if we track total word count
        }