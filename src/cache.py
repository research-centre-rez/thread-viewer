from src.loader import Thread
from tqdm import tqdm
import logging
import asyncio

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
        cap, frame_count = self.loader.get_capture(idx)
        left: list[bytes] = []
        right: list[bytes] = []

        for _ in tqdm(range(frame_count), desc=f"Loading layer {idx} footage"):
            ret, frame = cap.read()
            if not ret:
                break

            left.append(encode_frame(frame, True).tobytes())
            right.append(encode_frame(frame, False).tobytes())

            self.storage[idx] = (left, right)

        cap.release()
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