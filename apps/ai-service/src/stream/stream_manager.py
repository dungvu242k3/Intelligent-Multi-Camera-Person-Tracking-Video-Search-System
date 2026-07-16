import asyncio
import logging
from typing import Callable, Dict, Optional, Any
from .rtsp_source import RTSPSource

logger = logging.getLogger("ai_service.stream.stream_manager")

class StreamManager:
    """Manages the collection of RTSP camera streams and orchestrates their connection health checks.
    
    Adheres to robust concurrent execution patterns to prevent socket I/O from blocking the asyncio event loop.
    """

    def __init__(self, check_interval_seconds: float = 30.0):
        self.sources: Dict[str, RTSPSource] = {}
        self.check_interval_seconds = check_interval_seconds
        self._watchdog_task: Optional[asyncio.Task] = None
        self._on_disconnect_callback: Optional[Callable[[str], Any]] = None

    def register_source(self, camera_id: str, uri: str, name: str = "camera") -> RTSPSource:
        """Registers a camera source metadata descriptor.
        
        Args:
            camera_id: Unique string identifier for the camera.
            uri: RTSP address of the camera stream.
            name: Human-readable name/label.
            
        Returns:
            The created RTSPSource instance.
        """
        source = RTSPSource(camera_id, uri, name)
        self.sources[camera_id] = source
        logger.info(f"Registered camera stream source '{name}' (ID: {camera_id}) -> {uri}")
        return source

    def deregister_source(self, camera_id: str) -> Optional[RTSPSource]:
        """Deregisters a camera source descriptor.
        
        Args:
            camera_id: Unique string identifier for the camera to remove.
            
        Returns:
            The removed RTSPSource instance if found, otherwise None.
        """
        source = self.sources.pop(camera_id, None)
        if source:
            logger.info(f"Deregistered camera stream source '{source.name}' (ID: {camera_id})")
        return source

    def get_source(self, camera_id: str) -> Optional[RTSPSource]:
        """Retrieves a registered camera source."""
        return self.sources.get(camera_id)

    def register_disconnect_callback(self, callback: Callable[[str], Any]) -> None:
        """Registers a handler callback to be invoked when a stream falls offline.
        
        Args:
            callback: The callback function receiving the camera_id as its parameter.
        """
        self._on_disconnect_callback = callback

    async def start_watchdog(self) -> None:
        """Spawns the background asyncio watchdog loop to monitor network connections of camera endpoints."""
        if self._watchdog_task and not self._watchdog_task.done():
            logger.warning("Watchdog monitoring task is already running.")
            return

        self._watchdog_task = asyncio.create_task(self._run_watchdog())
        logger.info(f"Started connection watchdog. Scan interval: {self.check_interval_seconds}s")

    async def stop_watchdog(self) -> None:
        """Stops and cancels the running watchdog task."""
        if self._watchdog_task:
            self._watchdog_task.cancel()
            try:
                await self._watchdog_task
            except asyncio.CancelledError:
                pass
            self._watchdog_task = None
            logger.info("Stopped connection watchdog task.")

    async def _run_watchdog(self) -> None:
        """Infinite loop performing non-blocking connection checks in a background execution pool."""
        loop = asyncio.get_running_loop()
        
        while True:
            try:
                await asyncio.sleep(self.check_interval_seconds)
                for camera_id, source in list(self.sources.items()):
                    if not source.is_active:
                        continue
                    
                    # Run socket check in thread pool since socket.create_connection is blocking
                    is_reachable = await loop.run_in_executor(None, source.check_connectivity)
                    
                    if not is_reachable:
                        logger.error(
                            f"RTSP stream health check failed for '{source.name}' (ID: {camera_id}). Source offline."
                        )
                        if self._on_disconnect_callback:
                            try:
                                # Execute the callback. Supports both sync and async callbacks.
                                if asyncio.iscoroutinefunction(self._on_disconnect_callback):
                                    await self._on_disconnect_callback(camera_id)
                                else:
                                    self._on_disconnect_callback(camera_id)
                            except Exception as cb_err:
                                logger.error(f"Error execution disconnect callback for {camera_id}: {cb_err}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in watchdog runtime loop: {e}", exc_info=True)
