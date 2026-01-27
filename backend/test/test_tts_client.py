import asyncio
import websockets
import json
import base64
import wave
import io
from datetime import datetime

SAMPLE_RATE = 16000
CHUNK_SIZE = 320

async def tts_demo():
    uri = "ws://localhost:8000/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to server")
            print("TTS Demo: Listening for LLM responses...")
            
            audio_count = 0
            
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    msg_type = data.get("type")
                    
                    if msg_type == "tts_start":
                        duration = data.get("duration", 0)
                        print(f"\nTTS started (duration: {duration:.2f}s)")
                        print("Microphone input disabled during playback")
                        
                    elif msg_type == "tts_audio":
                        audio_b64 = data.get("audio")
                        if audio_b64:
                            audio_bytes = base64.b64decode(audio_b64)
                            audio_count += 1
                            
                            filename = f"tts_output_{audio_count}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
                            with open(filename, 'wb') as f:
                                f.write(audio_bytes)
                            
                            print(f"Saved TTS audio to: {filename}")
                            
                            await websocket.send(json.dumps({"type": "tts_finished"}))
                            print("Sent tts_finished, microphone re-enabled\n")
                            
                    elif msg_type == "llm_response":
                        text = data.get("text", "")
                        print(f"LLM Response: {text}")
                        
                    elif msg_type == "transcript":
                        text = data.get("text", "")
                        print(f"Transcript: {text}")
                        
                except json.JSONDecodeError:
                    continue
                    
    except KeyboardInterrupt:
        print("\nDisconnecting...")

if __name__ == "__main__":
    asyncio.run(tts_demo())

