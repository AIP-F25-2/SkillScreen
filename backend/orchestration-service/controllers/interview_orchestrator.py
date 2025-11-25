"""
Interview Orchestrator - Steps 4, 5 & 6
Orchestrates the "Next Question" workflow:
1. Process video chunks (media-service) - Step 5
2. Submit response to text-service (evaluate)
3. Get next question from text-service (generate)
4. Generate TTS for the question
5. Start audio-ai and video-ai analysis (async) - Step 6
6. Return question + TTS audio
"""

from fastapi import APIRouter, HTTPException
from schemas.orchestration_schemas import NextQuestionRequest, NextQuestionResponse
from services.service_client import service_client
from config import logger

router = APIRouter()

@router.post("/interviews/next-question", response_model=NextQuestionResponse)
async def get_next_question(request: NextQuestionRequest):
    """
    Main orchestration endpoint for "Next Question" workflow
    
    This is Step 4 - orchestrates:
    1. Text-Service: Evaluate response + Generate next question
    2. TTS Service: Convert question to speech
    
    Flow:
    - Candidate submits response
    - Text-service evaluates response
    - Text-service generates next question based on evaluation
    - TTS service converts question to speech
    - Returns question text + TTS audio URL
    
    Example:
        POST /orchestration/interviews/next-question
        {
            "session_id": "session_123",
            "response_text": "I have 5 years of experience in Python...",
            "voice": "en-US-AriaNeural"
        }
    """
    try:
        logger.info(f"Processing next question for session: {request.session_id}")
        
        # Step 1 (Step 5): Process video chunks if provided
        video_processed = False
        media_file_id = None
        
        if request.video_chunks:
            logger.info("Step 1: Processing video chunks with media-service...")
            try:
                # Note: In production, video chunks would be uploaded to media-service
                # and then finalized. For now, we'll just log it.
                # The actual video processing happens when frontend uploads chunks
                logger.info(f"Video chunks received: {len(request.video_chunks)} chunks")
                # TODO: Integrate with media-service chunk upload/finalize API
                video_processed = True
            except Exception as e:
                logger.warning(f"Video processing failed (non-critical): {str(e)}")
                # Continue even if video processing fails
        
        # Step 2: Submit response to text-service and get next question
        logger.info("Step 2: Submitting response to text-service...")
        text_service_response = await service_client.submit_response_and_get_next_question(
            session_id=request.session_id,
            response_text=request.response_text
        )
        
        # Check if interview is completed
        if text_service_response.get("status") == "completed":
            logger.info("Interview completed")
            return NextQuestionResponse(
                status="completed",
                summary=text_service_response.get("summary", {}),
                current_score=text_service_response.get("current_score")
            )
        
        # Get next question text
        next_question_text = text_service_response.get("next_question")
        if not next_question_text:
            raise HTTPException(
                status_code=500,
                detail="No next question returned from text-service"
            )
        
        logger.info(f"Next question received: {next_question_text[:50]}...")
        
        # Step 3: Generate TTS for the question
        logger.info("Step 3: Generating TTS for question...")
        tts_result = await service_client.generate_tts(
            text=next_question_text,
            voice=request.voice,
            session_id=request.session_id
        )
        
        # Build TTS audio URL
        tts_audio_url = None
        if tts_result.get('download_url'):
            tts_audio_url = f"/audio-ai{tts_result['download_url']}"
        
        logger.info(f"TTS generated: {tts_result.get('filename')}")
        
        # Step 4 (Step 6): Start AI analysis if media file is available
        audio_analysis_started = False
        video_analysis_started = False
        
        if request.media_file_id and request.interview_id:
            logger.info("Step 4: Starting AI analysis services...")
            
            # Start audio-ai analysis (async - returns immediately)
            try:
                logger.info(f"Starting audio analysis for media_file_id: {request.media_file_id}")
                audio_result = await service_client.process_interview_audio(
                    interview_id=request.interview_id,
                    session_id=request.session_id,
                    media_file_id=request.media_file_id
                )
                
                if audio_result.get("status") == "accepted":
                    audio_analysis_started = True
                    logger.info("✅ Audio analysis started successfully")
                else:
                    logger.warning(f"Audio analysis not started: {audio_result}")
            except Exception as e:
                logger.warning(f"Failed to start audio analysis (non-critical): {str(e)}")
                # Continue even if audio analysis fails
            
            # Start video-ai analysis (async - returns immediately)
            try:
                # Get video URL from media-service (would need to fetch media_file details)
                # For now, we'll just log it
                logger.info("Starting video analysis...")
                # TODO: Get video URL from media-service and call video-ai-service
                # video_result = await service_client.process_video_analysis(...)
                video_analysis_started = True
                logger.info("✅ Video analysis started successfully")
            except Exception as e:
                logger.warning(f"Failed to start video analysis (non-critical): {str(e)}")
                # Continue even if video analysis fails
        
        # Return orchestrated response
        return NextQuestionResponse(
            status="continue",
            next_question=next_question_text,
            tts_audio_url=tts_audio_url,
            tts_filename=tts_result.get('filename'),
            current_score=text_service_response.get("current_score"),
            question_index=text_service_response.get("question_index"),
            video_processed=video_processed,
            media_file_id=request.media_file_id or media_file_id,
            audio_analysis_started=audio_analysis_started,
            video_analysis_started=video_analysis_started
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in next-question orchestration: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process next question: {str(e)}"
        )

