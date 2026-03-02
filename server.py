import cv2
import uvicorn
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
import logging
import sys
import struct

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

VIDEO_PATH = (
    f"assets/delayed/output_sbs_delayed_{sys.argv[1]}.mp4" if len(sys.argv) > 1 else 0
)
logging.info(f"Using video path: {VIDEO_PATH}")

print(VIDEO_PATH)

JPEG_QUALITY = 100
left_cache = []
right_cache = []

try:
    cap = cv2.VideoCapture(VIDEO_PATH)
except Exception as e:
    logger.error(f"No video provided: {e}")
    sys.exit(1)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    h, w = frame.shape[:2]
    mid = w // 2

    _, l_buf = cv2.imencode(
        ".jpg", frame[:, :mid], [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
    )
    _, r_buf = cv2.imencode(
        ".jpg", frame[:, mid:], [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
    )

    left_cache.append(l_buf.tobytes())
    right_cache.append(r_buf.tobytes())

    if len(left_cache) % 100 == 0:
        logger.info(f"Loaded {len(left_cache)} frame pairs")

cap.release()
total_frames = len(left_cache)
logger.info(f"Loaded {total_frames} frame pairs.")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    pct: current position in the video
    delay: configured delay in frames
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            try:
                params = json.loads(data)
                pct = float(params.get("pct", 0.0))
                delay = int(params.get("delay", 0))

                idx_l = int(pct * (total_frames - 1))
                idx_l = max(0, min(idx_l, total_frames - 1))

                idx_r = idx_l + delay
                idx_r = max(0, min(idx_r, total_frames - 1))

                left_bytes = left_cache[idx_l]
                right_bytes = right_cache[idx_r]

                # big endian, uint, size valid for both images
                header = struct.pack(">I", len(left_bytes))
                payload = header + left_bytes + right_bytes

                await websocket.send_bytes(payload)

            except (ValueError, json.JSONDecodeError) as e:
                logger.error(f"{e}")
                pass

    except WebSocketDisconnect:
        logger.info("Client disconnected")


app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

