from fastapi import FastAPI,WebSocket,WebSocketDisconnect
from dotenv import load_dotenv
from app.audio_buffer import AudioBuffer
from app.noise_suppressor import NoiseSuppressor
import numpy as np

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
    noise_suppressor = NoiseSuppressor(sample_rate=16000)

    try:
        while True:
            audio_bytes = await websocket.receive_bytes()
            samples = np.frombuffer(audio_bytes, dtype=np.int16)
            audio_buffer.add_samples(samples)
            while audio_buffer.has_frame():
                frame = audio_buffer.get_frame()
                clean_frame, is_speech = noise_suppressor.process(frame)
                print("Frame RMS:",np.sqrt(np.mean(clean_frame ** 2)),"Speech:",is_speech)
    except WebSocketDisconnect:
        print("WebSocket connection closed")