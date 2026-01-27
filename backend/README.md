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

3. Run server:
```bash
uv run python main.py
```

Server runs on `http://localhost:8002`

## Testing

```bash
uv run python test/test_stt_client.py
```

## WebSocket Endpoint

- `/ws` - Audio streaming and transcription

## Messages

**From Server:**
- `{"type": "speech_start"}` - Speech detected
- `{"type": "live_transcript", "text": "..."}` - Interim result
- `{"type": "transcript", "text": "..."}` - Final result
- `{"type": "speech_end"}` - Speech ended
