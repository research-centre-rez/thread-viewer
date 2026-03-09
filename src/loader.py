import cv2
from pathlib import Path
import logging 
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Thread:
    def __init__(self):
        if len(sys.argv) < 2:
            logging.error("Too few arguments!")
            sys.exit(1)

        self.path = Path(sys.argv[1])
        logging.info(f"Using thread path: {self.path}")

        self.layers = sorted([f for f in self.path.iterdir() if f.suffix == ".mp4"])
        if not self.layers:
            logger.error("No .mp4 files found in the specified directory.")
            sys.exit(1)

        logging.info(f"Found layer footage: {self.layers}")


    def get_path(self, index) -> Path:
        if 0 > index >= len(self.layers):
            raise IndexError("Layer index out of bounds")

        return self.layers[index]
