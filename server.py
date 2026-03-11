import av
import struct
import json
import logging
import asyncio
import uvicorn
import sys
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from src.loader import Thread
from src.cache import Cache 
from src.utils import angle_to_index 

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()
video_dir = sys.argv[1] if len(sys.argv) > 1 else "."
thread = Thread(video_dir)
cache = Cache(thread)

cache.load_layer(0)

@app.websocket("/ws/{layer_idx}")
async def websocket_endpoint(websocket: WebSocket, layer_idx: int):
    await websocket.accept()
    
    if layer_idx not in cache.storage:
        await cache.preload_layer(layer_idx)
        
    layer_data = cache.get_layer(layer_idx)
    if not layer_data:
        await websocket.close(reason="Layer not found")
        return

    nal_cache, extradata = layer_data
    total_frames = len(nal_cache)

    # preload adjacent layers
    asyncio.create_task(cache.preload_layer(layer_idx + 1))
    asyncio.create_task(cache.preload_layer(layer_idx - 1))

    init_payload = struct.pack('>B', 0) + (extradata or b"")
    await websocket.send_bytes(init_payload)
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                params = json.loads(data)

                idx_l, idx_r = angle_to_index(params, total_frames)

                left_nal = nal_cache[idx_l]
                right_nal = nal_cache[idx_r]

                header = struct.pack('>BI', 1, len(left_nal))
                payload = header + left_nal + right_nal
                
                await websocket.send_bytes(payload)

            except (ValueError, json.JSONDecodeError):
                pass
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from layer {layer_idx}")

app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)