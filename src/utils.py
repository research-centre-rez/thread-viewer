from typing import Any
import logging
import struct
import cv2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

JPEG_QUALITY = 100

def encode_frame(frame, is_left: bool):
    """
    side (bool) 1=left half, 0=right half
    """
    mid = frame.shape[:2][1] // 2
    section = frame[:, :mid] if is_left else frame[:, mid:]
    _, buff = cv2.imencode(
        ".jpg", section, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
    )

    return buff

def angle_to_index(params: dict[str, Any], frame_count: int) -> tuple[int, int]:
    pct = float(params.get("pct", 0.0))
    delay = int(params.get("delay", 0))

    idx_l = int(pct * (frame_count - 1))
    idx_l = max(0, min(idx_l, frame_count - 1))

    idx_r = idx_l + delay
    idx_r = max(0, min(idx_r, frame_count - 1))

    return (idx_l, idx_r)

def unbound_access(bottom_bound, top_bound, access):
    if bottom_bound <= access <= top_bound:
        return False 

    logger.info(f"Out of bounds acces to layer {access}")
    return True 

def construct_payload(layer_data: tuple[list[bytes], list[bytes]], params: dict[str, Any]) -> bytes:
    """
    create payload in byte format to send through the websocket

    size, left view, right view
    """
    left, right = layer_data
    idx_l, idx_r = angle_to_index(params, len(left))

    left_bytes = left[idx_l]
    right_bytes = right[idx_r]

    header = struct.pack(">I", len(left_bytes))
    return header + left_bytes + right_bytes
