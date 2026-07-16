from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from urllib.parse import urlparse

class CameraCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    rtsp_url: str = Field(..., max_length=500, description="RTSP URL feed pathway")
    location: Optional[str] = Field(None, max_length=255)
    fps: Optional[int] = Field(30, ge=1, le=120)

    @field_validator("name", "location")
    @classmethod
    def strip_text_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("Field cannot be blank")
        return stripped

    @field_validator("rtsp_url")
    @classmethod
    def validate_rtsp_url(cls, v: str) -> str:
        """Ensures RTSP URL uses a valid protocol scheme."""
        v = v.strip()
        if any(ch.isspace() for ch in v):
            raise ValueError("URL must not contain whitespace")
        parsed = urlparse(v)
        if parsed.scheme.lower() not in {"rtsp", "rtsps"}:
            raise ValueError("URL must start with 'rtsp://' or 'rtsps://'")
        if not parsed.hostname:
            raise ValueError("URL must include a hostname")
        if parsed.fragment:
            raise ValueError("URL fragments are not allowed")
        if parsed.port is not None and not (1 <= parsed.port <= 65535):
            raise ValueError("URL port must be between 1 and 65535")
        return v

class CameraUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[str] = Field(None, max_length=255)
    fps: Optional[int] = Field(None, ge=1, le=120)

    @field_validator("name", "location")
    @classmethod
    def strip_text_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("Field cannot be blank")
        return stripped

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
