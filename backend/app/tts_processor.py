import os
import io
import wave
import numpy as np
from typing import Optional
import logging
from groq import Groq

logger = logging.getLogger(__name__)


class TTSProcessor:
    def __init__(self, model: str = "canopylabs/orpheus-v1-english"):
        self.model = model
        self.client = None
        
        api_key = os.getenv("GROQ_LLM_API_KEY")
        if api_key:
            try:
                self.client = Groq(api_key=api_key)
                logger.info(f"Groq TTS initialized with model: {self.model}")
            except Exception as e:
                logger.error(f"Failed to initialize Groq TTS client: {e}")
                self.client = None
        else:
            logger.warning("No Groq API key found, TTS disabled")

    def text_to_audio(self, text: str, sample_rate: int = 16000) -> Optional[bytes]:
        if not self.client or not text or not text.strip():
            return None

        try:
            response = self.client.audio.speech.create(
                model=self.model,
                input=text,
                voice="alloy",
                response_format="wav"
            )
            
            audio_data = response.read()
            
            audio_buffer = io.BytesIO()
            with wave.open(io.BytesIO(audio_data), 'rb') as wav_in:
                params = wav_in.getparams()
                audio_frames = wav_in.readframes(params.nframes)
                
                audio_array = np.frombuffer(audio_frames, dtype=np.int16)
                
                if params.nchannels > 1:
                    audio_array = audio_array.reshape(-1, params.nchannels)
                    audio_array = np.mean(audio_array, axis=1).astype(np.int16)
                
                original_rate = params.framerate
                if original_rate != sample_rate:
                    audio_array = self._resample(audio_array, original_rate, sample_rate)
            
            with wave.open(audio_buffer, 'wb') as wav_out:
                wav_out.setnchannels(1)
                wav_out.setsampwidth(2)
                wav_out.setframerate(sample_rate)
                wav_out.writeframes(audio_array.tobytes())
            
            return audio_buffer.getvalue()

        except Exception as e:
            logger.error(f"Groq TTS conversion error: {e}", exc_info=True)
            return None

    def _resample(self, audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        duration = len(audio) / orig_sr
        target_length = int(duration * target_sr)
        
        indices = np.linspace(0, len(audio) - 1, target_length)
        resampled = np.interp(indices, np.arange(len(audio)), audio)
        
        return resampled.astype(np.int16)

    def get_audio_duration(self, audio_bytes: bytes) -> float:
        try:
            with wave.open(io.BytesIO(audio_bytes), 'rb') as wav_file:
                params = wav_file.getparams()
                duration = params.nframes / params.framerate
                return duration
        except Exception as e:
            logger.error(f"Error calculating audio duration: {e}")
            return 0.0

    def is_available(self) -> bool:
        return self.client is not None

