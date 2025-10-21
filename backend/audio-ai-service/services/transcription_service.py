import whisper
from config import settings, logger
from typing import Dict, List, Optional
import torch


class TranscriptionService:
    """Handles audio transcription using Whisper"""
    
    def __init__(self):
        self.model = None
        self.device = settings.WHISPER_DEVICE
    
    def load_model(self):
        """Load Whisper model (lazy loading)"""
        if self.model is None:
            logger.info(f"Loading Whisper model: {settings.WHISPER_MODEL_SIZE}")
            logger.info(f"Using device: {self.device}")
            
            try:
                self.model = whisper.load_model(
                    settings.WHISPER_MODEL_SIZE,
                    device=self.device,
                    download_root=settings.MODEL_CACHE_DIR
                )
                logger.info("Whisper model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {str(e)}")
                raise
    
    def transcribe(self, audio_path: str) -> Dict:
        """
        Transcribe audio file
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Dictionary with transcription results
        """
        try:
            # Load model if not already loaded
            self.load_model()
            
            logger.info(f"Transcribing audio: {audio_path}")
            
            # Transcribe with word-level timestamps
            result = self.model.transcribe(
                audio_path,
                language="en",  # Force English for now
                word_timestamps=True,
                verbose=False
            )
            
            logger.info("Transcription completed successfully")
            
            # Extract word-level details
            words = []
            if "segments" in result:
                for segment in result["segments"]:
                    if "words" in segment:
                        for word in segment["words"]:
                            words.append({
                                "word": word.get("word", "").strip(),
                                "start": word.get("start", 0.0),
                                "end": word.get("end", 0.0),
                                "probability": word.get("probability", 0.0)
                            })
            
            return {
                "text": result.get("text", "").strip(),
                "language": result.get("language", "en"),
                "segments": result.get("segments", []),
                "words": words
            }
            
        except Exception as e:
            error_msg = f"Transcription error: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def get_word_count(self, text: str) -> int:
        """Count words in transcript"""
        return len(text.split())