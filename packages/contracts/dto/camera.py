from pydantic import BaseModel, Field, field_validator
from typing import Optional, List

class CameraCreate(BaseModel):
    name: str = Field(..., max_length=100)
    rtsp_url: str = Field(..., max_length=500, description="RTSP URL feed pathway")
    location: Optional[str] = Field(None, max_length=255)
    fps: Optional[int] = Field(30, ge=1, le=120)

    @field_validator("rtsp_url")
    @classmethod
    def validate_rtsp_url(cls, v: str) -> str:
        """Ensures RTSP URL uses a valid protocol scheme."""
        v = v.strip()
        if not v.lower().startswith(("rtsp://", "rtsps://")):
            raise ValueError("URL must start with 'rtsp://' or 'rtsps://'")
        return v

class CameraUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=255)
    fps: Optional[int] = Field(None, ge=1, le=120)

class CameraResponse(BaseModel):
    id: str
    name: str
    rtsp_url: str
    location: Optional[str]
    status: str
    fps: int
    created_at: str

class CameraStatusSummaryResponse(BaseModel):
    total: int
    online: int
    offline: int
