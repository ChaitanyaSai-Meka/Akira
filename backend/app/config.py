import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    SAMPLE_RATE = 16000
    FRAME_SIZE = 320
    VAD_AGGRESSIVENESS = 2
    VAD_MIN_SPEECH_FRAMES = 6
    VAD_MIN_SILENCE_FRAMES = 30
    TRANSCRIBER_STREAM_INTERVAL = 2.5
    TRANSCRIBER_MIN_NEW_AUDIO_SAMPLES = 20000
    TRANSCRIBER_MIN_AUDIO_DURATION = 0.6
    WEBSOCKET_TIMEOUT = 5.0
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


def get_config():
    env = os.getenv("ENVIRONMENT", "development")
    if env == "production":
        return ProductionConfig()
    return DevelopmentConfig()
