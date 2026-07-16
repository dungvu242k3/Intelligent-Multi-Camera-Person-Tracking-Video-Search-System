"""
GStreamer pad probe callbacks for DeepStream metadata interception.

Pipeline flow:
  nvurisourcesrc → nvstreammux → nvinfer(PGIE) → nvtracker → nvinfer(SGIE/ReID)
                                                               ↓
                                                        [this probe callback]
                                                               ↓
                                              Kafka event + MinIO crop + Qdrant embedding
"""
import logging
from datetime import datetime, timezone
from typing import Optional

try:
    import pyds
    _PYDS_AVAILABLE = True
except ImportError:
    _PYDS_AVAILABLE = False

from events.event_schemas import TrackingEvent, DetectionPayload, BoundingBox
from events.kafka_producer import KafkaEventProducer
from storage.crop_saver import CropSaver
from reid.feature_extractor import ReIDFeatureExtractor
from reid.mtmc_association import MTMCAssociator
from reid.gallery_manager import PersonGalleryManager

logger = logging.getLogger("ai_service.probes")

# Class index → label (must match yolo_labels.txt order)
CLASS_MAPPING = {
    0: "person",
    1: "fire",
    2: "smoke",
    3: "object",
}

GST_PAD_PROBE_OK = 0  # Gst.PadProbeReturn.OK == 0


class DeepStreamProbeCallbacks:
    """GStreamer pad probe callbacks for metadata extraction.
    
    Registered on the SGIE output src pad so that both PGIE detection metadata
    AND SGIE ReID tensor metadata are available simultaneously.
    """

    def __init__(
        self,
        kafka_producer: KafkaEventProducer,
        crop_saver: CropSaver,
        kafka_topic: str = "detection-events",
        mtmc_associator: Optional[MTMCAssociator] = None,
        gallery_manager: Optional[PersonGalleryManager] = None,
    ):
        self.kafka_producer = kafka_producer
        self.crop_saver = crop_saver
        self.kafka_topic = kafka_topic
        self.reid_extractor = ReIDFeatureExtractor()
        self.mtmc = mtmc_associator or MTMCAssociator()
        self.gallery_manager = gallery_manager  # May be None if Qdrant unavailable
        self._frame_count = 0

    # ------------------------------------------------------------------
    # Main pad probe callback
    # ------------------------------------------------------------------

    def tracking_src_pad_buffer_probe(self, pad, info, u_data) -> int:
        """Called by GStreamer for every buffer (batch of frames) flowing through the SGIE src pad."""
        if not _PYDS_AVAILABLE:
            logger.warning("pyds not available — probe disabled")
            return GST_PAD_PROBE_OK

        gst_buffer = info.get_buffer()
        if not gst_buffer:
            logger.warning("Unable to get GstBuffer from pad probe info")
            return GST_PAD_PROBE_OK

        batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
        if not batch_meta:
            return GST_PAD_PROBE_OK

        l_frame = batch_meta.frame_meta_list
        active_track_keys = []

        while l_frame is not None:
            try:
                frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
            except StopIteration:
                break

            self._frame_count += 1
            frame_number = frame_meta.frame_num
            camera_id = str(frame_meta.source_id)
            timestamp = datetime.now(timezone.utc).isoformat() + "Z"

            # Map NVMM surface → NumPy array for crop extraction
            frame_np = None
            try:
                frame_np = pyds.get_nvds_buf_surface(hash(gst_buffer), frame_meta.batch_id)
            except Exception as e:
                logger.debug(f"Surface map failed for frame {frame_number}: {e}")

            l_obj = frame_meta.obj_meta_list
            while l_obj is not None:
                try:
                    obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
                except StopIteration:
                    break

                self._process_object(
                    obj_meta=obj_meta,
                    frame_np=frame_np,
                    camera_id=camera_id,
                    frame_number=frame_number,
                    timestamp=timestamp,
                    active_track_keys=active_track_keys,
                )

                try:
                    l_obj = l_obj.next
                except StopIteration:
                    break

            try:
                l_frame = l_frame.next
            except StopIteration:
                break

        # Cleanup stale tracks (prevents unbounded memory growth)
        if self._frame_count % 300 == 0:  # Every 300 frames ≈ 10 seconds @ 30 fps
            self.mtmc.cleanup_lost_tracks(active_track_keys)

        return GST_PAD_PROBE_OK

    # ------------------------------------------------------------------
    # Per-object processing
    # ------------------------------------------------------------------

    def _process_object(
        self,
        obj_meta,
        frame_np,
        camera_id: str,
        frame_number: int,
        timestamp: str,
        active_track_keys: list,
    ):
        class_id = obj_meta.class_id
        object_type = CLASS_MAPPING.get(class_id, "unknown")
        confidence = float(obj_meta.confidence)
        tracking_id = int(obj_meta.object_id)
        bbox = obj_meta.rect_params

        active_track_keys.append((camera_id, tracking_id))

        # 1. Extract ReID embedding (persons only)
        embedding: list = []
        person_uuid: Optional[str] = None

        if class_id == 0:  # person
            embedding = self.reid_extractor.extract(obj_meta) or []
            if embedding:
                # MTMC: resolve local track_id → global person_uuid
                person_uuid, is_new = self.mtmc.associate(camera_id, tracking_id, embedding)
                # Persist embedding to Qdrant asynchronously (gallery manager handles skip if None)
                if self.gallery_manager:
                    try:
                        self.gallery_manager.upsert_embedding(
                            person_uuid=person_uuid,
                            embedding=embedding,
                            payload={"camera_id": camera_id, "timestamp": timestamp},
                        )
                    except Exception as e:
                        logger.debug(f"Qdrant upsert skipped: {e}")

        # 2. Save crop asynchronously to MinIO
        crop_path = ""
        if frame_np is not None:
            crop_path = self.crop_saver.save_crop_async(frame_np, bbox, object_type)

        # 3. Build and publish Kafka event
        event = TrackingEvent(
            event_id=f"{camera_id}_{frame_number}_{tracking_id}_{class_id}",
            timestamp=timestamp,
            camera_id=camera_id,
            frame_number=frame_number,
            detection=DetectionPayload(
                class_id=class_id,
                type=object_type,
                confidence=confidence,
                tracking_id=tracking_id,
                bbox=BoundingBox(
                    left=float(bbox.left),
                    top=float(bbox.top),
                    width=float(bbox.width),
                    height=float(bbox.height),
                ),
                embedding=embedding,
                crop_path=crop_path,
            ),
        )

        # Add person_uuid to payload if resolved
        if person_uuid:
            event_dict = event.to_dict()
            event_dict["detection"]["person_uuid"] = person_uuid
        else:
            event_dict = event.to_dict()

        kafka_key = f"{camera_id}_{tracking_id}"
        self.kafka_producer.send_event(
            topic=self.kafka_topic,
            key=kafka_key,
            event_data=event_dict,
        )
