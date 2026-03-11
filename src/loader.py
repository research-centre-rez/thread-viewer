import cv2
from pathlib import Path
import logging 
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class Thread:
    def __init__(self, directory: str):
        self.dir_path = Path(directory)
        self.layers = sorted([p for p in self.dir_path.glob("*.mp4")])
        if not self.layers:
            logger.error(f"No MP4 files found in {self.dir_path}")
            sys.exit(1)
        logger.info(f"Loaded {len(self.layers)} video layers from {self.dir_path}")

    def get_path(self, idx: int) -> Path:
        return self.layers[idx]
