from pydantic import BaseModel
from typing import Optional, List

class BBoxDTO(BaseModel):
    left: float
    top: float
    width: float
    height: float

class TrackingEventResponse(BaseModel):
    id: str
    person_id: Optional[str]
    camera_id: str
    confidence: float
    bbox: BBoxDTO
    crop_path: Optional[str]
    timestamp: str

class TrailPointDTO(BaseModel):
    event_id: str
    camera_id: str
    timestamp: str
    bbox: BBoxDTO
    crop_path: Optional[str]

class PersonTrailResponse(BaseModel):
    person_id: str
    trail_points: List[TrailPointDTO]
