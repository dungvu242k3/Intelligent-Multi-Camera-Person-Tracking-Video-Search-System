import io
import logging
from minio import Minio
from minio.error import S3Error

logger = logging.getLogger("ai_service.minio")

class MinioStorageClient:
    """Wrapper around Minio Python SDK for uploading object crops and video clips."""
    def __init__(self, endpoint: str, access_key: str, secret_key: str, secure: bool = False):
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        logger.info(f"MinIO client initialized for endpoint: {endpoint}")

    def ensure_bucket(self, bucket_name: str):
        """Creates the bucket if it does not exist."""
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                logger.info(f"Created MinIO bucket: {bucket_name}")
        except S3Error as e:
            logger.error(f"Failed to check or create bucket {bucket_name}: {e}")
            raise e

    def upload_bytes(self, bucket_name: str, object_name: str, data: bytes, content_type: str = "image/jpeg") -> str:
        """Uploads raw bytes to a bucket and returns the object name/path."""
        try:
            self.ensure_bucket(bucket_name)
            data_stream = io.BytesIO(data)
            self.client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=data_stream,
                length=len(data),
                content_type=content_type
            )
            # Return relative path bucket_name/object_name
            return f"{bucket_name}/{object_name}"
        except Exception as e:
            logger.error(f"Failed to upload object {object_name} to bucket {bucket_name}: {e}")
            raise e
