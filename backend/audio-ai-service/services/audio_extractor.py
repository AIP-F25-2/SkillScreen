import ffmpeg
from config import logger
from utils.file_utils import create_temp_file, get_file_size_mb
from typing import Tuple, Optional
import os


class AudioExtractor:
    """Extracts audio from video files using ffmpeg"""
    
    def __init__(self):
        self.extracted_files = []
    
    def extract(self, video_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract audio from video file
        
        Args:
            video_path: Path to video file
        
        Returns:
            (audio_path, error_message) - audio_path is None if error
        """
        try:
            if not os.path.exists(video_path):
                return None, f"Video file not found: {video_path}"
            
            # Create temp file for audio
            audio_path = create_temp_file(suffix=".wav")
            
            logger.info(f"Extracting audio from {video_path}")
            logger.info(f"Output audio path: {audio_path}")
            
            # Extract audio using ffmpeg
            # -vn: no video
            # -acodec pcm_s16le: PCM 16-bit little-endian (uncompressed)
            # -ar 16000: 16kHz sample rate (optimal for speech)
            # -ac 1: mono channel
            stream = ffmpeg.input(video_path)
            stream = ffmpeg.output(
                stream, 
                audio_path,
                vn=None,  # No video
                acodec='pcm_s16le',  # PCM format
                ar='16000',  # 16kHz sample rate
                ac=1  # Mono
            )
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            # Verify audio file was created
            if not os.path.exists(audio_path):
                return None, "Audio extraction failed - no output file"
            
            audio_size = get_file_size_mb(audio_path)
            logger.info(f"Audio extracted successfully: {audio_size:.2f}MB")
            
            self.extracted_files.append(audio_path)
            return audio_path, None
            
        except ffmpeg.Error as e:
            error_msg = f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}"
            logger.error(error_msg)
            return None, error_msg
        except Exception as e:
            error_msg = f"Audio extraction error: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
    
    def get_audio_duration(self, audio_path: str) -> Optional[float]:
        """
        Get duration of audio file in seconds
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Duration in seconds, or None if error
        """
        try:
            probe = ffmpeg.probe(audio_path)
            duration = float(probe['format']['duration'])
            return duration
        except Exception as e:
            logger.error(f"Failed to get audio duration: {str(e)}")
            return None
    
    def cleanup(self):
        """Clean up all extracted audio files"""
        from utils.file_utils import cleanup_temp_file
        for filepath in self.extracted_files:
            cleanup_temp_file(filepath)
        self.extracted_files.clear()