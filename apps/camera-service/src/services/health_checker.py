import asyncio
import logging
import time
from typing import List, Tuple
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import async_sessionmaker
from config.settings import settings
from services.camera_service import CameraService

logger = logging.getLogger("camera_service.health_checker")

class RtspHealthChecker:
    """Background service to continuously monitor and update RTSP feed connectivity status."""
    def __init__(self, db_session_maker: async_sessionmaker):
        self.session_maker = db_session_maker
        self.running = False
        self._camera_cache: List[object] = []
        self._camera_cache_expires_at = 0.0
        self._semaphore = asyncio.Semaphore(settings.HEALTH_CHECK_MAX_CONCURRENCY)

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

    async def _probe_camera_status(self, camera) -> Tuple[object, str]:
        """Probes a single camera without touching the shared database session."""
        async with self._semaphore:
            host, port = self._parse_rtsp_host_port(camera.rtsp_url)
            is_online = await self.probe_socket(host, port)
            return camera, "CONNECTED" if is_online else "DISCONNECTED"

    async def _load_cameras(self, service: CameraService) -> List[object]:
        now = time.time()
        if now < self._camera_cache_expires_at:
            return self._camera_cache
        cameras: List[object] = list(await service.list_all_cameras(limit=settings.CAMERA_LIST_MAX_LIMIT))
        self._camera_cache = cameras
        self._camera_cache_expires_at = now + max(settings.HEALTH_CHECK_INTERVAL_SECONDS, 1)
        return cameras

    async def start_monitoring(self):
        """Infinite health checking loop executing checks concurrently."""
        self.running = True
        logger.info(f"RTSP Health Checker loop started (Interval: {settings.HEALTH_CHECK_INTERVAL_SECONDS}s)")
        
        while self.running:
            try:
                # Open separate database session for each batch check
                async with self.session_maker() as session:
                    service = CameraService(session)
                    cameras = await self._load_cameras(service)

                    tasks = [self._probe_camera_status(camera) for camera in cameras]
                    results = await asyncio.gather(*tasks)
                    for camera, new_status in results:
                        if camera.status != new_status:
                            logger.info(f"Camera {camera.name} ({camera.id}) status changed: {camera.status} -> {new_status}")
                            await service.update_status(camera.id, new_status)
                    await session.commit()
            except Exception as e:
                logger.error(f"Error occurred in health checking batch: {e}")
                
            await asyncio.sleep(settings.HEALTH_CHECK_INTERVAL_SECONDS)

    def stop(self):
        """Halts the checker loop."""
        self.running = False
