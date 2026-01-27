import os
from groq import Groq
from typing import Optional


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
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.7,
                max_tokens=256,
            )

            response = message.choices[0].message.content
            return response if response.strip() else None

        except Exception as e:
            print(f"LLM error: {e}")
            return None
