from fastapi import FastAPI,WebSocket,WebSocketDisconnect
from dotenv import load_dotenv
import numpy as np

load_dotenv()

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection accepted")

    try:
        while True:
            audio_bytes = await websocket.receive_bytes()
            audio_np = np.frombuffer(audio_bytes,dtype=np.int16)
            print("Received length samples:", len(audio_np))
    except WebSocketDisconnect:
        print("WebSocket connection closed")