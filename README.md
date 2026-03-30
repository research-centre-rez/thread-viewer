# thread-viewer

## Project description



## Setup

This guide assumes up-to-date [uv](https://docs.astral.sh/uv/) and ffmpeg installations.

Create a new virtual environment and install dependencies with:

```bash
uv venv thread-viewer
.venv/bin/activate
uv pip install -e .
```

## Usage
> [!WARNING]: the script assumes the directory
> contains individual layers of the given thread.


**Pre-process a single thread**

 Substitute `THREAD_DIR` with per-layer videos location. Substitute `THREAD_NAME` with the experiment name.

```bash
python scripts/preprocess.py <THREAD_DIR> <THREAD_NAME>
```

After the offline pre-processing is finished, display the prepared thread. Loading a jpeg encoded thread should take around ~0.5s from a cold start.

**Start the viewer server**

```bash
python server.py demux/<THREAD_NAME>
```

**Open the client**

Start a browser of your choice, supported by the headset.

Navigate to localhost: ` http://0.0.0.0:8000 ` and follow HUD instructions.