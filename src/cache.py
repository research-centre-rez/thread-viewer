from src.loader import Thread
from tqdm import tqdm
import logging
import asyncio
import tempfile
from pathlib import Path
import subprocess

from src.utils import encode_frame

type HalfView = list[bytes]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Cache:
    def __init__(self, loader: Thread) -> None:
        """
        self.storage (dict[int, tuple[Layer, Layer]]):
            associates each layer index to a pair of left and right eye views
        """
        self.loader = loader
        self.storage: dict[int, tuple[HalfView, HalfView]] = {}
        self.jobs = set()

    def load_layer(self, idx: int) -> None:
        video_path = self.loader.get_path(idx)
        left: list[bytes] = []
        right: list[bytes] = []

        logger.info(f"Extracting layer {idx} frames via ffmpeg")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            cmd = [
                "ffmpeg", "-y", 
                "-hide_banner", "-loglevel", "warning", "-stats",
                "-i", str(video_path),
                "-filter_complex", "[0:v]crop=iw/2:ih:0:0[l];[0:v]crop=iw/2:ih:iw/2:0[r]",
                "-map", "[l]", "-q:v", "2", str(temp_path / "l_%06d.jpg"),
                "-map", "[r]", "-q:v", "2", str(temp_path / "r_%06d.jpg")
            ]
            
            subprocess.run(
                cmd, 
                stdout=subprocess.DEVNULL, 
                check=True
            )
            
            l_files = sorted(temp_path.glob("l_*.jpg"))
            r_files = sorted(temp_path.glob("r_*.jpg"))
            frame_count = len(l_files)

            for l_file, r_file in tqdm(zip(l_files, r_files), total=frame_count, desc=f"Loading layer {idx} to RAM"):
                with open(l_file, "rb") as fl, open(r_file, "rb") as fr:
                    left.append(fl.read())
                    right.append(fr.read())

        self.storage[idx] = (left, right)
        logger.info(f"Loaded {frame_count} frame pairs")

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

    def get_layer(self, idx: int) -> tuple[HalfView, HalfView] | None:
        return self.storage.get(idx)

    def pop_layer(self, idx: int) -> None:
        self.storage.pop(idx, None)