# Real-time Speech-to-Text Backend

FastAPI WebSocket server for real-time speech recognition using Groq Whisper API.

## Setup

1. Install dependencies:
```bash
cd backend
uv sync
```

2. Add Groq API key to `.env`:
```bash
GROQ_API_KEY=your_groq_api_key_here
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

Speak into your microphone and see live transcription every 4 seconds, with final result when you stop speaking.

## WebSocket Endpoint

- `/ws` - Audio streaming and transcription

## WebSocket Messages

**From Server:**
- `{"type": "speech_start"}` - Speech detected
- `{"type": "live_transcript", "text": "..."}` - Interim result (every 4 seconds)
- `{"type": "transcript", "text": "..."}` - Final transcription
- `{"type": "speech_end"}` - Speech boundary ended
- `{"type": "heartbeat"}` - Connection keep-alive

**From Client:**
- Binary PCM audio frames (16-bit, 16kHz, mono)

## Configuration

Edit `backend/app/config.py` to adjust:
- `TRANSCRIBER_STREAM_INTERVAL` - Live update frequency (default: 4.0 seconds)
- `VAD_ENERGY_RATIO` - Speech sensitivity (lower = more sensitive)
- `VAD_MIN_SILENCE_FRAMES` - Silence needed to end speech
