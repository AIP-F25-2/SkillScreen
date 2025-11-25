"""
Service Client - HTTP client for calling other microservices
"""

import httpx
import os
from typing import Dict, Any, Optional
from config import logger

# Service URLs from environment variables
SERVICE_URLS = {
    "text_service": os.getenv("TEXT_SERVICE_URL", "http://text-service:8080"),
    "audio_ai_service": os.getenv("AUDIO_AI_SERVICE_URL", "http://audio-ai-service:8080"),
    "video_ai_service": os.getenv("VIDEO_AI_SERVICE_URL", "http://video-ai-service:8080"),
    "media_service": os.getenv("MEDIA_SERVICE_URL", "http://media-service:8080"),
    "interview_service": os.getenv("INTERVIEW_SERVICE_URL", "http://interview-service:8080"),
    "assessment_service": os.getenv("ASSESSMENT_SERVICE_URL", "http://assessment-service:8080"),
}

class ServiceClient:
    """HTTP client for calling microservices"""
    
    def __init__(self):
        self.timeout = 300.0  # 5 minutes timeout for long operations
        self.client = httpx.AsyncClient(timeout=self.timeout)
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def _request(
        self,
        method: str,
        service_name: str,
        endpoint: str,
        data: Optional[Dict] = None,
        files: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to a microservice
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            service_name: Name of the service (key in SERVICE_URLS)
            endpoint: API endpoint path
            data: Request body data
            files: Files to upload (for multipart/form-data)
        
        Returns:
            Response data as dictionary
        """
        if service_name not in SERVICE_URLS:
            raise ValueError(f"Unknown service: {service_name}")
        
        url = f"{SERVICE_URLS[service_name]}{endpoint}"
        
        try:
            if files:
                # For file uploads (multipart/form-data)
                response = await self.client.request(
                    method,
                    url,
                    data=data,
                    files=files
                )
            else:
                # For JSON requests
                response = await self.client.request(
                    method,
                    url,
                    json=data
                )
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error calling {service_name}{endpoint}: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error calling {service_name}{endpoint}: {str(e)}")
            raise
    
    # ============================================
    # Text Service Methods
    # ============================================
    
    async def submit_response_and_get_next_question(
        self,
        session_id: str,
        response_text: str
    ) -> Dict[str, Any]:
        """Submit response to text-service and get next question"""
        return await self._request(
            "POST",
            "text_service",
            f"/api/interviews/{session_id}/respond",
            data={"response_text": response_text}
        )
    
    async def start_interview(
        self,
        candidate_id: str,
        job_id: str,
        interview_type: str = "standard"
    ) -> Dict[str, Any]:
        """Start interview and get first question"""
        return await self._request(
            "POST",
            "text_service",
            "/api/interviews/start",
            data={
                "candidate_id": candidate_id,
                "job_id": job_id,
                "interview_type": interview_type,
                "max_questions": 6
            }
        )
    
    # ============================================
    # TTS (Text-to-Speech) Methods
    # ============================================
    
    async def generate_tts(
        self,
        text: str,
        voice: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate speech from text using TTS service
        
        Returns:
            {
                "status": "success",
                "filename": "abc123.mp3",
                "download_url": "/api/tts/download/abc123.mp3",
                "text": "...",
                "voice": "..."
            }
        """
        return await self._request(
            "POST",
            "audio_ai_service",
            "/api/tts/generate",
            data={
                "text": text,
                "voice": voice or "en-US-AriaNeural",
                "session_id": session_id
            }
        )
    
    async def generate_tts_stream(
        self,
        text: str,
        voice: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> bytes:
        """
        Generate speech and return audio file directly (streaming)
        
        Returns:
            Audio file bytes (MP3)
        """
        url = f"{SERVICE_URLS['audio_ai_service']}/api/tts/generate-stream"
        
        response = await self.client.post(
            url,
            json={
                "text": text,
                "voice": voice or "en-US-AriaNeural",
                "session_id": session_id
            }
        )
        response.raise_for_status()
        return response.content
    
    # ============================================
    # Audio AI Service Methods
    # ============================================
    
    async def process_interview_audio(
        self,
        interview_id: str,
        session_id: str,
        media_file_id: str
    ) -> Dict[str, Any]:
        """
        Start audio analysis processing (async)
        
        Returns immediately with status "accepted"
        Processing happens in background
        """
        return await self._request(
            "POST",
            "audio_ai_service",
            "/api/audio/process-interview-audio",
            data={
                "interview_id": interview_id,
                "session_id": session_id,
                "media_file_id": media_file_id
            }
        )
    
    async def get_audio_processing_status(
        self,
        media_file_id: str
    ) -> Dict[str, Any]:
        """Check audio processing status"""
        return await self._request(
            "GET",
            "audio_ai_service",
            f"/api/audio/audio-status/{media_file_id}"
        )
    
    # ============================================
    # Media Service Methods
    # ============================================
    
    async def finalize_video_upload(
        self,
        user_id: str,
        session_id: str,
        candidate_id: str
    ) -> Dict[str, Any]:
        """Finalize video upload after all chunks are uploaded"""
        return await self._request(
            "POST",
            "media_service",
            "/finalize_upload",
            data={
                "user_id": user_id,
                "session_id": session_id,
                "candidate_id": candidate_id
            }
        )
    
    # ============================================
    # Video AI Service Methods
    # ============================================
    
    async def process_video_analysis(
        self,
        video_url: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Start video AI analysis (async)"""
        # TODO: Implement when video-ai-service endpoint is available
        # This is a placeholder
        return {
            "status": "accepted",
            "message": "Video analysis started",
            "session_id": session_id
        }
    
    # ============================================
    # Assessment Service Methods
    # ============================================
    
    async def get_assessment_results(
        self,
        interview_id: str
    ) -> Dict[str, Any]:
        """Get assessment results for an interview"""
        return await self._request(
            "GET",
            "assessment_service",
            f"/assessments/{interview_id}"
        )


# Global service client instance
service_client = ServiceClient()

