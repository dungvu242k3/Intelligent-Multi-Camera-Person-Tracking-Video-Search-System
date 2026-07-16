import logging
import numpy as np
import pyds
from datetime import datetime
from apps.ai-service.src.events.kafka_producer import KafkaEventProducer
from apps.ai-service.src.storage.crop_saver import CropSaver

logger = logging.getLogger("ai_service.probes")

# Class index mapping matching our yolo_labels.txt
CLASS_MAPPING = {
    0: "person",
    1: "fire",
    2: "smoke",
    3: "object"
}

class DeepStreamProbeCallbacks:
    """Class containing GStreamer pad probe callbacks for metadata extraction."""
    def __init__(self, kafka_producer: KafkaEventProducer, crop_saver: CropSaver, kafka_topic: str = "detection-events"):
        self.kafka_producer = kafka_producer
        self.crop_saver = crop_saver
        self.kafka_topic = kafka_topic

    def tracking_src_pad_buffer_probe(self, pad, info, u_data) -> int:
        """Probe callback registered at the output pad of SGIE (ReID) or Tracker.
        Intercepts metadata and sends events to Kafka/MinIO.
        """
        gst_buffer = info.get_buffer()
        if not gst_buffer:
            logger.warning("Unable to get GstBuffer from pad info")
            return pyds.GST_PAD_PROBE_OK

        # Fetch batch metadata from GstBuffer
        batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
        
        # Iterate through frames in the batch
        l_frame = batch_meta.frame_meta_list
        while l_frame is not None:
            try:
                frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
            except StopIteration:
                break

            frame_number = frame_meta.frame_num
            camera_id = str(frame_meta.source_id) # Stream ID
            timestamp = datetime.utcnow().isoformat() + "Z"

            # Retrieve the raw frame image as a NumPy array (efficient NVMM mapping)
            frame_np = None
            try:
                # pyds utility maps raw buffer memory to standard NumPy ndarray
                frame_np = pyds.get_nvds_buf_surface(hash(gst_buffer), frame_meta.batch_id)
            except Exception as e:
                logger.error(f"Failed to get NumPy surface for frame {frame_number}: {e}")

            # Iterate through detected objects in this frame
            l_obj = frame_meta.obj_meta_list
            while l_obj is not None:
                try:
                    obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
                except StopIteration:
                    break

                class_id = obj_meta.class_id
                object_type = CLASS_MAPPING.get(class_id, "unknown")
                confidence = obj_meta.confidence
                tracking_id = obj_meta.object_id # Unique ID across frames (from nvtracker)

                # Bounding box coordinates
                bbox = obj_meta.rect_params
                
                # Check for SGIE ReID embedding metadata (only for person class)
                embedding = []
                if class_id == 0: # person
                    embedding = self._extract_reid_embedding(obj_meta)

                # Save crop image asynchronously to MinIO (if frame surface mapping succeeded)
                crop_path = ""
                if frame_np is not None:
                    crop_path = self.crop_saver.save_crop_async(frame_np, bbox, object_type)

                # Construct event payload
                event_payload = {
                    "event_id": f"{camera_id}_{frame_number}_{tracking_id}_{class_id}",
                    "timestamp": timestamp,
                    "camera_id": camera_id,
                    "frame_number": frame_number,
                    "detection": {
                        "class_id": class_id,
                        "type": object_type,
                        "confidence": float(confidence),
                        "tracking_id": int(tracking_id),
                        "bbox": {
                            "left": float(bbox.left),
                            "top": float(bbox.top),
                            "width": float(bbox.width),
                            "height": float(bbox.height)
                        },
                        "embedding": embedding,
                        "crop_path": crop_path
                    }
                }

                # Push event to Kafka
                # Using tracking_id as key ensures all events for a single target go to the same Kafka partition!
                kafka_key = f"{camera_id}_{tracking_id}"
                self.kafka_producer.send_event(
                    topic=self.kafka_topic,
                    key=kafka_key,
                    event_data=event_payload
                )

                try:
                    l_obj = l_obj.next
                except StopIteration:
                    break

            try:
                l_frame = l_frame.next
            except StopIteration:
                break

        return pyds.GST_PAD_PROBE_OK

    def _extract_reid_embedding(self, obj_meta) -> list:
        """Helper to extract secondary classifier (ReID) embedding vector from user metadata."""
        embedding = []
        l_user = obj_meta.obj_user_meta_list
        while l_user is not None:
            try:
                user_meta = pyds.NvDsUserMeta.cast(l_user.data)
            except StopIteration:
                break

            # Check if this user metadata contains Tensor output from SGIE (gie-id 2)
            if user_meta.base_meta.meta_type == pyds.NVDSINFER_TENSOR_OUTPUT_META:
                try:
                    tensor_meta = pyds.NvDsInferTensorMeta.cast(user_meta.user_meta_data)
                    # Loop over output layers and find our 'features' layer (OSNet ReID output)
                    for i in range(tensor_meta.num_output_layers):
                        layer = pyds.get_nvds_LayerInfo(tensor_meta, i)
                        if layer.layerName == "features":
                            # Read raw float buffer of 512 dimensions
                            raw_ptr = layer.buffer
                            # Map pointer to numpy array using ctypes
                            import ctypes
                            num_elements = 512
                            float_arr = ctypes.cast(raw_ptr, ctypes.POINTER(ctypes.c_float * num_elements)).contents
                            embedding = [float(x) for x in float_arr]
                            break
                except Exception as e:
                    logger.error(f"Error parsing ReID tensor output metadata: {e}")

            try:
                l_user = l_user.next
            except StopIteration:
                break
        return embedding
