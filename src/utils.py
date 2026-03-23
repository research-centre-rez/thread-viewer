from typing import Any
import logging
import struct
from zipfile import Path

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

def unbound_access(bottom_bound: int, top_bound: int, access: int):
    if bottom_bound <= access < top_bound:
        return False 

    logger.info(f"Out of bounds access to layer {access}")
    return True 

def construct_payload(layer_data: list[bytes], params: dict[str, Any]) -> bytes:
    """
    create payload in byte format to send through the websocket
    size, left view, right view
    """
    idx_l, idx_r = angle_to_index(params, len(layer_data))

    left_bytes = layer_data[idx_l]
    right_bytes = layer_data[idx_r]

    header = struct.pack(">I", len(left_bytes))
    return header + left_bytes + right_bytes

def file_count(path: Path, ext="") -> int:
    return sum(1 for item in path.iterdir() if item.is_file() and (ext == "" or item.suffix == ext))