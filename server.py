import cv2
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

VIDEO_PATH = "assets/delayed/output_sbs_delayed_25.mp4"
JPEG_QUALITY = 70
cache = []

cap = cv2.VideoCapture(VIDEO_PATH)
    
while True:
    ret, frame = cap.read()
    if not ret:
        break
        
    if not(len(cache) % 100):
        print(f"Loaded {len(cache)} frames")

    _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
    cache.append(buffer.tobytes())
    
cap.release()
total_frames = len(cache)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            try:
                pct = float(data)

                frame_idx = int(pct * (total_frames - 1))
                frame_idx = max(0, min(frame_idx, total_frames - 1))
                
                #"O(1)" lookup
                await websocket.send_bytes(cache[frame_idx])
                
            except ValueError:
                pass
    except WebSocketDisconnect:
        print("Client disconnected")

app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)