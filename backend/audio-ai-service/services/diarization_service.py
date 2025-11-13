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
                # Set HuggingFace token as environment variable
                import os
                os.environ["HF_TOKEN"] = settings.HUGGINGFACE_TOKEN
                
                # Load pipeline - use older version 3.0 for compatibility
                self.pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.0",  # Changed from 3.1
                    use_auth_token=settings.HUGGINGFACE_TOKEN  # Explicitly pass token
                )
                
                # Set device
                if self.pipeline:  # Check if loaded successfully
                    device = torch.device(settings.WHISPER_DEVICE)
                    self.pipeline.to(device)
                    logger.info("Diarization pipeline loaded successfully")
                else:
                    raise RuntimeError("Pipeline failed to load")
                    
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
            raise RuntimeError(error_msg) from e
    
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
        speaker_segment_counts = {}  # Track number of segments per speaker
        
        for segment in segments:
            speaker = segment["speaker"]
            duration = segment["duration"]
            speaker_times[speaker] = speaker_times.get(speaker, 0) + duration
            speaker_segment_counts[speaker] = speaker_segment_counts.get(speaker, 0) + 1
        
        # Filter out likely noise (very short speaking time)
        NOISE_THRESHOLD = 0.03  # Speakers with <3% total time likely noise
        filtered_speakers = {}
        noise_speakers = []
        
        for speaker, time in speaker_times.items():
            percentage = (time / duration_seconds) * 100
            
            if percentage < (NOISE_THRESHOLD * 100):
                # Likely noise/background
                noise_speakers.append(speaker)
                logger.info(f"{speaker} filtered as noise ({percentage:.1f}% speaking time)")
            else:
                filtered_speakers[speaker] = time
        
        # Recalculate with filtered speakers
        actual_num_speakers = len(filtered_speakers)
        
        # Sort speakers by speaking time (descending)
        sorted_speakers = sorted(filtered_speakers.items(), key=lambda x: x[1], reverse=True)
        
        # Analysis
        is_suspicious = False
        risk_level = "low"
        reason = "Single speaker detected - normal interview"
        
        if actual_num_speakers == 1:
            # Only one real speaker (others were noise)
            risk_level = "low"
            if len(noise_speakers) > 0:
                reason = f"Single speaker detected (filtered {len(noise_speakers)} background noise)"
            else:
                reason = "Single speaker detected throughout interview"
        
        elif actual_num_speakers == 2:
            # Two real speakers - check if it's interviewer + candidate pattern
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
        
        elif actual_num_speakers > 2:
            # More than 2 speakers - definitely suspicious
            is_suspicious = True
            risk_level = "high"
            reason = f"{actual_num_speakers} speakers detected - likely external assistance"
        
        speaker_changes = self.detect_speaker_changes(segments)
        
        # Filter speaker changes to only include non-noise speakers
        filtered_speaker_changes = [
            change for change in speaker_changes 
            if change["from_speaker"] not in noise_speakers 
            and change["to_speaker"] not in noise_speakers
        ]
        
        return {
            "cheating_flag": is_suspicious,
            "risk_level": risk_level,
            "reason": reason,
            "num_speakers": actual_num_speakers,  # Filtered count
            "num_speakers_raw": num_speakers,  # Original count before filtering
            "noise_filtered": len(noise_speakers),
            "speaker_times": filtered_speakers,
            "speaker_time_percentages": {
                speaker: round((time / duration_seconds) * 100, 2) 
                for speaker, time in filtered_speakers.items()
            },
            "speaker_changes": filtered_speaker_changes,
            "total_speaker_changes": len(filtered_speaker_changes)
        }