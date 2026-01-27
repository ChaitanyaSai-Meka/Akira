import os
import numpy as np
import time
import tempfile
import wave
from pathlib import Path
from groq import Groq
from typing import Optional


class SpeechTranscriber:
    def __init__(self, sample_rate: int = 16000, stream_interval: float = 2.0):
        self.sample_rate = sample_rate
        self.stream_interval = stream_interval
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        self.audio_buffer = np.array([], dtype=np.int16)
        self.last_transcribe_time = time.time()
        self.last_transcribed_length = 0

    def add_frame(self, frame: np.ndarray) -> None:
        self.audio_buffer = np.concatenate([self.audio_buffer, frame.astype(np.int16)])

    def should_transcribe(self) -> bool:
        return time.time() - self.last_transcribe_time >= self.stream_interval

    def _create_wav_file(self, audio_data: np.ndarray) -> str:
        tmp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_path = tmp_file.name
        tmp_file.close()

        with wave.open(tmp_path, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_data.astype(np.int16).tobytes())

        return tmp_path

    def transcribe(self, clear_buffer: bool = True) -> Optional[str]:
        if len(self.audio_buffer) == 0:
            return None

        if not clear_buffer:
            new_samples = len(self.audio_buffer) - self.last_transcribed_length
            if new_samples < 16000:
                return None

        try:
            tmp_path = self._create_wav_file(self.audio_buffer)

            with open(tmp_path, "rb") as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    file=(Path(tmp_path).name, audio_file.read()),
                    model="whisper-large-v3",
                    temperature=0,
                    response_format="verbose_json",
                )

            os.unlink(tmp_path)

            self.last_transcribed_length = len(self.audio_buffer)

            if clear_buffer:
                self.audio_buffer = np.array([], dtype=np.int16)
                self.last_transcribed_length = 0

            self.last_transcribe_time = time.time()

            text = transcription.text if hasattr(transcription, 'text') else str(transcription)
            return text if text.strip() else None

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
