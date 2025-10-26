import numpy as np
from typing import Dict
from faster_whisper import WhisperModel
from config import logger
import time
import asyncio
from functools import partial


class StreamingTranscriber:
    """Simple real-time audio transcription - text only"""
    
    def __init__(self, model_size: str = "base"):
        """Initialize streaming transcriber"""
        logger.info(f"Initializing streaming transcriber with model: {model_size}")
        
        self.model = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8"
        )
        
        self.sample_rate = 16000
        self.audio_buffer = []
        self.transcript_buffer = []
        
        # Buffer settings
        self.buffer_duration = 3.0  # Keep last 3 seconds
        self.min_audio_length = 0.5  # Min 0.5s to transcribe
        
        # Silence detection
        self.silence_threshold = 0.01
        self.silence_duration = 0.0
        
        logger.info("Streaming transcriber initialized")
    
    async def process_chunk(self, audio_chunk: bytes) -> Dict:
        """
        Process audio chunk and return transcription
        
        Args:
            audio_chunk: Raw audio bytes (16kHz, 16-bit PCM, mono)
        
        Returns:
            {
                "text": str,
                "is_final": bool
            }
        """
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Check for silence
            is_silent = self._is_silence(audio_array)
            
            if is_silent:
                self.silence_duration += len(audio_array) / self.sample_rate
                
                # If silence > 1 second, finalize previous text
                if self.silence_duration > 1.0 and len(self.audio_buffer) > 0:
                    result = await self._transcribe_buffer(is_final=True)
                    self.audio_buffer = []
                    self.silence_duration = 0.0
                    return result
                
                return {"text": "", "is_final": False}
            else:
                self.silence_duration = 0.0
            
            # Add to buffer
            self.audio_buffer.append(audio_array)
            
            # Keep only last N seconds
            max_samples = int(self.buffer_duration * self.sample_rate)
            total_samples = sum(len(chunk) for chunk in self.audio_buffer)
            
            while total_samples > max_samples and len(self.audio_buffer) > 1:
                removed = self.audio_buffer.pop(0)
                total_samples -= len(removed)
            
            # Transcribe if we have enough audio
            if total_samples >= int(self.min_audio_length * self.sample_rate):
                result = await self._transcribe_buffer(is_final=False)
                return result
            
            return {"text": "", "is_final": False}
            
        except Exception as e:
            logger.error(f"Error processing chunk: {str(e)}")
            return {"text": "", "is_final": False, "error": str(e)}
    
    def _transcribe_sync(self, audio: np.ndarray, is_final: bool) -> Dict:
        """Synchronous transcription - runs in executor"""
        try:
            # Transcribe
            segments, _ = self.model.transcribe(
                audio,
                beam_size=1 if not is_final else 5,
                language="en",
                vad_filter=True
            )

            # Extract text only
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text)

            text = " ".join(text_parts).strip()

            # Save to transcript buffer if final
            if is_final and text:
                self.transcript_buffer.append(text)

            return {"text": text, "is_final": is_final}

        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            return {"text": "", "is_final": is_final, "error": str(e)}

    async def _transcribe_buffer(self, is_final: bool = False) -> Dict:
        """Transcribe the current audio buffer"""
        if not self.audio_buffer:
            return {"text": "", "is_final": is_final}

        # Concatenate buffer
        audio = np.concatenate(self.audio_buffer)

        # Run blocking transcription in executor to avoid blocking event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            partial(self._transcribe_sync, audio, is_final)
        )

        return result
    
    def _is_silence(self, audio: np.ndarray) -> bool:
        """Check if audio chunk is silent"""
        energy = np.abs(audio).mean()
        return energy < self.silence_threshold
    
    def get_full_transcript(self) -> str:
        """Get complete transcript from session"""
        return " ".join(self.transcript_buffer)
    
    async def finalize(self) -> Dict:
        """Finalize session and return complete transcript"""
        logger.info("Finalizing streaming session")
        
        # Transcribe any remaining buffer
        if self.audio_buffer:
            await self._transcribe_buffer(is_final=True)
        
        full_transcript = self.get_full_transcript()
        
        logger.info(f"Session finalized: {len(full_transcript)} characters")
        
        return {"full_transcript": full_transcript}