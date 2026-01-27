# Real-time Speech-to-Text Backend

A production-ready FastAPI backend for real-time speech recognition with Voice Activity Detection (VAD) and noise suppression.

## Features

- Real-time audio streaming via WebSocket
- Voice Activity Detection (VAD) for automatic speech boundaries
- Noise suppression for cleaner audio
- Live transcription updates every 2 seconds during speech
- Final transcription when speech ends
- Google Cloud Speech API integration

## Architecture

```
WebSocket Audio Stream
    ↓
Audio Buffer (320-sample frames)
    ↓
Noise Suppressor
    ↓
Voice Activity Detector (VAD)
    ↓
Speech Transcriber (Google Cloud API)
    ↓
WebSocket Response (JSON)
```

## Setup

### Prerequisites

- Python 3.12+
- Google Cloud Speech API credentials
- macOS/Linux

### Installation

1. Set up virtual environment with uv:
```bash
cd backend
uv sync
```

2. Add Google Cloud credentials:
```bash
# Save your service account JSON to:
backend/google_credentials.json
```

3. Configure environment:
```bash
# backend/.env
GOOGLE_APPLICATION_CREDENTIALS=./google_credentials.json
```

## Running

```bash
cd backend
uv run python main.py
```

Server runs on `http://localhost:8002`

## WebSocket API

### Endpoint: `/ws`

#### Message Types Sent by Client

- Binary audio frames (PCM 16-bit, 16kHz)

#### Message Types Received from Server

**speech_start**
```json
{"type": "speech_start"}
```

**live_transcript**
```json
{"type": "live_transcript", "text": "partial text"}
```

**transcript** (final)
```json
{"type": "transcript", "text": "complete sentence"}
```

**speech_end**
```json
{"type": "speech_end"}
```

**heartbeat**
```json
{"type": "heartbeat"}
```

## Configuration

Edit `backend/app/config.py` to adjust parameters:

- `VAD_ENERGY_RATIO`: Speech detection sensitivity (lower = more sensitive)
- `VAD_MIN_SPEECH_FRAMES`: Frames needed to start speech detection
- `VAD_MIN_SILENCE_FRAMES`: Frames of silence to end speech
- `TRANSCRIBER_STREAM_INTERVAL`: Seconds between live transcription updates
- `SAMPLE_RATE`: Audio sample rate (Hz)
- `DEBUG`: Enable debug mode

## Testing

```bash
cd backend
uv run python test/test_stt_client.py
```

Speak into your microphone. Live transcriptions appear every 2 seconds during speech, with a final transcription when you stop.

## Performance

- **Latency**: ~2-3 seconds for live updates, 3-5 seconds for final transcription
- **Audio Format**: PCM 16-bit, 16kHz mono
- **Max Concurrent Connections**: Depends on Google Cloud API quota

## Troubleshooting

### Speech not detected
- Check microphone input levels
- Reduce `VAD_ENERGY_RATIO` (more sensitive)
- Check `VAD_MIN_SILENCE_FRAMES` isn't too high

### Duplicate transcriptions
- Ensure `TRANSCRIBER_STREAM_INTERVAL` and `TRANSCRIBER_MIN_NEW_AUDIO_SAMPLES` are set correctly

### Google Cloud errors
- Verify credentials file path in `.env`
- Check API is enabled in Google Cloud Console
- Verify service account has Speech-to-Text permissions

## File Structure

```
backend/
├── app/
│   ├── app.py              # Main FastAPI application
│   ├── config.py           # Configuration management
│   ├── vad.py              # Voice Activity Detection
│   ├── speech_transcriber.py # Speech-to-Text service
│   ├── noise_suppressor.py # Audio noise suppression
│   └── audio_buffer.py     # Audio frame buffering
├── test/
│   └── test_stt_client.py  # WebSocket test client
├── main.py                 # Entry point
├── pyproject.toml          # Dependencies
└── .env                    # Environment variables
```

## Security

- Keep `google_credentials.json` out of version control (added to .gitignore)
- Use environment variables for sensitive data
- Validate WebSocket connections in production

## License

Proprietary
