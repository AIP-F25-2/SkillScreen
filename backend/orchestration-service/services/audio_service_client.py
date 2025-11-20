"""
Audio AI Service Client

Handles communication with audio-ai-service for:
- Audio/video processing
- Transcription
- Filler word detection
- Speaker analysis
- Vocal analytics
"""

import httpx
import logging
from typing import Dict, Any, Optional
from config import settings

logger = logging.getLogger(__name__)


class AudioServiceClient:
    """Client for audio-ai-service API"""
    
    def __init__(self):
        self.base_url = settings.AUDIO_AI_SERVICE_URL
        self.timeout = settings.PROCESSING_TIMEOUT
        
    async def process_interview_audio(
        self,
        interview_id: str,
        session_id: str,
        media_file_id: str
    ) -> Dict[str, Any]:
        """
        Trigger audio processing for interview recording
        
        This is async - the service will process in background
        
        Returns:
        - Immediate acknowledgment
        - Processing status
        """
        try:
            logger.info(f"Triggering audio processing for media {media_file_id}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/audio/process-interview-audio",
                    json={
                        "interview_id": interview_id,
                        "session_id": session_id,
                        "media_file_id": media_file_id
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"✅ Audio processing triggered: {result.get('status')}")
                
                return result
                
        except httpx.HTTPError as e:
            logger.error(f"❌ HTTP error triggering audio processing: {str(e)}")
            raise Exception(f"Failed to trigger audio processing: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error triggering audio processing: {str(e)}")
            raise
    
    async def get_audio_status(self, media_file_id: str) -> Dict[str, Any]:
        """
        Check audio processing status
        
        Returns:
        - Status: pending, processing, completed, failed
        - Error details if failed
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/audio/audio-status/{media_file_id}"
                )
                
                response.raise_for_status()
                result = response.json()
                
                return result
                
        except httpx.HTTPError as e:
            logger.error(f"❌ HTTP error getting audio status: {str(e)}")
            raise Exception(f"Failed to get audio status: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error getting audio status: {str(e)}")
            raise
    
    async def get_audio_analysis(
        self,
        interview_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Get audio analysis results
        
        Returns:
        - Transcript
        - Filler word analysis
        - Speaker analysis
        - Vocal analytics
        - Confidence scores
        """
        try:
            logger.info(f"Getting audio analysis for session {session_id}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Get from AI analysis table
                response = await client.get(
                    f"{self.base_url}/api/audio/analysis/{interview_id}/{session_id}"
                )
                
                if response.status_code == 404:
                    logger.warning(f"Audio analysis not found for session {session_id}")
                    return None
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"✅ Audio analysis retrieved")
                
                return result
                
        except httpx.HTTPError as e:
            logger.error(f"❌ HTTP error getting audio analysis: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"❌ Error getting audio analysis: {str(e)}")
            return None
    
    async def get_candidate_transcripts(self, candidate_id: str) -> Dict[str, Any]:
        """
        Get all transcripts for a candidate
        
        Returns:
        - All interview transcripts
        - Word-level timestamps
        - Transcription confidence
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/audio/candidate-transcripts/{candidate_id}"
                )
                
                response.raise_for_status()
                result = response.json()
                
                return result
                
        except httpx.HTTPError as e:
            logger.error(f"❌ HTTP error getting transcripts: {str(e)}")
            raise Exception(f"Failed to get transcripts: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error getting transcripts: {str(e)}")
            raise
    
    async def get_candidate_audio_analysis(self, candidate_id: str) -> Dict[str, Any]:
        """
        Get comprehensive audio analysis for candidate
        
        Returns:
        - Confidence scores
        - Communication quality
        - Filler analysis
        - Vocal analytics
        - Cheating detection
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/audio/candidate-audio-analysis/{candidate_id}"
                )
                
                response.raise_for_status()
                result = response.json()
                
                return result
                
        except httpx.HTTPError as e:
            logger.error(f"❌ HTTP error getting audio analysis: {str(e)}")
            raise Exception(f"Failed to get audio analysis: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error getting audio analysis: {str(e)}")
            raise

