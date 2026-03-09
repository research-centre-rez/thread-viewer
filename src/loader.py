import cv2
from pathlib import Path
import logging 
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Thread:
    def __init__(self):
        self.path = Path(sys.argv[1])
        logging.info(f"Using thread path: {self.path}")

        self.layers = sorted([f for f in self.path.iterdir() if f.suffix == ".mp4"])
        if not self.layers:
            logger.error("No .mp4 files found in the specified directory.")
            sys.exit(1)

        logging.info(f"Found layer footage: {self.layers}")


    def get_capture(self, index) -> tuple[cv2.VideoCapture, int]:
        try:
            cap = cv2.VideoCapture(str(self.layers[index]))
        except Exception as e:
            logger.error(f"No video provided: {e}")
            sys.exit(1)

        return (cap, int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))