from pyannote.audio import Pipeline
from config import settings, logger
from typing import Dict, List, Optional
import torch


class DiarizationService:
    """Speaker diarization using pyannote.audio"""
    
    def __init__(self):
        self.pipeline = None
    
    def load_pipeline(self):
        """Load pyannote diarization pipeline"""
        if self.pipeline is None:
            if not settings.HUGGINGFACE_TOKEN:
                raise ValueError("HUGGINGFACE_TOKEN not set in environment")
            
            logger.info("Loading pyannote diarization pipeline...")
            try:
                self.pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=settings.HUGGINGFACE_TOKEN
                )
                
                # Set device
                device = torch.device(settings.WHISPER_DEVICE)
                self.pipeline.to(device)
                
                logger.info("Diarization pipeline loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load diarization pipeline: {str(e)}")
                raise
    
    def diarize(self, audio_path: str) -> Dict:
        """
        Perform speaker diarization
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Diarization results with speaker segments
        """
        try:
            # Load pipeline if not loaded
            self.load_pipeline()
            
            logger.info(f"Running diarization on: {audio_path}")
            
            # Run diarization
            diarization = self.pipeline(audio_path)
            
            # Extract speaker segments
            speakers = set()
            segments = []
            
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                speakers.add(speaker)
                segments.append({
                    "start": round(turn.start, 2),
                    "end": round(turn.end, 2),
                    "duration": round(turn.end - turn.start, 2),
                    "speaker": speaker
                })
            
            num_speakers = len(speakers)
            
            logger.info(f"Diarization complete: {num_speakers} speaker(s) detected")
            
            return {
                "num_speakers": num_speakers,
                "speakers": list(speakers),
                "segments": segments,
                "total_segments": len(segments)
            }
            
        except Exception as e:
            error_msg = f"Diarization error: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def detect_speaker_changes(self, segments: List[Dict]) -> List[Dict]:
        """
        Detect when speakers change
        
        Args:
            segments: List of speaker segments
        
        Returns:
            List of speaker change events
        """
        changes = []
        
        for i in range(1, len(segments)):
            prev_speaker = segments[i-1]["speaker"]
            curr_speaker = segments[i]["speaker"]
            
            if prev_speaker != curr_speaker:
                changes.append({
                    "timestamp": segments[i]["start"],
                    "from_speaker": prev_speaker,
                    "to_speaker": curr_speaker
                })
        
        return changes
    
    def assess_cheating_risk(self, diarization_result: Dict, duration_seconds: float) -> Dict:
        """
        Assess cheating risk based on diarization
        
        Args:
            diarization_result: Results from diarization
            duration_seconds: Total audio duration
        
        Returns:
            Cheating risk assessment
        """
        num_speakers = diarization_result["num_speakers"]
        segments = diarization_result["segments"]
        
        # Calculate speaking time per speaker
        speaker_times = {}
        for segment in segments:
            speaker = segment["speaker"]
            duration = segment["duration"]
            speaker_times[speaker] = speaker_times.get(speaker, 0) + duration
        
        # Sort speakers by speaking time (descending)
        sorted_speakers = sorted(speaker_times.items(), key=lambda x: x[1], reverse=True)
        
        # Analysis
        is_suspicious = False
        risk_level = "low"
        reason = "Single speaker detected - normal interview"
        
        if num_speakers == 1:
            # Only one speaker - normal
            risk_level = "low"
            reason = "Single speaker detected throughout interview"
        
        elif num_speakers == 2:
            # Two speakers - check if it's interviewer + candidate pattern
            primary_speaker_time = sorted_speakers[0][1]
            secondary_speaker_time = sorted_speakers[1][1]
            
            # Calculate percentage of speaking time
            primary_percentage = (primary_speaker_time / duration_seconds) * 100
            secondary_percentage = (secondary_speaker_time / duration_seconds) * 100
            
            # If secondary speaker talks < 10% of time, likely interviewer asking questions
            if secondary_percentage < 10:
                is_suspicious = False
                risk_level = "low"
                reason = f"Two speakers detected: Primary speaker {primary_percentage:.1f}%, Secondary {secondary_percentage:.1f}% (likely interviewer asking questions)"
            
            # If both speakers talk ~equally (40-60% each), suspicious
            elif 40 <= primary_percentage <= 60 and 40 <= secondary_percentage <= 60:
                is_suspicious = True
                risk_level = "high"
                reason = f"Two speakers with equal speaking time detected ({primary_percentage:.1f}% vs {secondary_percentage:.1f}%) - possible collaboration"
            
            # Secondary speaks 10-40% - moderate concern
            else:
                is_suspicious = True
                risk_level = "medium"
                reason = f"Two speakers: Primary {primary_percentage:.1f}%, Secondary {secondary_percentage:.1f}% - unusual distribution, possible coaching"
        
        elif num_speakers > 2:
            # More than 2 speakers - definitely suspicious
            is_suspicious = True
            risk_level = "high"
            reason = f"{num_speakers} speakers detected - likely external assistance"
        
        speaker_changes = self.detect_speaker_changes(segments)
        
        return {
            "cheating_flag": is_suspicious,
            "risk_level": risk_level,
            "reason": reason,
            "num_speakers": num_speakers,
            "speaker_times": speaker_times,
            "speaker_time_percentages": {
                speaker: round((time / duration_seconds) * 100, 2) 
                for speaker, time in speaker_times.items()
            },
            "speaker_changes": speaker_changes,
            "total_speaker_changes": len(speaker_changes)
        }