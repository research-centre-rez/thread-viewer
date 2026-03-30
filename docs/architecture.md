# Architecture

## Front-end
### A-frame 
The client relies on A-Frame to render a WebXR stereoscopic scene containing a user camera and two distinct video planes.  WebGL shader applies dynamic horizontal image translation directly to the textures. WebSocket connection continuously streams raw JPEG binaries into JavaScript objects, which are decoded into textures for immediate GPU rendering.

### Controls
User headset yaw is mapped from a full 360-degree rotation to the total frame count of the video. Hardware VR controllers (left, right) and keyboard (A, D) allow the user to manually adjust the frame delay and convergence shift.

## Back-end

### Offline ffmpeg pre-process
`scripts/preprocess.py` demuxes a raw mp4 video files into individual JPEG frames. The script supposes the offline variant of the problem.

### Inter-eye delay
The server dynamically calculates stereoscopic parallax by offsetting the requested frame index for the right eye based on the delay parameter.

### Layer management
The FastAPI server async caches multiple pre-processed video layers into RAM. Adjacent threads are preloaded into memory to guarantee zero-latency switching when the user triggers a layer change.