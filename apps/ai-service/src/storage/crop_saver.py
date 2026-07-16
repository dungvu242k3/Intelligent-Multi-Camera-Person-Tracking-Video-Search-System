import cv2
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor

from packages.shared.storage.minio import MinioStorageClient

logger = logging.getLogger("ai_service.storage")

class CropSaver:
    """Handles async cropping, JPEG encoding, and uploading to MinIO object storage."""
    def __init__(self, minio_client: MinioStorageClient, bucket_name: str = "detection-crops", max_workers: int = 4):
        self.minio_client = minio_client
        self.bucket_name = bucket_name
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        # Ensure bucket exists
        self.minio_client.ensure_bucket(bucket_name)

    def save_crop_async(self, frame_np, bbox, object_type: str) -> str:
        """Saves a bounding box crop asynchronously.
        Returns the prospective object name (UUID-based) immediately.
        """
        object_id = str(uuid.uuid4())
        object_name = f"{object_type}/{object_id}.jpg"
        
        # Submit the crop and upload task to the background worker pool
        # This keeps the GStreamer pad probe thread completely unblocked!
        self.executor.submit(self._crop_encode_upload, frame_np.copy(), bbox, object_name)
        
        return f"{self.bucket_name}/{object_name}"

    def _crop_encode_upload(self, frame_np, bbox, object_name: str):
        """Crops, encodes, and uploads the frame slice to S3."""
        try:
            h, w, _ = frame_np.shape
            # Parse bounding box coordinates (normalized or absolute)
            x_min = max(0, int(bbox.left))
            y_min = max(0, int(bbox.top))
            x_max = min(w, int(bbox.left + bbox.width))
            y_max = min(h, int(bbox.top + bbox.height))

            if x_max <= x_min or y_max <= y_min:
                logger.warning(f"Invalid bounding box size for crop: {bbox}")
                return

            # Crop the sub-image
            crop = frame_np[y_min:y_max, x_min:x_max]
            
            # Encode to JPEG bytes
            success, encoded_img = cv2.imencode(".jpg", crop, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
            if not success:
                logger.error("Failed to encode crop to JPEG format")
                return

            # Upload bytes directly to MinIO
            jpeg_bytes = encoded_img.tobytes()
            self.minio_client.upload_bytes(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=jpeg_bytes,
                content_type="image/jpeg"
            )
            logger.debug(f"Uploaded crop to MinIO: {object_name}")
        except Exception as e:
            logger.error(f"Error during async crop saving for {object_name}: {e}")

    def shutdown(self):
        """Shuts down the worker pool, waiting for pending uploads."""
        self.executor.shutdown(wait=True)
