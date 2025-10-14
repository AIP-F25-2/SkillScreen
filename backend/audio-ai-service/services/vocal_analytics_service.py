import librosa
import numpy as np
from config import logger
from typing import Dict, List, Optional, Tuple


class VocalAnalyticsService:
    """Analyzes vocal features for soft-skill assessment"""
    
    def __init__(self):
        self.sample_rate = 16000  # 16kHz (same as audio extraction)
    
    def analyze(self, audio_path: str, transcript: str, 
                word_timestamps: List[Dict], duration: float) -> Dict:
        """
        Complete vocal analysis
        
        Args:
            audio_path: Path to audio file
            transcript: Transcribed text
            word_timestamps: List of words with timestamps
            duration: Audio duration in seconds
        
        Returns:
            Dictionary with all analytics
        """
        try:
            logger.info("Starting vocal analytics...")
            
            # Load audio
            audio, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Calculate metrics
            speaking_rate = self._calculate_speaking_rate(transcript, word_timestamps, duration)
            pitch_analysis = self._analyze_pitch(audio, sr)
            energy_analysis = self._analyze_energy(audio)
            pause_analysis = self._analyze_pauses(word_timestamps, duration)
            
            logger.info("Vocal analytics completed")
            
            return {
                "speaking_rate": speaking_rate,
                "pitch_analysis": pitch_analysis,
                "energy_analysis": energy_analysis,
                "pause_analysis": pause_analysis
            }
            
        except Exception as e:
            error_msg = f"Vocal analytics error: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _calculate_speaking_rate(self, transcript: str, 
                                  word_timestamps: List[Dict], 
                                  duration: float) -> Dict:
        """Calculate speaking rate (words per minute)"""
        try:
            word_count = len(transcript.split())
            duration_minutes = duration / 60.0
            
            if duration_minutes == 0:
                wpm = 0
            else:
                wpm = round(word_count / duration_minutes, 1)
            
            # Classify pace
            if wpm < 100:
                pace = "slow"
            elif wpm < 160:
                pace = "moderate"
            else:
                pace = "fast"
            
            logger.info(f"Speaking rate: {wpm} WPM ({pace})")
            
            return {
                "words_per_minute": wpm,
                "total_words": word_count,
                "speaking_duration": duration,
                "pace": pace
            }
            
        except Exception as e:
            logger.error(f"Speaking rate calculation failed: {str(e)}")
            return {
                "words_per_minute": 0,
                "total_words": 0,
                "speaking_duration": duration,
                "pace": "unknown"
            }
    
    def _analyze_pitch(self, audio: np.ndarray, sr: int) -> Dict:
        """Analyze pitch characteristics"""
        try:
            # Extract pitch using librosa
            pitches, magnitudes = librosa.piptrack(y=audio, sr=sr)
            
            # Get pitch values where magnitude is highest
            # Get pitch values where magnitude is highest
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
    
                # Filter valid pitch range (human voice: 80-400 Hz)
                # This excludes harmonics and noise
                if 80 <= pitch <= 400:
                    pitch_values.append(pitch)
           
            
            if len(pitch_values) == 0:
                return {
                    "mean_hz": 0,
                    "std_hz": 0,
                    "min_hz": 0,
                    "max_hz": 0,
                    "range_hz": 0
                }
            
            pitch_values = np.array(pitch_values)
            
            mean_pitch = float(np.mean(pitch_values))
            std_pitch = float(np.std(pitch_values))
            min_pitch = float(np.min(pitch_values))
            max_pitch = float(np.max(pitch_values))
            range_pitch = max_pitch - min_pitch
            
            logger.info(f"Pitch: mean={mean_pitch:.1f}Hz, std={std_pitch:.1f}Hz")
            
            return {
                "mean_hz": round(mean_pitch, 1),
                "std_hz": round(std_pitch, 1),
                "min_hz": round(min_pitch, 1),
                "max_hz": round(max_pitch, 1),
                "range_hz": round(range_pitch, 1)
            }
            
        except Exception as e:
            logger.error(f"Pitch analysis failed: {str(e)}")
            return {
                "mean_hz": 0,
                "std_hz": 0,
                "min_hz": 0,
                "max_hz": 0,
                "range_hz": 0
            }
    
    def _analyze_energy(self, audio: np.ndarray) -> Dict:
        """Analyze energy/volume dynamics"""
        try:
            # Calculate RMS energy
            rms = librosa.feature.rms(y=audio)[0]
            
            # Convert to dB
            rms_db = librosa.amplitude_to_db(rms)
            
            mean_energy = float(np.mean(rms_db))
            std_energy = float(np.std(rms_db))
            min_energy = float(np.min(rms_db))
            max_energy = float(np.max(rms_db))
            
            logger.info(f"Energy: mean={mean_energy:.1f}dB, std={std_energy:.1f}dB")
            
            return {
                "mean_db": round(mean_energy, 1),
                "std_db": round(std_energy, 1),
                "min_db": round(min_energy, 1),
                "max_db": round(max_energy, 1),
                "dynamic_range_db": round(max_energy - min_energy, 1)
            }
            
        except Exception as e:
            logger.error(f"Energy analysis failed: {str(e)}")
            return {
                "mean_db": 0,
                "std_db": 0,
                "min_db": 0,
                "max_db": 0,
                "dynamic_range_db": 0
            }
    
    def _analyze_pauses(self, word_timestamps: List[Dict], duration: float) -> Dict:
        """Analyze pause patterns"""
        try:
            if len(word_timestamps) < 2:
                return {
                    "total_pauses": 0,
                    "total_pause_duration": 0,
                    "avg_pause_duration": 0,
                    "max_pause_duration": 0,
                    "pause_rate_per_minute": 0
                }
            
            pauses = []
            
            # Calculate gaps between words
            for i in range(len(word_timestamps) - 1):
                current_word_end = word_timestamps[i].get("end", 0)
                next_word_start = word_timestamps[i + 1].get("start", 0)
                
                gap = next_word_start - current_word_end
                
                # Consider gap as pause if > 0.3 seconds
                if gap > 0.3:
                    pauses.append(gap)
            
            if len(pauses) == 0:
                return {
                    "total_pauses": 0,
                    "total_pause_duration": 0,
                    "avg_pause_duration": 0,
                    "max_pause_duration": 0,
                    "pause_rate_per_minute": 0
                }
            
            total_pauses = len(pauses)
            total_pause_duration = sum(pauses)
            avg_pause = np.mean(pauses)
            max_pause = max(pauses)
            
            # Pauses per minute
            duration_minutes = duration / 60.0
            pause_rate = total_pauses / duration_minutes if duration_minutes > 0 else 0
            
            logger.info(f"Pauses: {total_pauses} pauses, avg={avg_pause:.2f}s")
            
            return {
                "total_pauses": total_pauses,
                "total_pause_duration": round(total_pause_duration, 2),
                "avg_pause_duration": round(avg_pause, 2),
                "max_pause_duration": round(max_pause, 2),
                "pause_rate_per_minute": round(pause_rate, 1)
            }
            
        except Exception as e:
            logger.error(f"Pause analysis failed: {str(e)}")
            return {
                "total_pauses": 0,
                "total_pause_duration": 0,
                "avg_pause_duration": 0,
                "max_pause_duration": 0,
                "pause_rate_per_minute": 0
            }