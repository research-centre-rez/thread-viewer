from typing import Any
import logging
import struct
import cv2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def angle_to_index(params: dict[str, Any], frame_count: int) -> tuple[int, int]:
    pct = float(params.get("pct", 0.0))
    delay = int(params.get("delay", 0))

    idx_l = int(pct * (frame_count - 1))
    idx_l = max(0, min(idx_l, frame_count - 1))

    idx_r = idx_l + delay
    idx_r = max(0, min(idx_r, frame_count - 1))

    return (idx_l, idx_r)