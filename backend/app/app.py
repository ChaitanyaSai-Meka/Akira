from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from app.config import get_config
from app.audio_buffer import AudioBuffer
from app.noise_suppressor import NoiseSuppressor
from app.vad import VAD
from app.speech_transcriber import SpeechTranscriber
from app.llm_processor import LLMProcessor
from app.tts_processor import TTSProcessor
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


async def safe_send_text(websocket: WebSocket, message: dict) -> bool:
    try:
        await websocket.send_text(json.dumps(message))
        return True
    except (WebSocketDisconnect, RuntimeError) as e:
        logger.debug(f"Cannot send text, client disconnected: {e}")
        return False

async def safe_send_bytes(websocket: WebSocket, data: bytes) -> bool:
    try:
        await websocket.send_bytes(data)
        return True
    except (WebSocketDisconnect, RuntimeError) as e:
        logger.debug(f"Cannot send bytes, client disconnected: {e}")
        return False

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connected")

    audio_buffer = AudioBuffer(frame_size=config.FRAME_SIZE)
    noise_suppressor = NoiseSuppressor()
    vad = VAD(
        aggressiveness=config.VAD_AGGRESSIVENESS,
        min_speech_frames=config.VAD_MIN_SPEECH_FRAMES,
        min_silence_frames=config.VAD_MIN_SILENCE_FRAMES,
    )
    transcriber = SpeechTranscriber(
        sample_rate=config.SAMPLE_RATE,
        stream_interval=config.TRANSCRIBER_STREAM_INTERVAL
    )
    llm = LLMProcessor()
    tts = TTSProcessor()
    
    is_ai_speaking = False
    last_live_transcript = None

    try:
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive(),
                    timeout=config.WEBSOCKET_TIMEOUT
                )
                
                if data.get("type") == "websocket.disconnect":
                    break
                
                if data.get("type") == "websocket.receive":
                    if "text" in data:
                        try:
                            message = json.loads(data["text"])
                        except (json.JSONDecodeError, ValueError) as e:
                            logger.warning(f"Malformed JSON payload: {data['text'][:100]}, error: {e}")
                            continue
                        
                        if not isinstance(message, dict):
                            logger.warning(f"Parsed message is not a dict: {type(message).__name__}, value: {str(message)[:100]}")
                            continue
                        
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
                                await safe_send_text(websocket, {"type": "speech_start"})
                                logger.info("Speech started")

                            elif vad_event == "speech":
                                transcriber.add_frame(clean_frame)

                                if transcriber.should_transcribe():
                                    transcript = transcriber.transcribe(clear_buffer=False)
                                    if transcript:
                                        normalized = " ".join(transcript.split()).lower()
                                        if normalized != last_live_transcript:
                                            last_live_transcript = normalized
                                            logger.debug(f"Live: {transcript}")
                                            logger.info(f"Live transcript received (length: {len(transcript)})")
                                            await safe_send_text(websocket, {
                                                "type": "live_transcript",
                                                "text": transcript
                                            })

                            elif vad_event == "speech_end":
                                logger.info("Speech ended")
                                transcript = transcriber.transcribe(clear_buffer=True)
                                if transcript:
                                    logger.debug(f"Final: {transcript}")
                                    logger.info(f"Final transcript received (length: {len(transcript)})")
                                    if not await safe_send_text(websocket, {
                                        "type": "transcript",
                                        "text": transcript
                                    }):
                                        break

                                    llm_response = await asyncio.to_thread(llm.process, transcript)
                                    if llm_response:
                                        logger.debug(f"LLM: {llm_response}")
                                        logger.info(f"LLM response generated (length: {len(llm_response)})")
                                        
                                        if not await safe_send_text(websocket, {
                                            "type": "llm_response",
                                            "text": llm_response
                                        }):
                                            break
                                        
                                        if tts.is_available():
                                            is_ai_speaking = True
                                            try:
                                                audio_data = await asyncio.to_thread(tts.text_to_audio, llm_response)
                                                if audio_data:
                                                    if await safe_send_bytes(websocket, audio_data):
                                                        logger.info("Sent TTS audio to client")
                                                    else:
                                                        is_ai_speaking = False
                                                        break
                                                else:
                                                    logger.warning("TTS returned no audio data")
                                                    is_ai_speaking = False
                                                    await safe_send_text(websocket, {"type": "tts_finished"})
                                            except WebSocketDisconnect:
                                                logger.info("Client disconnected during TTS")
                                                is_ai_speaking = False
                                                break
                                            except Exception as e:
                                                logger.error(f"TTS error: {e}", exc_info=True)
                                                is_ai_speaking = False
                                                await safe_send_text(websocket, {"type": "tts_finished"})
                                        else:
                                            await safe_send_text(websocket, {"type": "tts_finished"})

                                await safe_send_text(websocket, {"type": "speech_end"})
                                last_live_transcript = None
                    
            except asyncio.TimeoutError:
                await safe_send_text(websocket, {"type": "heartbeat"})
                continue

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
