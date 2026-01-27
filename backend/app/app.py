from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from app.config import get_config
from app.audio_buffer import AudioBuffer
from app.noise_suppressor import NoiseSuppressor
from app.vad import VAD
from app.speech_transcriber import SpeechTranscriber
import numpy as np
import asyncio
import json

config = get_config()

app = FastAPI()


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection accepted")

    audio_buffer = AudioBuffer(frame_size=config.FRAME_SIZE)
    noise_suppressor = NoiseSuppressor()
    vad = VAD(
        energy_ratio=config.VAD_ENERGY_RATIO,
        min_speech_frames=config.VAD_MIN_SPEECH_FRAMES,
        min_silence_frames=config.VAD_MIN_SILENCE_FRAMES,
    )
    transcriber = SpeechTranscriber(
        sample_rate=config.SAMPLE_RATE,
        stream_interval=config.TRANSCRIBER_STREAM_INTERVAL
    )

    try:
        while True:
            try:
                audio_bytes = await asyncio.wait_for(
                    websocket.receive_bytes(),
                    timeout=config.WEBSOCKET_TIMEOUT
                )
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({"type": "heartbeat"}))
                continue

            samples = np.frombuffer(audio_bytes, dtype=np.int16)
            audio_buffer.add_samples(samples)

            while audio_buffer.has_frame():
                frame = audio_buffer.get_frame()
                if len(frame) < config.FRAME_SIZE:
                    continue

                clean_frame = noise_suppressor.process(frame)
                vad_event = vad.process(clean_frame)

                if vad_event == "speech_start":
                    transcriber.clear()
                    transcriber.add_frame(clean_frame)
                    await websocket.send_text(json.dumps({"type": "speech_start"}))
                    print("Speech started")

                elif vad_event == "speech":
                    transcriber.add_frame(clean_frame)

                    if transcriber.should_transcribe():
                        transcript = transcriber.transcribe(clear_buffer=False)
                        if transcript:
                            print(f"Live: {transcript}")
                            await websocket.send_text(json.dumps({
                                "type": "live_transcript",
                                "text": transcript
                            }))

                elif vad_event == "speech_end":
                    print(f"Speech ended after {vad.silence_frames} silent frames")
                    transcript = transcriber.transcribe(clear_buffer=True)
                    if transcript:
                        print(f"Final: {transcript}")
                        await websocket.send_text(json.dumps({
                            "type": "transcript",
                            "text": transcript
                        }))
                    await websocket.send_text(json.dumps({"type": "speech_end"}))

    except WebSocketDisconnect:
        print("WebSocket connection closed")
