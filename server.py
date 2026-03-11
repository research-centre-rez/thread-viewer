import uvicorn
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import asyncio

from src.loader import Thread 
from src.cache import Cache 
from src.utils import construct_payload, unbound_access

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

thread = Thread()
cache = Cache(thread)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[BLOCKING OPERATION] Loading first layer")
    cache.load_layer(0)
    
    logger.info("[BLOCKING OPERATION] Preloading second layer")
    asyncio.create_task(cache.preload_layer(1))

    yield

    logger.info("Shutting down, clearing cache")
    cache.storage.clear()

app = FastAPI(lifespan=lifespan)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    current_idx = 0 # index stored PER CONNECTION
    try:
        while True:
            data = await websocket.receive_text()
            try:
                params = json.loads(data)
                
                # move to the next layer
                action = params.get("action", "")
                direction = 1 if action == "next"  else -1 if action == "prev" else 0

                if action:
                    if unbound_access(0, len(thread.layers), current_idx+direction):
                        continue

                    current_idx += direction
                    logger.info(f"Changing to layer {current_idx}")
                    asyncio.create_task(cache.preload_layer(current_idx + direction))
                    continue

                layer_data = cache.get_layer(current_idx)
                if not layer_data:
                    logger.warning(f"Layer {current_idx} not loaded yet.")
                    continue

                payload = construct_payload(layer_data, params)
                await websocket.send_bytes(payload)

            except (ValueError, json.JSONDecodeError) as e:
                logger.error(f"Payload error: {e}")

    except WebSocketDisconnect:
        logger.info("Client disconnected")


app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

