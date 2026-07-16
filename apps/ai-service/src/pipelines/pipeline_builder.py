import logging
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

logger = logging.getLogger("ai_service.pipeline")

class PipelineBuilder:
    """Helper class to programmatically build a GStreamer/DeepStream Pipeline."""
    def __init__(self, name: str = "ds-pipeline"):
        Gst.init(None)
        self.pipeline = Gst.Pipeline.new(name)
        if not self.pipeline:
            raise RuntimeError("Failed to create GStreamer pipeline instance")
        self.elements = {}

    def add_element(self, factory_name: str, name: str) -> Gst.Element:
        """Creates a GStreamer element and adds it to the pipeline."""
        element = Gst.ElementFactory.make(factory_name, name)
        if not element:
            raise RuntimeError(f"Failed to create element '{name}' from factory '{factory_name}'")
        self.pipeline.add(element)
        self.elements[name] = element
        logger.debug(f"Added element {name} ({factory_name}) to pipeline")
        return element

    def set_properties(self, name: str, **properties):
        """Sets properties on a registered pipeline element."""
        element = self.elements.get(name)
        if not element:
            raise KeyError(f"Element '{name}' not found in pipeline dictionary")
        for key, val in properties.items():
            element.set_property(key, val)
            logger.debug(f"Set property '{key}' = '{val}' on element '{name}'")

    def link_elements(self, *names):
        """Linearly links a list of registered element names in the order provided."""
        for i in range(len(names) - 1):
            src = self.elements.get(names[i])
            dest = self.elements.get(names[i+1])
            if not src or not dest:
                raise KeyError(f"Failed to link: elements '{names[i]}' or '{names[i+1]}' not found")
            if not src.link(dest):
                raise RuntimeError(f"Failed to link GStreamer element '{names[i]}' to '{names[i+1]}'")
            logger.debug(f"Linked element '{names[i]}' -> '{names[i+1]}'")

    def link_request_pad(self, src_name: str, dest_name: str, pad_template: str = "sink_%u", pad_index: int = 0):
        """Links a source element's src pad to a destination element's request pad (e.g. nvstreammux sink pad)."""
        src = self.elements.get(src_name)
        dest = self.elements.get(dest_name)
        if not src or not dest:
            raise KeyError(f"Elements '{src_name}' or '{dest_name}' not found")

        # Get request pad on destination
        pad_name = pad_template.replace("%u", str(pad_index))
        dest_pad = dest.get_request_pad(pad_name)
        if not dest_pad:
            raise RuntimeError(f"Failed to get request pad '{pad_name}' on '{dest_name}'")

        # Get static src pad on source element
        src_pad = src.get_static_pad("src")
        if not src_pad:
            # If static pad doesn't exist, try getting request or dynamic pad
            src_pad = src.get_request_pad("src")
        
        if not src_pad:
            raise RuntimeError(f"Failed to get src pad on source element '{src_name}'")

        # Link pads
        status = src_pad.link(dest_pad)
        if status != Gst.PadLinkReturn.OK:
            raise RuntimeError(f"Failed to link pads {src_name}.src -> {dest_name}.{pad_name}: status {status}")
        logger.debug(f"Linked pad '{src_name}.src' -> '{dest_name}.{pad_name}'")

    def get_element(self, name: str) -> Gst.Element:
        """Returns GStreamer element instance by key name."""
        return self.elements.get(name)

    def get_pipeline(self) -> Gst.Pipeline:
        """Returns the completed GStreamer Pipeline instance."""
        return self.pipeline
