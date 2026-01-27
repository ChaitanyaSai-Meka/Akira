from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from app.config import get_config
from app.audio_buffer import AudioBuffer
from app.noise_suppressor import NoiseSuppressor
from app.vad import VAD
from app.speech_transcriber import SpeechTranscriber
from app.llm_processor import LLMProcessor
from dotenv import load_dotenv
import numpy as np
import asyncio
import json
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = get_config()
app = FastAPI()


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connected")

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
    llm = LLMProcessor()
    
    is_ai_speaking = False
    last_live_transcript = None

    try:
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive(),
                    timeout=config.WEBSOCKET_TIMEOUT
                )
                
                if data.get("type") == "websocket.receive":
                    if "text" in data:
                        message = json.loads(data["text"])
                        
                        if message.get("type") == "tts_finished":
                            is_ai_speaking = False
                            logger.info("AI finished speaking")
                            
                    elif "bytes" in data:
                        if is_ai_speaking:
                            continue
                            
                        audio_bytes = data["bytes"]
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
                                last_live_transcript = None
                                await websocket.send_text(json.dumps({"type": "speech_start"}))
                                logger.info("Speech started")

                            elif vad_event == "speech":
                                transcriber.add_frame(clean_frame)

                                if transcriber.should_transcribe():
                                    transcript = transcriber.transcribe(clear_buffer=False)
                                    if transcript:
                                        normalized = " ".join(transcript.split()).lower()
                                        if normalized != last_live_transcript:
                                            last_live_transcript = normalized
                                            logger.info(f"Live: {transcript}")
                                            await websocket.send_text(json.dumps({
                                                "type": "live_transcript",
                                                "text": transcript
                                            }))

                            elif vad_event == "speech_end":
                                logger.info("Speech ended")
                                transcript = transcriber.transcribe(clear_buffer=True)
                                if transcript:
                                    logger.info(f"Final: {transcript}")
                                    await websocket.send_text(json.dumps({
                                        "type": "transcript",
                                        "text": transcript
                                    }))

                                    llm_response = await asyncio.to_thread(llm.process, transcript)
                                    if llm_response:
                                        logger.info(f"LLM: {llm_response}")
                                        
                                        is_ai_speaking = True
                                        
                                        await websocket.send_text(json.dumps({
                                            "type": "llm_response",
                                            "text": llm_response
                                        }))

                                await websocket.send_text(json.dumps({"type": "speech_end"}))
                                last_live_transcript = None
                    
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({"type": "heartbeat"}))
                continue

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
