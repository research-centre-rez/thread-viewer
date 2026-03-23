from pathlib import Path
import logging 
import argparse
from src.utils import file_count

parser = argparse.ArgumentParser("Thread preprocessing")
parser.add_argument("source", help="Folder containing the pre-processed thread", type=str)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Thread:
    def __init__(self):
        self.path = Path(parser.parse_args().source)
        self.layers = [[] * file_count(self.path)]
        logging.info(f"Using thread path: {self.path}")

        for idx, l in enumerate(self.path.iterdir()):
            self.frames = sorted([f for f in l.iterdir() if f.suffix == ".jpg"])
            if not self.frames:
                raise ValueError(f"No frames found in layer {l.name}")
            self.layers[idx] = self.frames

    def get_path(self, index) -> Path:
        if 0 > index >= len(self.layers):
            raise IndexError("Layer index out of bounds")

        return self.layers[index]