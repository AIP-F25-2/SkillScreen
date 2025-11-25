from fastapi import APIRouter, HTTPException
from schemas.question_schemas import NextQuestionRequest, NextQuestionResponse
from services.text_service_client import TextServiceClient
from services.audio_service_client import AudioServiceClient
from services.media_service_client import MediaServiceClient
from services.ai_services_client import AIServicesClient
from config.logger import logger
import asyncio

router = APIRouter()
text_client = TextServiceClient()
audio_client = AudioServiceClient()
media_client = MediaServiceClient()
ai_client = AIServicesClient()

@router.post("/next", response_model=NextQuestionResponse)
async def get_next_question(request: NextQuestionRequest):
    """
    MAIN ORCHESTRATION - Handle "Next Question" button
    
    Flow:
    1. Text Service: evaluate + generate next question
    2. Audio-AI TTS: generate speech
    3. Media Service: finalize video upload → get media_file_id
    4. Fire-and-forget: Audio-AI + Video-AI analysis
    5. Return: next question + audio
    """
    logger.info(f"📥 Next question for session {request.session_id}")
    
    try:
        # STEP 1: Text Service - evaluate + next question
        logger.info("📝 Step 1: Calling text-service")
        text_result = await text_client.evaluate_and_generate_next_question(
            session_id=str(request.session_id),
            question_id=request.question_id,
            candidate_response=request.candidate_response,
            response_time_seconds=request.response_time_seconds
        )
        
        # Check if completed
        if text_result["status"] == "completed":
            logger.info("✅ Interview completed")
            return NextQuestionResponse(
                status="completed",
                summary=text_result["summary"]
            )
        
        next_question = text_result["next_question"]
        next_question_id = text_result["next_question_id"]
        evaluation_score = text_result["evaluation_score"]
        
        # STEP 2: Audio TTS
        logger.info("🎵 Step 2: Generating TTS")
        audio_result = await audio_client.generate_speech(
            text=next_question,
            session_id=str(request.session_id)
        )
        
        # STEP 3: Media Service - finalize upload
        logger.info("📹 Step 3: Finalizing video")
        audio_ai_success = False
        video_ai_success = False
        
        try:
            media_result = await media_client.finalize_upload(
                interview_id=str(request.interview_id),
                session_id=str(request.session_id)
            )
            
            # Extract media_file_id (check different possible field names)
            media_file_id = None
            for key in ["media_file_id", "db_id", "id"]:
                if key in media_result:
                    media_file_id = str(media_result[key])
                    break
            
            if media_file_id:
                logger.info(f"✅ Video finalized: {media_file_id}")
                
                # STEP 4: Fire-and-forget AI analysis
                logger.info("🔥 Step 4: Triggering AI analysis")
                
                audio_ai_task = asyncio.create_task(
                    ai_client.trigger_audio_analysis(
                        str(request.interview_id),
                        str(request.session_id),
                        media_file_id
                    )
                )
                video_ai_task = asyncio.create_task(
                    ai_client.trigger_video_analysis(
                        str(request.interview_id),
                        str(request.session_id),
                        media_file_id
                    )
                )
                
                audio_ai_success, video_ai_success = await asyncio.gather(
                    audio_ai_task,
                    video_ai_task,
                    return_exceptions=True
                )
                
                logger.info(f"🎯 AI triggered: audio={audio_ai_success}, video={video_ai_success}")
        
        except Exception as e:
            logger.warning(f"⚠️ Media/AI step failed: {str(e)}")
        
        # STEP 5: Return response
        return NextQuestionResponse(
            status="continue",
            next_question_text=next_question,
            next_question_id=next_question_id,
            audio_download_url=audio_result["download_url"],
            evaluation_score=evaluation_score,
            feedback=text_result.get("feedback"),
            audio_ai_triggered=bool(audio_ai_success),
            video_ai_triggered=bool(video_ai_success)
        )
    
    except Exception as e:
        logger.error(f"❌ Orchestration failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))