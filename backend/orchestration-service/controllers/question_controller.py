from fastapi import APIRouter, HTTPException
from schemas.question_schemas import NextQuestionRequest, NextQuestionResponse
from services.text_service_client import TextServiceClient
from services.audio_service_client import AudioServiceClient
from services.media_service_client import MediaServiceClient
from services.interview_service_client import InterviewServiceClient
from config.logger import logger
import asyncio

router = APIRouter()
text_client = TextServiceClient()
audio_client = AudioServiceClient()
media_client = MediaServiceClient()
interview_client = InterviewServiceClient()


@router.post("/next", response_model=NextQuestionResponse)
async def get_next_question(request: NextQuestionRequest):
    """
    MAIN ORCHESTRATION - Handle "Next Question" button

    Complete Flow:
    1. Get live transcription from audio-ai (transcript of what candidate said)
    2. Submit transcript to text-service for evaluation
    3. Get next question from text-service (dynamically generated)
    4. Generate TTS for next question
    5. Fire-and-forget: Audio-AI + Video-AI analysis (async)
    6. Return: next question + audio + evaluation score
    """
    logger.info(f"📥 Processing response for session {request.session_id}")

    try:
        interview_id = str(request.interview_id)
        session_id = str(request.session_id)

        # STEP 1: Get live transcription from audio-ai
        logger.info("🎤 Step 1: Getting live transcription from audio-ai")
        try:
            transcription = await audio_client.get_live_transcription(session_id)
            transcript_text = transcription.get("transcript", request.candidate_response)
            logger.info(f"✅ Transcription retrieved: {transcript_text[:100]}...")
        except Exception as e:
            logger.warning(f"⚠️ Transcription failed, using provided response: {str(e)}")
            transcript_text = request.candidate_response

        # STEP 2: Submit response to text-service for evaluation
        logger.info("📝 Step 2: Submitting response to text-service for evaluation")
        evaluation_result = await text_client.submit_response(
            interview_id=interview_id,
            session_id=session_id,
            response_text=transcript_text
        )

        if not evaluation_result.get("success"):
            logger.error(f"❌ Response evaluation failed: {evaluation_result.get('error')}")
            raise HTTPException(status_code=400, detail=evaluation_result.get("error"))

        evaluation_data = evaluation_result.get("data", {}).get("evaluation", {})
        evaluation_score = evaluation_data.get("score", 0)
        feedback = evaluation_data.get("feedback", "")

        logger.info(f"✅ Response evaluated - Score: {evaluation_score}")

        # STEP 3: Check if interview is completed
        logger.info("📊 Step 3: Checking if interview is completed")
        interview_status = await interview_client.get_interview(interview_id)

        if interview_status.get("success"):
            current_status = interview_status.get("data", {}).get("status")
            if current_status == "completed":
                logger.info("✅ Interview completed")
                # Get final evaluation
                final_eval = await text_client.evaluate_interview(interview_id)
                return NextQuestionResponse(
                    status="completed",
                    summary=final_eval.get("data", {}),
                    evaluation_score=evaluation_score,
                    feedback=feedback
                )

        # STEP 4: Get next question (dynamically generated)
        logger.info("🎯 Step 4: Generating next question")

        # Get candidate_id and job_position_id from interview
        interview_details = interview_status.get("data", {})
        candidate_id = interview_details.get("candidate_id")
        job_position_id = interview_details.get("job_position_id")

        if not candidate_id or not job_position_id:
            raise HTTPException(
                status_code=400,
                detail="candidate_id and job_position_id required to generate next question"
            )

        next_question_result = await text_client.get_next_question(
            interview_id=interview_id,
            candidate_id=candidate_id,
            job_position_id=job_position_id
        )

        if not next_question_result.get("success"):
            logger.error(f"❌ Next question generation failed: {next_question_result.get('error')}")
            raise HTTPException(status_code=500, detail="Failed to generate next question")

        next_question_data = next_question_result.get("data", {})
        next_question_text = next_question_data.get("question_text", "")
        next_question_id = next_question_data.get("id", "")

        logger.info(f"✅ Next question generated: {next_question_text[:100]}...")

        # STEP 5: Generate TTS for next question
        logger.info("🎵 Step 5: Generating TTS for next question")
        audio_result = await audio_client.generate_speech(
            text=next_question_text,
            interview_id=interview_id
        )

        audio_url = None
        if audio_result.get("success"):
            audio_url = audio_result.get("data", {}).get("audio_url")
            logger.info(f"✅ TTS generated")
        else:
            logger.warning(f"⚠️ TTS generation failed: {audio_result.get('error')}")

        # STEP 6: Fire-and-forget - Trigger background analysis (async, don't wait)
        logger.info("🔥 Step 6: Triggering background AI analysis (async)")
        audio_ai_success = False
        video_ai_success = False

        try:
            # Get media_file_id from media service
            media_result = await media_client.finalize_upload(
                interview_id=interview_id,
                session_id=session_id
            )

            media_file_id = None
            for key in ["media_file_id", "db_id", "id"]:
                if key in media_result.get("data", {}):
                    media_file_id = media_result["data"][key]
                    break

            if media_file_id:
                logger.info(f"✅ Video finalized: {media_file_id}")

                # Create async tasks for background analysis (don't wait for completion)
                async def trigger_audio_analysis():
                    try:
                        await audio_client.analyze_audio(
                            interview_id=interview_id,
                            session_id=session_id,
                            media_file_id=str(media_file_id)
                        )
                        logger.info("✅ Audio analysis triggered")
                        return True
                    except Exception as e:
                        logger.warning(f"⚠️ Audio analysis trigger failed: {str(e)}")
                        return False

                async def trigger_video_analysis():
                    try:
                        # Get video URL and trigger analysis
                        await audio_client.analyze_video(
                            interview_id=interview_id,
                            session_id=session_id,
                            media_file_id=str(media_file_id)
                        )
                        logger.info("✅ Video analysis triggered")
                        return True
                    except Exception as e:
                        logger.warning(f"⚠️ Video analysis trigger failed: {str(e)}")
                        return False

                # Fire-and-forget: don't await, just create tasks
                asyncio.create_task(trigger_audio_analysis())
                asyncio.create_task(trigger_video_analysis())

        except Exception as e:
            logger.warning(f"⚠️ Media finalization/AI trigger failed (non-critical): {str(e)}")

        # STEP 7: Return response to candidate
        # NOTE: Do NOT send evaluation_score or feedback to candidate!
        # These are for recruiter/dashboard only
        logger.info("✅ Returning next question to candidate")
        return NextQuestionResponse(
            status="continue",
            next_question_text=next_question_text,
            next_question_id=next_question_id,
            audio_download_url=audio_url,
            evaluation_score=None,  # Hidden from candidate
            feedback=None,  # Hidden from candidate
            audio_ai_triggered=audio_ai_success,
            video_ai_triggered=video_ai_success
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Orchestration failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))