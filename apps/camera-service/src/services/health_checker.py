import asyncio
import logging
import re
import socket
from typing import Tuple
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config.settings import settings
from services.camera_service import CameraService

logger = logging.getLogger("camera_service.health_checker")

class RtspHealthChecker:
    """Background service to continuously monitor and update RTSP feed connectivity status."""
    def __init__(self, db_session_maker: async_sessionmaker):
        self.session_maker = db_session_maker
        self.running = False

    def _parse_rtsp_host_port(self, rtsp_url: str) -> Tuple[str, int]:
        """Helper to extract IP/Domain and Port from an RTSP URL."""
        try:
            # Clean protocol prefix for parsing if urlparse fails
            parsed = urlparse(rtsp_url)
            netloc = parsed.netloc
            if not netloc and "rtsp://" in rtsp_url:
                netloc = rtsp_url.split("rtsp://")[1].split("/")[0]

            if "@" in netloc: # Contains credentials user:pass@host:port
                netloc = netloc.split("@")[1]

            if ":" in netloc:
                host, port_str = netloc.split(":")
                return host, int(port_str)
            else:
                return netloc, 554 # Default RTSP port
        except Exception as e:
            logger.error(f"Failed to parse RTSP URL {rtsp_url}: {e}")
            return "", 554

    async def probe_socket(self, host: str, port: int, timeout: float = 2.0) -> bool:
        """Asynchronously probes connection to host and port."""
        if not host:
            return False
        try:
            # Use asyncio to check port connection
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=timeout
            )
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False

    async def _check_camera(self, camera, service: CameraService):
        """Probes a single camera and updates database status if changed."""
        host, port = self._parse_rtsp_host_port(camera.rtsp_url)
        is_online = await self.probe_socket(host, port)
        new_status = "CONNECTED" if is_online else "DISCONNECTED"
        
        if camera.status != new_status:
            logger.info(f"Camera {camera.name} ({camera.id}) status changed: {camera.status} -> {new_status}")
            await service.update_status(camera.id, new_status)

    async def start_monitoring(self):
        """Infinite health checking loop executing checks concurrently."""
        self.running = True
        logger.info(f"RTSP Health Checker loop started (Interval: {settings.HEALTH_CHECK_INTERVAL_SECONDS}s)")
        
        while self.running:
            try:
                # Open separate database session for each batch check
                async with self.session_maker() as session:
                    service = CameraService(session)
                    cameras = await service.list_all_cameras()
                    
                    # Spawn concurrent tasks for all cameras
                    tasks = [self._check_camera(camera, service) for camera in cameras]
                    await asyncio.gather(*tasks)
            except Exception as e:
                logger.error(f"Error occurred in health checking batch: {e}")
                
            await asyncio.sleep(settings.HEALTH_CHECK_INTERVAL_SECONDS)

    def stop(self):
        """Halts the checker loop."""
        self.running = False
