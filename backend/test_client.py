import asyncio
import websockets
import numpy as np

async def send_audio():
    uri = "ws://localhost:8002/ws"
    async with websockets.connect(uri) as websocket:
        for _ in range(50):
            # 20ms of silence @16kHz
            samples = np.zeros(320, dtype=np.int16)
            await websocket.send(samples.tobytes())
            await asyncio.sleep(0.02)

asyncio.run(send_audio())
