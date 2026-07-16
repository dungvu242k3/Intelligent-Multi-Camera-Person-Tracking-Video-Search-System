"""
GPU metrics monitoring via pynvml (nvidia-ml-py3).
Runs in a background daemon thread and exposes GPU utilization / memory stats
to the health-check endpoint and periodic Kafka health events.
"""
from __future__ import annotations
import logging
import threading
import time
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("ai_service.gpu_monitor")

try:
    import pynvml
    _NVML_AVAILABLE = True
except ImportError:
    _NVML_AVAILABLE = False
    logger.warning("pynvml not available — GPU monitoring disabled. "
                   "Install nvidia-ml-py3 inside the DeepStream container.")


@dataclass
class GpuStats:
    device_name: str = "N/A"
    gpu_util_pct: float = 0.0
    mem_used_mb: float = 0.0
    mem_total_mb: float = 0.0
    temperature_c: float = 0.0
    power_draw_w: float = 0.0


class GpuMonitor:
    """Polls NVML every `poll_interval_s` seconds and caches latest GPU stats.
    Thread-safe — stats can be read from any thread via `get_stats()`.
    """

    def __init__(self, gpu_index: int = 0, poll_interval_s: float = 5.0):
        self._gpu_index = gpu_index
        self._poll_interval = poll_interval_s
        self._stats = GpuStats()
        self._lock = threading.Lock()
        self._handle = None
        self._running = False
        self._thread: Optional[threading.Thread] = None

        if _NVML_AVAILABLE:
            try:
                pynvml.nvmlInit()
                self._handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_index)
                name = pynvml.nvmlDeviceGetName(self._handle)
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(self._handle)
                with self._lock:
                    self._stats.device_name = name.decode() if isinstance(name, bytes) else name
                    self._stats.mem_total_mb = mem_info.total / (1024 ** 2)
                logger.info(f"GPU Monitor initialised: {self._stats.device_name} "
                            f"({self._stats.mem_total_mb:.0f} MB VRAM)")
            except Exception as e:
                logger.error(f"Failed to init NVML: {e}")
                self._handle = None

    def start(self):
        """Start background polling thread (daemon — exits with the main process)."""
        if not self._handle:
            logger.warning("GPU handle not available — GpuMonitor polling skipped.")
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._poll_loop,
            name="gpu-monitor",
            daemon=True
        )
        self._thread.start()
        logger.info(f"GPU monitoring started (interval={self._poll_interval}s)")

    def stop(self):
        self._running = False
        if _NVML_AVAILABLE and self._handle:
            try:
                pynvml.nvmlShutdown()
            except Exception:
                pass

    def get_stats(self) -> GpuStats:
        """Returns a snapshot of the latest GPU metrics (thread-safe copy)."""
        with self._lock:
            return GpuStats(**self._stats.__dict__)

    def _poll_loop(self):
        while self._running:
            try:
                util = pynvml.nvmlDeviceGetUtilizationRates(self._handle)
                mem = pynvml.nvmlDeviceGetMemoryInfo(self._handle)
                temp = pynvml.nvmlDeviceGetTemperature(
                    self._handle, pynvml.NVML_TEMPERATURE_GPU
                )
                try:
                    power = pynvml.nvmlDeviceGetPowerUsage(self._handle) / 1000.0
                except pynvml.NVMLError:
                    power = 0.0

                with self._lock:
                    self._stats.gpu_util_pct = float(util.gpu)
                    self._stats.mem_used_mb = mem.used / (1024 ** 2)
                    self._stats.temperature_c = float(temp)
                    self._stats.power_draw_w = power

            except Exception as e:
                logger.debug(f"GPU poll error: {e}")

            time.sleep(self._poll_interval)
