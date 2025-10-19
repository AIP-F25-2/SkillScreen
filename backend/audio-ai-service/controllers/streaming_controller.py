from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.streaming_transcriber import StreamingTranscriber
from config import logger
import json
import base64

router = APIRouter()

# Store active sessions
active_sessions = {}


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
            
            # Handle START command
            if msg_type == "start":
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
            
            # Handle AUDIO data
            elif msg_type == "audio":
                if not transcriber:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Session not started. Send 'start' command first."
                    })
                    continue
                
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
            
            # Handle STOP command
            elif msg_type == "stop":
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
                    
                    transcriber = None
                
                await websocket.send_json({
                    "type": "stopped",
                    "message": "Session stopped"
                })
            
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}"
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
        
        # Cleanup on disconnect
        if session_id and session_id in active_sessions:
            del active_sessions[session_id]
    
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass


@router.get("/status")
async def get_streaming_status():
    """Get current streaming status"""
    return {
        "active_sessions": len(active_sessions),
        "sessions": list(active_sessions.keys())
    }