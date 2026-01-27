import asyncio
import websockets
import json
import sounddevice as sd
import numpy as np

async def test_speech_to_text():
    uri = "ws://localhost:8002/ws"
    
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket. Listening for audio...")
        print("Speak something and the text will be printed below:\n")
        
        sample_rate = 16000
        block_duration = 0.02
        block_size = int(sample_rate * block_duration)
        
        audio_queue = asyncio.Queue()
        
        def audio_callback(indata, frames, time_info, status):
            if status:
                print(f"Audio status: {status}")
            audio_queue.put_nowait(indata.copy())
        
        async def send_audio():
            while True:
                try:
                    audio_data = await asyncio.wait_for(audio_queue.get(), timeout=0.05)
                    await websocket.send(audio_data.tobytes())
                except asyncio.TimeoutError:
                    pass
        
        async def receive_messages():
            try:
                async for message in websocket:
                    data = json.loads(message)
                    
                    if data["type"] == "speech_start":
                        print("[Speech detected...]")
                    elif data["type"] == "live_transcript":
                        print(f"[Live] {data['text']}")
                    elif data["type"] == "transcript":
                        print(f"\n[Final] {data['text']}\n")
                    elif data["type"] == "speech_end":
                        print("[Speech ended]\n")
            except websockets.exceptions.ConnectionClosed:
                print("WebSocket connection closed")
        
        with sd.InputStream(
            samplerate=sample_rate,
            channels=1,
            dtype=np.int16,
            blocksize=block_size,
            callback=audio_callback
        ):
            try:
                await asyncio.gather(
                    send_audio(),
                    receive_messages()
                )
            except KeyboardInterrupt:
                print("\nTest stopped")

if __name__ == "__main__":
    asyncio.run(test_speech_to_text())
