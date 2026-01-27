import os
import numpy as np
import time
from pathlib import Path
from google.cloud import speech_v1
from typing import Optional


class SpeechTranscriber:
    def __init__(self, sample_rate: int = 16000, language_code: str = "en-US", stream_interval: float = 2.0):
        self.sample_rate = sample_rate
        self.language_code = language_code
        self.stream_interval = stream_interval
        self.client = None
        self.config = None

        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if credentials_path:
            abs_path = str(Path(credentials_path).resolve())
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = abs_path

        try:
            self.client = speech_v1.SpeechClient()
            self.config = speech_v1.RecognitionConfig(
                encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=sample_rate,
                language_code=language_code,
            )
        except Exception as e:
            print(f"Warning: Could not initialize Google Cloud Speech API: {e}")
            print("Set GOOGLE_APPLICATION_CREDENTIALS environment variable with path to your credentials JSON")

        self.audio_buffer = np.array([], dtype=np.int16)
        self.last_transcribe_time = time.time()
        self.last_transcribed_length = 0

    def add_frame(self, frame: np.ndarray) -> None:
        self.audio_buffer = np.concatenate([self.audio_buffer, frame.astype(np.int16)])

    def should_transcribe(self) -> bool:
        return time.time() - self.last_transcribe_time >= self.stream_interval

    def transcribe(self, clear_buffer: bool = True) -> Optional[str]:
        if len(self.audio_buffer) == 0 or self.client is None:
            return None

        if not clear_buffer:
            new_samples = len(self.audio_buffer) - self.last_transcribed_length
            if new_samples < 16000:
                return None

        try:
            audio_bytes = self.audio_buffer.tobytes()
            audio = speech_v1.RecognitionAudio(content=audio_bytes)

            response = self.client.recognize(config=self.config, audio=audio)

            self.last_transcribed_length = len(self.audio_buffer)

            if clear_buffer:
                self.audio_buffer = np.array([], dtype=np.int16)
                self.last_transcribed_length = 0

            self.last_transcribe_time = time.time()

            if response.results:
                transcript = " ".join(
                    result.alternatives[0].transcript
                    for result in response.results
                )
                return transcript if transcript.strip() else None

            return None
        except Exception as e:
            print(f"Transcription error: {e}")
            if clear_buffer:
                self.audio_buffer = np.array([], dtype=np.int16)
                self.last_transcribed_length = 0
            return None

    def clear(self) -> None:
        self.audio_buffer = np.array([], dtype=np.int16)
        self.last_transcribed_length = 0
        self.last_transcribe_time = time.time()
