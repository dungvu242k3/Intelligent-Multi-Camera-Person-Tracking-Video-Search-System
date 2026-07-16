"""
Pydantic schemas for DeepStream detection & tracking events published to Kafka.
Used by downstream consumers (gateway, search-service, analytics) for validation.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Optional
import json


@dataclass
class BoundingBox:
    left: float
    top: float
    width: float
    height: float

    @property
    def x_max(self) -> float:
        return self.left + self.width

    @property
    def y_max(self) -> float:
        return self.top + self.height

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DetectionPayload:
    class_id: int
    type: str                    # "person" | "fire" | "smoke" | "object"
    confidence: float
    tracking_id: int
    bbox: BoundingBox
    embedding: List[float] = field(default_factory=list)
    crop_path: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["bbox"] = self.bbox.to_dict()
        return d


@dataclass
class TrackingEvent:
    """Top-level event schema published to Kafka topic `detection-events`."""
    event_id: str
    timestamp: str               # ISO-8601 UTC
    camera_id: str
    frame_number: int
    detection: DetectionPayload

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "camera_id": self.camera_id,
            "frame_number": self.frame_number,
            "detection": self.detection.to_dict(),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class HealthEvent:
    """Periodic health-check event published to Kafka topic `pipeline-health`."""
    service: str = "ai-service"
    status: str = "running"          # "running" | "degraded" | "stopped"
    gpu_util_pct: float = 0.0
    gpu_mem_used_mb: float = 0.0
    active_sources: int = 0
    frames_processed: int = 0

    def to_json(self) -> str:
        return json.dumps(asdict(self))
