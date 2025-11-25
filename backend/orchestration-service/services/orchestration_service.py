import asyncio
from config.logger import logger
from services.text_service_client import TextServiceClient
from services.audio_service_client import AudioServiceClient
from services.ai_services_client import AIServicesClient
from schemas.orchestration_schemas import NextQuestionResponse

class OrchestrationService:
    """Main orchestration logic"""
    
    def __init__(self):
        self.text_client = TextServiceClient()
        self.audio_client = AudioServiceClient()
        self.ai_client = AIServicesClient()
    
    async def process_next_question(
        self,
        interview_id: str,
        session_id: str,
        media_file_id: str,
        candidate_response: str
    ) -> NextQuestionResponse:
        """
        Main orchestration flow for "Next Question" button
        
        Steps:
        1. Call text-service (synchronous - WAIT)
        2. Call audio TTS (synchronous - WAIT)
        3. Return to frontend
        4. Fire-and-forget AI analysis (background)
        """
        
        logger.info(f"🚀 Starting orchestration for interview {interview_id}")
        
        try:
            # STEP 1: Call text-service (WAIT - synchronous)
            logger.info("📝 Step 1: Evaluating response + generating next question...")
            text_result = await self.text_client.evaluate_and_generate_next_question(
                interview_id=interview_id,
                session_id=session_id,
                candidate_response=candidate_response
            )
            
            next_question = text_result["next_question"]
            evaluation_score = text_result["evaluation_score"]
            feedback = text_result["feedback"]
            
            logger.info(f"✅ Next question generated: {next_question[:50]}...")
            
            # STEP 2: Call audio TTS (WAIT - synchronous)
            logger.info("🎵 Step 2: Generating TTS audio...")
            audio_result = await self.audio_client.generate_speech(
                text=next_question,
                session_id=session_id
            )
            
            audio_url = audio_result["download_url"]
            logger.info(f"✅ TTS audio generated: {audio_url}")
            
            # STEP 3: Fire-and-forget AI analysis (background)
            logger.info("🔥 Step 3: Triggering background AI analysis...")
            
            # Run both AI service calls concurrently (but don't wait)
            audio_ai_task = asyncio.create_task(
                self.ai_client.trigger_audio_analysis(interview_id, session_id, media_file_id)
            )
            video_ai_task = asyncio.create_task(
                self.ai_client.trigger_video_analysis(interview_id, session_id, media_file_id)
            )
            
            # Wait for AI triggers to complete (but only wait 5 seconds max)
            audio_ai_success, video_ai_success = await asyncio.gather(
                audio_ai_task,
                video_ai_task,
                return_exceptions=True
            )
            
            logger.info(f"🎯 Audio AI triggered: {audio_ai_success}")
            logger.info(f"🎯 Video AI triggered: {video_ai_success}")
            
            # STEP 4: Return response to frontend
            return NextQuestionResponse(
                status="success",
                next_question_text=next_question,
                audio_download_url=audio_url,
                evaluation_score=evaluation_score,
                feedback=feedback,
                audio_ai_triggered=bool(audio_ai_success),
                video_ai_triggered=bool(video_ai_success)
            )
        
        except Exception as e:
            logger.error(f"❌ Orchestration failed: {str(e)}")
            return NextQuestionResponse(
                status="error",
                next_question_text="",
                audio_download_url="",
                evaluation_score=None,
                feedback=None,
                audio_ai_triggered=False,
                video_ai_triggered=False,
                error=str(e)
            )