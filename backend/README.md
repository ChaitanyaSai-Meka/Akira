# Real-time Speech-to-Text with LLM Processing

FastAPI WebSocket server for real-time speech recognition using Groq Whisper API, with Llama LLM processing of transcribed text.

## Pipeline

```text
Audio Input → Noise Suppression → VAD Detection → Transcription (Whisper)
                                                        ↓
                                                LLM Processing (Llama)
                                                        ↓
                                                WebSocket Response
```

## Setup

1. Install dependencies:
```bash
cd backend
uv sync
```

2. Add Groq API keys to `.env`:
```bash
GROQ_API_KEY=your_groq_whisper_api_key_here
GROQ_LLM_API_KEY=your_groq_llm_api_key_here
```

3. Run server (Terminal 1):
```bash
cd backend
uv run python main.py
```

Server runs on `ws://localhost:8002/ws`

## Testing

Run in a separate terminal (Terminal 2):

```bash
cd backend
RUN_MANUAL_TESTS=1 uv run python test/test_stt_client.py
```

Speak into your microphone and see:
1. Live transcription every 4 seconds
2. Final transcription when speech ends
3. LLM response to the transcribed text

## WebSocket Endpoint

- `/ws` - Audio streaming, transcription, and LLM processing

## WebSocket Messages

**From Server:**
- `{"type": "speech_start"}` - Speech detected
- `{"type": "live_transcript", "text": "..."}` - Interim result (every 4 seconds)
- `{"type": "transcript", "text": "..."}` - Final transcription
- `{"type": "llm_response", "text": "..."}` - LLM processing result
- `{"type": "speech_end"}` - Speech boundary ended
- `{"type": "heartbeat"}` - Connection keep-alive

**From Client:**
- Binary PCM audio frames (16-bit, 16 kHz, mono)

## Models Used

- **Speech-to-Text**: Groq Whisper (whisper-large-v3) - Fast and accurate
- **LLM**: Groq Llama 3.1 8B - Cost-efficient and ultra-fast

## Configuration

Edit `backend/app/config.py` to adjust:
- `TRANSCRIBER_STREAM_INTERVAL` - Live update frequency (default: 4.0 seconds)
- `VAD_ENERGY_RATIO` - Speech sensitivity (lower = more sensitive)
- `VAD_MIN_SILENCE_FRAMES` - Silence needed to end speech
