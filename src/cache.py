from src.loader import Thread
from tqdm import tqdm
import logging
import asyncio
import tempfile
from pathlib import Path
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Cache:
    def __init__(self, loader: Thread) -> None:
        self.loader = loader
        self.storage: dict[int, list[bytes]] = {}
        self.jobs = set()

    def load_layer(self, idx: int) -> None:
        video_path = self.loader.get_path(idx)
        frames: list[bytes] = []

        logger.info(f"Extracting layer {idx} 2D frames via ffmpeg")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            cmd = [
                "ffmpeg", "-y", 
                "-hide_banner", "-loglevel", "warning", "-stats",
                "-i", str(video_path),
                "-q:v", "2", str(temp_path / "f_%06d.jpg")
            ]
            
            subprocess.run(
                cmd, 
                stdout=subprocess.DEVNULL, 
                check=True
            )
            
            files = sorted(temp_path.glob("f_*.jpg"))
            frame_count = len(files)

            for f_file in tqdm(files, total=frame_count, desc=f"Loading layer {idx} to RAM"):
                with open(f_file, "rb") as f:
                    frames.append(f.read())

        self.storage[idx] = frames
        logger.info(f"Loaded {frame_count} frames for layer {idx}")

    async def preload_layer(self, idx: int):
        if idx in self.jobs or idx in self.storage:
            logger.info("Layer is being processed or is already loaded")
            return

        if idx >= len(self.loader.layers):
            logger.info("Out of layers")
            return
            
        self.jobs.add(idx)
        await asyncio.to_thread(self.load_layer, idx)
        self.jobs.discard(idx)

    def get_layer(self, idx: int) -> list[bytes] | None:
        return self.storage.get(idx)

    def pop_layer(self, idx: int) -> None:
        self.storage.pop(idx, None)