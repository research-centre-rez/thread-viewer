import av
import logging
import asyncio

from src.loader import Thread

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class Cache:
    def __init__(self, loader: Thread) -> None:
        self.loader = loader
        self.storage: dict[int, tuple[list[bytes], bytes]] = {}
        self.jobs = set()

    def load_layer(self, idx: int) -> None:
        if idx >= len(self.loader.layers):
            return
            
        video_path = self.loader.get_path(idx)
        nal_cache: list[bytes] = []
        extradata = b""

        logger.info(f"Demuxing NAL units for layer {idx}: {video_path.name}")

        try:
            container = av.open(str(video_path))
            video_stream = container.streams.video[0]
            extradata = video_stream.codec_context.extradata or b""

            for packet in container.demux(video_stream):
                if packet.dts is None:
                    continue
                nal_cache.append(bytes(packet))
                
            container.close()
        except Exception as e:
            logger.error(f"Failed to load layer {idx}: {e}")
            return

        self.storage[idx] = (nal_cache, extradata)
        logger.info(f"Loaded {len(nal_cache)} NAL units for layer {idx}")

    async def preload_layer(self, idx: int):
        if idx in self.jobs or idx in self.storage:
            return
        if idx >= len(self.loader.layers) or idx < 0:
            return
            
        self.jobs.add(idx)
        await asyncio.to_thread(self.load_layer, idx)
        self.jobs.discard(idx)

    def get_layer(self, idx: int) -> tuple[list[bytes], bytes] | None:
        return self.storage.get(idx)