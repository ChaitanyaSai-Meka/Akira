import os
import logging
from typing import Optional
from deepgram import DeepgramClient
import httpx

logger = logging.getLogger(__name__)


class TTSProcessor:
    def __init__(self, model: str = "aura-asteria-en"):
        self.model = model
        self.client = None
        
        api_key = os.getenv("DEEPGRAM_API_KEY")
        if api_key:
            try:
                self.client = DeepgramClient(api_key=api_key)
                logger.info(f"Deepgram TTS initialized with model: {self.model}")
            except Exception as e:
                logger.error(f"Failed to initialize Deepgram TTS client: {e}")
                self.client = None
        else:
            logger.warning("No Deepgram API key found, TTS disabled")

    def text_to_audio(self, text: str) -> Optional[bytes]:
        if not self.client or not text or not text.strip():
            return None

        try:
            logger.info(f"Generating TTS for text: {text[:50]}...")
            
            response = self.client.speak.v1.audio.generate(
                text=text,
                model=self.model,
                encoding="linear16",
                sample_rate=16000,
            )
            
            if isinstance(response, httpx.Response):
                audio_data = response.content
            else:
                audio_data = b"".join(response)
            
            logger.info(f"Received Deepgram TTS audio: {len(audio_data)} bytes")
            return audio_data

        except Exception as e:
            logger.error(f"Deepgram TTS error: {e}", exc_info=True)
            return None

    def is_available(self) -> bool:
        return self.client is not None

