from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.streaming_transcriber import StreamingTranscriber
from config import logger
import json
import base64

router = APIRouter()

# Store active sessions
active_sessions = {}


async def _handle_start_message(websocket: WebSocket, data: dict):
    """Handle the 'start' message type"""
    session_id = data.get("session_id", f"session_{id(websocket)}")
    model = data.get("model", "base")

    logger.info(f"Starting streaming session: {session_id}")

    # Create transcriber
    transcriber = StreamingTranscriber(model_size=model)
    active_sessions[session_id] = transcriber

    await websocket.send_json({
        "type": "started",
        "session_id": session_id,
        "message": "Session started"
    })

    return session_id, transcriber


async def _handle_audio_message(websocket: WebSocket, transcriber, data: dict):
    """Handle the 'audio' message type"""
    if not transcriber:
        await websocket.send_json({
            "type": "error",
            "message": "Session not started. Send 'start' command first."
        })
        return

    try:
        # Decode audio
        audio_data = data.get("data", "")
        audio_bytes = base64.b64decode(audio_data)

        # Process chunk
        result = await transcriber.process_chunk(audio_bytes)

        # Send result
        await websocket.send_json({
            "type": "transcription",
            "text": result["text"],
            "is_final": result["is_final"]
        })

    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "message": f"Audio processing error: {str(e)}"
        })


async def _handle_stop_message(websocket: WebSocket, session_id: str, transcriber):
    """Handle the 'stop' message type"""
    if transcriber:
        logger.info(f"Stopping streaming session: {session_id}")

        # Finalize session
        final_result = await transcriber.finalize()

        # Send final result
        await websocket.send_json({
            "type": "final",
            "full_transcript": final_result["full_transcript"]
        })

        # Cleanup
        if session_id in active_sessions:
            del active_sessions[session_id]

    await websocket.send_json({
        "type": "stopped",
        "message": "Session stopped"
    })

    return None  # Return None to clear transcriber


async def _handle_unknown_message(websocket: WebSocket, msg_type: str):
    """Handle unknown message types"""
    await websocket.send_json({
        "type": "error",
        "message": f"Unknown message type: {msg_type}"
    })


@router.websocket("/ws/stream-transcribe")
async def websocket_stream_transcribe(websocket: WebSocket):
    """
    WebSocket endpoint for real-time audio transcription

    Client sends:
    {
        "type": "start",
        "session_id": "optional-session-id",
        "model": "base"
    }
    {
        "type": "audio",
        "data": "<base64-encoded-audio>"
    }
    {
        "type": "stop"
    }

    Server sends:
    {
        "type": "transcription",
        "text": "Hello world",
        "is_final": false
    }
    {
        "type": "final",
        "full_transcript": "Complete text..."
    }
    """

    session_id = None
    transcriber = None

    try:
        # Accept connection
        await websocket.accept()
        logger.info("WebSocket connection established")

        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "message": "WebSocket connected"
        })

        while True:
            # Receive message
            message = await websocket.receive_text()
            data = json.loads(message)

            msg_type = data.get("type")

            # Dispatch to appropriate handler
            if msg_type == "start":
                session_id, transcriber = await _handle_start_message(websocket, data)
            elif msg_type == "audio":
                await _handle_audio_message(websocket, transcriber, data)
            elif msg_type == "stop":
                transcriber = await _handle_stop_message(websocket, session_id, transcriber)
            else:
                await _handle_unknown_message(websocket, msg_type)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
        if session_id and session_id in active_sessions:
            del active_sessions[session_id]

    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except (WebSocketDisconnect, RuntimeError):
            # WebSocket already closed, cannot send error message
            pass


@router.get("/status")
async def get_streaming_status():
    """Get current streaming status"""
    return {
        "active_sessions": len(active_sessions),
        "sessions": list(active_sessions.keys())
    }