import subprocess
import sys
from pathlib import Path
import os
import argparse
from datetime import datetime

parser = argparse.ArgumentParser("Thread preprocessing")
parser.add_argument("source", help="Folder containing original thread videos, video per layer", type=str)
parser.add_argument("name", help="Name of the thread", type=str, default=datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))

OUTPUT_PATH = Path("../demux")


def main():
    args = parser.parse_args()
    os.makedirs(OUTPUT_PATH, exist_ok=True)

    layers = sorted(Path(args.source).glob("*.mp4"))
    for idx, layer in enumerate(layers):
        video_path = layer

        os.makedirs(OUTPUT_PATH/ args.name / f"layer_{idx:03d}", exist_ok=True)

        cmd = [
            "ffmpeg", "-y", 
            "-hide_banner", "-loglevel", "warning", "-stats",
            "-i", str(video_path),
            "-q:v", "2", str(OUTPUT_PATH / args.name / f"layer_{idx:03d}" / "f_%05d.jpg")
        ]
        
        subprocess.run(
            cmd, 
            stdout=subprocess.DEVNULL, 
            check=True
        )
                
        frame_count = sum(1 for item in (OUTPUT_PATH / args.name / f"layer_{idx:03d}").iterdir() if item.is_file())
        print(f"Layer {idx}: Extracted {frame_count} frames")

if __name__ == "__main__":
    main()