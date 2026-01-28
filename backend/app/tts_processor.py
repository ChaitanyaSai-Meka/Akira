import os
import logging
import time
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

    def text_to_audio(self, text: str, max_retries: int = 3) -> Optional[bytes]:
        if not self.client or not text or not text.strip():
            return None

        for attempt in range(max_retries):
            try:
                logger.debug(f"Generating TTS for text: {text[:50]}...")
                logger.info(f"Generating TTS (text_length={len(text)}, attempt={attempt + 1}/{max_retries})")
                
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
                
                if audio_data and len(audio_data) > 0:
                    logger.info(f"Received Deepgram TTS audio: {len(audio_data)} bytes")
                    return audio_data
                else:
                    logger.warning("TTS returned empty audio data")
                    
            except (httpx.ConnectError, httpx.TimeoutException, ConnectionError) as e:
                logger.warning(f"Network error on attempt {attempt + 1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 0.5
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {max_retries} attempts failed due to network errors")
                    return None
            except Exception as e:
                logger.error(f"Deepgram TTS error: {e}", exc_info=True)
                return None
        
        return None

    def is_available(self) -> bool:
        return self.client is not None

