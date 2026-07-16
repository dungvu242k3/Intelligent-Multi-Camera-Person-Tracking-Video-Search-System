import uuid
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, field

@dataclass
class BoundingBox:
    left: float
    top: float
    width: float
    height: float

    def area(self) -> float:
        return self.width * self.height

    def center(self) -> tuple:
        return (self.left + self.width / 2.0, self.top + self.height / 2.0)

    def iou(self, other: 'BoundingBox') -> float:
        """Calculates Intersection over Union (IoU) with another bounding box."""
        x1 = max(self.left, other.left)
        y1 = max(self.top, other.top)
        x2 = min(self.left + self.width, other.left + other.width)
        y2 = min(self.top + self.height, other.top + other.height)

        intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
        union = self.area() + other.area() - intersection
        
        if union <= 0.0:
            return 0.0
        return intersection / union

@dataclass
class TrackingEvent:
    camera_id: uuid.UUID
    confidence: float
    bbox: BoundingBox
    timestamp: datetime
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    person_id: Optional[uuid.UUID] = None
    crop_path: Optional[str] = None
    embedding: List[float] = field(default_factory=list)
