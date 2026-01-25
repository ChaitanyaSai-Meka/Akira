import asyncio
import websockets
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
FRAME_SIZE = 320

async def stream_mic():
    uri = "ws://localhost:8002/ws"
    async with websockets.connect(uri) as websocket:

        loop=asyncio.get_event_loop()

        def callback(indata, frames, time, status):
            audio = indata[:, 0].astype(np.int16)
            asyncio.run_coroutine_threadsafe(
                websocket.send(audio.tobytes()),
                loop
            )

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
            blocksize=FRAME_SIZE,
            callback=callback,
        ):
            print(" Speaking... Press Ctrl+C to stop")
            await asyncio.Future()  

asyncio.run(stream_mic())