import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "./google_credentials.json")
    SAMPLE_RATE = 16000
    FRAME_SIZE = 320
    VAD_ENERGY_RATIO = 1.2
    VAD_MIN_SPEECH_FRAMES = 2
    VAD_MIN_SILENCE_FRAMES = 30
    TRANSCRIBER_STREAM_INTERVAL = 2.0
    TRANSCRIBER_MIN_NEW_AUDIO_SAMPLES = 16000
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
