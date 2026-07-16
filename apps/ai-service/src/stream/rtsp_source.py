import logging
import socket
from typing import Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger("ai_service.stream.rtsp_source")

class RTSPSource:
    """Represents a single RTSP Camera Source and monitors its physical network connectivity."""

    def __init__(self, camera_id: str, uri: str, name: str = "camera"):
        self.camera_id = camera_id
        self.uri = uri
        self.name = name
        self.is_active = True
        self.last_status = "unknown"
        
        # Parse target host and port to perform lightweight TCP connectivity checks
        self.host, self.port = self._parse_uri(uri)

    def _parse_uri(self, uri: str) -> Tuple[Optional[str], int]:
        """Extracts the hostname and port from the RTSP URI for network socket verification.
        
        Args:
            uri: The raw RTSP connection string.
            
        Returns:
            A tuple containing the target hostname (or None if invalid) and the port number.
        """
        try:
            # Handle standard rtsp:// or rtsps:// schemes
            parsed = urlparse(uri)
            host = parsed.hostname
            # Default RTSP port is 554
            port = parsed.port if parsed.port is not None else 554
            return host, port
        except Exception as e:
            logger.error(
                f"Failed to parse RTSP URI '{uri}' for camera '{self.name}' (ID: {self.camera_id}): {e}"
            )
            return None, 554

    def check_connectivity(self, timeout_seconds: float = 2.0) -> bool:
        """Performs a lightweight TCP handshake check on the RTSP port to verify network availability.
        
        This prevents blocking the GStreamer/DeepStream pipeline threads on dead/unresponsive sockets.
        
        Args:
            timeout_seconds: Socket timeout limit in seconds.
            
        Returns:
            True if the camera socket responds, False otherwise.
        """
        if not self.host:
            self.last_status = "invalid_uri"
            return False

        try:
            # Standard socket TCP connect test
            with socket.create_connection((self.host, self.port), timeout=timeout_seconds):
                self.last_status = "connected"
                return True
        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            logger.warning(
                f"Camera '{self.name}' ({self.camera_id}) is unreachable at {self.host}:{self.port} - Error: {e}"
            )
            self.last_status = "offline"
            return False

    def to_dict(self) -> dict:
        """Serializes current status metadata for monitoring/health endpoints."""
        return {
            "camera_id": self.camera_id,
            "name": self.name,
            "uri": self.uri,
            "status": self.last_status,
            "is_active": self.is_active
        }
