from fastapi import FastAPI,WebSocket,WebSocketDisconnect
from dotenv import load_dotenv
from app.audio_buffer import AudioBuffer
from app.noise_suppressor import NoiseSuppressor
from app.vad import VAD
import numpy as np
import asyncio

load_dotenv()

app = FastAPI()


@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection accepted")
    audio_buffer = AudioBuffer(frame_size=320)
    noise_suppressor = NoiseSuppressor()
    vad = VAD()

    try:
        while True:
            try:
                audio_bytes = await asyncio.wait_for(
                    websocket.receive_bytes(),
                    timeout=5.0 
                )
            except asyncio.TimeoutError:
                await websocket.send_bytes(b"\x00")
                continue
            samples = np.frombuffer(audio_bytes, dtype=np.int16)
            audio_buffer.add_samples(samples)
            while audio_buffer.has_frame():
                frame = audio_buffer.get_frame()
                if len(frame) < 320:
                    continue
                clean_frame = noise_suppressor.process(frame)
                vad_event = vad.process(clean_frame)
                if vad_event == "speech_start":
                    await websocket.send_bytes(clean_frame.tobytes())
                    print(" Speech started")

                elif vad_event == "speech":
                    await websocket.send_bytes(clean_frame.tobytes())

                elif vad_event == "speech_end":
                    print(f"Speech ended after {vad.silence_frames} silent frames")

                elif vad_event == "silence":
                    pass

    except WebSocketDisconnect:
        print("WebSocket connection closed")