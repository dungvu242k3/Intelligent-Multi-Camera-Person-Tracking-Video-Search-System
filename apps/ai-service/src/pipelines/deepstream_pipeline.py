import logging
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib  # noqa: E402
from typing import List  # noqa: E402
from pipelines.pipeline_builder import PipelineBuilder  # noqa: E402
from plugins.probe_callbacks import DeepStreamProbeCallbacks  # noqa: E402

logger = logging.getLogger("ai_service.pipeline")

class DeepStreamPipeline:
    """Manages the complete lifecycle of the multi-stream DeepStream pipeline."""
    def __init__(self, sources: List[str], pgie_config: str, sgie_config: str, tracker_config: str, callbacks: DeepStreamProbeCallbacks):
        self.sources = sources
        self.pgie_config = pgie_config
        self.sgie_config = sgie_config
        self.tracker_config = tracker_config
        self.callbacks = callbacks
        
        self.builder = PipelineBuilder("multi-camera-tracking-pipeline")
        self.loop = GLib.MainLoop()
        self.bus = None
        self._build()

    def _build(self):
        """Constructs the complete GStreamer pipeline structure."""
        logger.info(f"Building pipeline with {len(self.sources)} sources...")

        # Determine model inference plugin dynamically (nvinferserver for Triton, nvinfer for local TensorRT)
        pgie_plugin = "nvinferserver" if "triton" in self.pgie_config else "nvinfer"
        sgie_plugin = "nvinferserver" if "triton" in self.sgie_config else "nvinfer"
        logger.info(f"Using Inference Plugins -> PGIE: {pgie_plugin}, SGIE: {sgie_plugin}")

        # 1. Add elements to pipeline
        # nvstreammux: Batch frames from multiple sources
        self.builder.add_element("nvstreammux", "muxer")
        # PGIE: YOLO Multi-class detector
        self.builder.add_element(pgie_plugin, "pgie")
        # nvtracker: CUDA-accelerated tracking
        self.builder.add_element("nvtracker", "tracker")
        # SGIE: ReID feature extractor
        sgie = self.builder.add_element(sgie_plugin, "sgie")
        # nvvideoconvert: Color conversion before output/probe
        self.builder.add_element("nvvideoconvert", "convert")
        # fakesink: Production sink (headless, no rendering overhead)
        self.builder.add_element("fakesink", "sink")

        # 2. Configure Streammux
        # Set video frame batch sizes and dimensional norms
        self.builder.set_properties("muxer",
            width=1920,
            height=1080,
            batch_size=len(self.sources),
            batched_push_timeout=40000, # 40ms timeout before pushing batch
            live_source=1
        )

        # 3. Configure Inference, Tracker and Converter elements
        self.builder.set_properties("pgie", config_file_path=self.pgie_config)
        self.builder.set_properties("sgie", config_file_path=self.sgie_config)
        self.builder.set_properties("convert", nvbuf_memory_type=3) # Unified Memory for NumPy access
        self.builder.set_properties("tracker",
            ll_config_file=self.tracker_config,
            ll_lib_file="/opt/nvidia/deepstream/deepstream/lib/libnvds_nvmultiobjecttracker.so"
        )
        # Disable sync for raw performance/maximum throughput
        self.builder.set_properties("sink", sync=0)

        # 4. Link general pipeline components (after muxer)
        self.builder.link_elements("muxer", "pgie", "tracker", "sgie", "convert", "sink")

        # 5. Add sources and link to nvstreammux sink pads
        for idx, src_url in enumerate(self.sources):
            source_name = f"source_{idx}"
            # nvurisourcesrc handles file:// and rtsp:// paths automatically with auto-reconnection
            self.builder.add_element("nvurisourcesrc", source_name)
            self.builder.set_properties(source_name, uri=src_url)
            # Link nvurisourcesrc src pad to muxer sink_%u request pad
            self.builder.link_request_pad(source_name, "muxer", pad_template="sink_%u", pad_index=idx)

        # 6. Add buffer pad probe callback on SGIE src pad to capture inference results
        sgie_src_pad = sgie.get_static_pad("src")
        if not sgie_src_pad:
            raise RuntimeError("Failed to obtain SGIE src pad")
            
        sgie_src_pad.add_probe(
            Gst.PadProbeType.BUFFER,
            self.callbacks.tracking_src_pad_buffer_probe,
            None
        )
        logger.info("Probe callback successfully attached to SGIE output")

        # 7. Listen for pipeline messages (Error, End-of-Stream) on GStreamer Bus
        pipeline = self.builder.get_pipeline()
        self.bus = pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message", self._on_bus_message)

    def _on_bus_message(self, bus, message):
        """Bus message event handler."""
        t = message.type
        if t == Gst.MessageType.EOS:
            logger.info("End-of-Stream (EOS) message received. Stopping pipeline...")
            self.stop()
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            logger.error(f"GStreamer Pipeline Error: {err.message} | Debug: {debug}")
            self.stop()
        return True

    def start(self):
        """Starts the GStreamer pipeline and runs the GLib main loop."""
        pipeline = self.builder.get_pipeline()
        logger.info("Starting pipeline (Setting state to PLAYING)...")
        state_return = pipeline.set_state(Gst.State.PLAYING)
        if state_return == Gst.StateChangeReturn.FAILURE:
            raise RuntimeError("Failed to set GStreamer pipeline state to PLAYING")
        
        # Start GLib thread event loop (blocks until loop.quit() is called)
        self.loop.run()

    def stop(self):
        """Stops the GLib main loop and sets pipeline state to NULL."""
        if self.loop.is_running():
            logger.info("Quitting GLib main loop...")
            self.loop.quit()
        
        pipeline = self.builder.get_pipeline()
        logger.info("Stopping pipeline (Setting state to NULL)...")
        pipeline.set_state(Gst.State.NULL)
