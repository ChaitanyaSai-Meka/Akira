from fastapi import FastAPI,WebSocket,WebSocketDisconnect
from dotenv import load_dotenv
from app.audio_buffer import AudioBuffer
from app.noise_suppressor import NoiseSuppressor
from app.vad import VAD
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
    vad = VAD()

    try:
        while True:
            audio_bytes = await websocket.receive_bytes()
            samples = np.frombuffer(audio_bytes, dtype=np.int16)
            audio_buffer.add_samples(samples)
            while audio_buffer.has_frame():
                frame = audio_buffer.get_frame()
                clean_frame, is_speech = noise_suppressor.process(frame)
                vad_event = vad.process(clean_frame)
                if vad_event == "speech_start":
                    print(" Speech started")

                elif vad_event == "speech":
                    print(" Speaking")

                elif vad_event == "speech_end":
                    print(" Speech ended")
    except WebSocketDisconnect:
        print("WebSocket connection closed")