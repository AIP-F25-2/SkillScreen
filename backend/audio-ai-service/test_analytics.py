"""
Test script for streaming WebSocket API
Run this to verify the streaming endpoint works
"""

import asyncio
import websockets
import json
import base64
import numpy as np

async def test_streaming():
    uri = "ws://localhost:8000/api/stream/ws/stream-transcribe"
    
    print("Connecting to WebSocket...")
    
    async with websockets.connect(uri) as websocket:
        # Wait for connection message
        msg = await websocket.recv()
        print(f"✅ Connected: {msg}")
        
        # Start session
        print("\n📤 Sending START command...")
        await websocket.send(json.dumps({
            "type": "start",
            "session_id": "test_session_123",
            "model": "base"
        }))
        
        msg = await websocket.recv()
        print(f"✅ Session started: {msg}")
        
        # Send dummy audio chunks (3 chunks of silence)
        print("\n📤 Sending audio chunks...")
        for i in range(3):
            # Generate 1 second of silence (16kHz, 16-bit PCM)
            dummy_audio = np.zeros(16000, dtype=np.int16)
            
            # Convert to bytes and encode to base64
            audio_bytes = dummy_audio.tobytes()
            encoded = base64.b64encode(audio_bytes).decode('utf-8')
            
            await websocket.send(json.dumps({
                "type": "audio",
                "data": encoded
            }))
            
            print(f"  Sent chunk {i+1}/3")
            
            # Receive transcription
            msg = await websocket.recv()
            data = json.loads(msg)
            print(f"  ✅ Received: {data}")
            
            await asyncio.sleep(0.5)
        
        # Stop session
        print("\n📤 Sending STOP command...")
        await websocket.send(json.dumps({
            "type": "stop"
        }))
        
        msg = await websocket.recv()
        print(f"✅ Final result: {msg}")
        
        print("\n🎉 Test completed successfully!")

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Testing Streaming WebSocket API")
    print("=" * 60)
    
    try:
        asyncio.run(test_streaming())
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        print("\nMake sure:")
        print("  1. Docker container is running")
        print("  2. Service is accessible at localhost:8000")