"""
Spatial constraint validation for multi-camera tracking.
Filters impossible cross-camera associations based on geographic distance and time.

Real-world constraint:
- If a person was seen at Camera A at time T, they cannot appear at Camera B
  unless enough travel time has elapsed (based on physical camera distance).
"""
from __future__ import annotations
import logging
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger("ai_service.spatial")


@dataclass
class CameraLocation:
    camera_id: str
    lat: float
    lon: float
    building: Optional[str] = None
    floor: Optional[int] = None


class SpatialConstraintValidator:
    """Validates if a cross-camera re-identification is spatially feasible.
    
    Uses Haversine distance and a configurable max human walking speed
    to determine if a person could physically appear at the new camera.
    
    NOTE: This is a secondary validation layer. The primary ReID match
    (cosine similarity) is still required.
    """

    # Average human walking speed 1.4 m/s ≈ 5 km/h
    DEFAULT_MAX_SPEED_MPS = 3.0  # Allow up to ~10 km/h (fast walk / light jog)

    def __init__(
        self,
        camera_locations: Optional[Dict[str, CameraLocation]] = None,
        max_speed_mps: float = DEFAULT_MAX_SPEED_MPS,
    ):
        self._locations: Dict[str, CameraLocation] = camera_locations or {}
        self.max_speed_mps = max_speed_mps

    def register_camera(self, location: CameraLocation):
        self._locations[location.camera_id] = location

    def is_feasible(
        self,
        from_camera: str,
        from_timestamp: str,
        to_camera: str,
        to_timestamp: str,
    ) -> bool:
        """Returns True if a cross-camera transition is physically possible."""
        if from_camera == to_camera:
            return True  # Same camera is always feasible

        loc_a = self._locations.get(from_camera)
        loc_b = self._locations.get(to_camera)

        if not loc_a or not loc_b:
            # No GPS data registered — allow association
            return True

        try:
            t1 = datetime.fromisoformat(from_timestamp.replace("Z", "+00:00"))
            t2 = datetime.fromisoformat(to_timestamp.replace("Z", "+00:00"))
            elapsed_s = abs((t2 - t1).total_seconds())
        except Exception:
            return True  # Parse error → allow

        distance_m = self._haversine_m(loc_a.lat, loc_a.lon, loc_b.lat, loc_b.lon)
        min_travel_s = distance_m / self.max_speed_mps

        feasible = elapsed_s >= min_travel_s
        if not feasible:
            logger.debug(
                f"Spatial constraint violation: {from_camera}→{to_camera} "
                f"distance={distance_m:.1f}m elapsed={elapsed_s:.1f}s "
                f"required>={min_travel_s:.1f}s"
            )
        return feasible

    @staticmethod
    def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine formula — returns distance in metres."""
        import math
        R = 6_371_000  # Earth radius in metres
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return 2 * R * math.asin(math.sqrt(a))
