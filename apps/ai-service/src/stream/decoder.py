import logging
from typing import Any

# Note: We avoid direct hard dependencies on gi inside this file if it is running on a CPU-only
# dev machine where gi isn't installed (though it will run fine inside Docker).
logger = logging.getLogger("ai_service.stream.decoder")

class HardwareDecoder:
    """Configures and optimizes NVIDIA hardware-accelerated GStreamer video decoders (nvv4l2decoder)."""

    def __init__(self, gpu_id: int = 0):
        self.gpu_id = gpu_id

    def configure_properties(self, decoder_element: Any, skip_frames_level: int = 0) -> None:
        """Applies GPU-accelerated settings and load reduction configurations to the GStreamer element.
        
        Args:
            decoder_element: The GStreamer nvv4l2decoder element instance.
            skip_frames_level: Optimization flag indicating which frame types to skip during decoding.
                0: Decode all frames (Maximum accuracy - Default)
                1: Skip non-reference frames (Light CPU/GPU reduction)
                2: Skip B-frames (Moderate GPU memory/compute savings)
                3: Decode key-frames (I-frames) only (Aggressive CPU/GPU savings)
        """
        if decoder_element is None:
            logger.warning("Decoder element is null. Skipping hardware properties configuration.")
            return

        try:
            # Bind the decoder to the correct NVIDIA GPU
            decoder_element.set_property("gpu-id", self.gpu_id)
            
            # Configure frame skipping to balance frame rate vs GPU load
            decoder_element.set_property("skip-frames", skip_frames_level)
            
            # Enable low-latency decoding pipeline behavior
            decoder_element.set_property("low-latency-mode", 1)
            
            logger.info(
                f"Configured GPU hardware decoder '{decoder_element.get_name()}' "
                f"on GPU Device {self.gpu_id} with skip-frames level: {skip_frames_level}"
            )
        except Exception as e:
            logger.error(
                f"Error applying properties to decoder element '{getattr(decoder_element, 'get_name', lambda: 'unknown')()}': {e}"
            )
