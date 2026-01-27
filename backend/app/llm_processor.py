import os
import logging
from groq import Groq, APIError
from typing import Optional

logger = logging.getLogger(__name__)


class LLMProcessor:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_LLM_API_KEY"))
        self.model = "llama-3.1-8b-instant"

    def process(self, text: str) -> Optional[str]:
        if not text or not text.strip():
            return None

        try:
            message = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are Akira, a concise assistant. Answer in 1-2 short sentences. Avoid filler, repetition, and disclaimers."
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.3,
                max_tokens=100,
            )

            response = message.choices[0].message.content
            return response if response.strip() else None

        except APIError as e:
            logger.error(f"Groq API error for model {self.model}: {e}", exc_info=True)
            return None
