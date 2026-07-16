import uuid
from pathlib import PurePath
from typing import List
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from infrastructure.persistence.database import get_db_session
from services.camera_service import CameraService
from packages.contracts.dto.camera import CameraCreate, CameraUpdate, CameraResponse, CameraStatusSummaryResponse
from packages.shared.security import AuthenticatedUser, Role, require_roles
from config.settings import settings

router = APIRouter(prefix="/cameras", tags=["cameras"])
require_admin = require_roles(Role.ADMIN)
require_operator = require_roles(Role.ADMIN, Role.OPERATOR)
VIDEO_UPLOAD_MAX_BYTES = 250 * 1024 * 1024
VIDEO_UPLOAD_CHUNK_BYTES = 1024 * 1024
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov"}
ALLOWED_VIDEO_CONTENT_TYPES = {
    "video/mp4",
    "video/x-msvideo",
    "video/x-matroska",
    "video/quicktime",
    "application/octet-stream",
}


class VideoUrlTestRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        normalized = value.strip()
        parsed = urlparse(normalized)
        if parsed.scheme.lower() not in {"rtsp", "http", "https"} or not parsed.netloc:
            raise ValueError("URL must be a valid rtsp://, http://, or https:// stream URL")
        if any(ch.isspace() for ch in normalized):
            raise ValueError("URL must not contain whitespace")
        return normalized


class VideoTestAcceptedResponse(BaseModel):
    accepted: bool
    job_id: str
    source_type: str
    status: str
    message: str
    filename: str | None = None
    url: str | None = None
    size_bytes: int | None = None

@router.post("", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
async def create_camera(
    data: CameraCreate,
    current_user: AuthenticatedUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session)
):
    """Registers a new camera RTSP stream."""
    service = CameraService(db)
    # Check if duplicate RTSP URL exists
    existing = await service.get_by_rtsp_url(data.rtsp_url)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A camera with this RTSP URL is already registered."
        )
    try:
        camera = await service.create_camera(
            name=data.name,
            rtsp_url=data.rtsp_url,
            location=data.location,
            fps=data.fps or 30
        )
        await db.commit()
        await db.refresh(camera)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A camera with this RTSP URL is already registered."
        )
    return _to_response_dto(camera)

@router.get("", response_model=List[CameraResponse])
async def list_cameras(
    limit: int = Query(default=50, ge=1, le=settings.CAMERA_LIST_MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    current_user: AuthenticatedUser = Depends(require_operator),
    db: AsyncSession = Depends(get_db_session)
):
    """Lists all registered cameras."""
    service = CameraService(db)
    cameras = await service.list_all_cameras(limit=limit, offset=offset)
    return [_to_response_dto(c) for c in cameras]

@router.get("/status-summary", response_model=CameraStatusSummaryResponse)
async def get_status_summary(
    current_user: AuthenticatedUser = Depends(require_operator),
    db: AsyncSession = Depends(get_db_session)
):
    """Fetches stats on online vs offline cameras."""
    service = CameraService(db)
    total, online = await service.get_status_counts()
    offline = total - online
    return CameraStatusSummaryResponse(
        total=total,
        online=online,
        offline=offline
    )


@router.post("/test-url", response_model=VideoTestAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
async def test_video_url(
    data: VideoUrlTestRequest,
    current_user: AuthenticatedUser = Depends(require_operator),
):
    """Validates an operator-submitted stream URL for video analysis testing."""
    return VideoTestAcceptedResponse(
        accepted=True,
        job_id=str(uuid.uuid4()),
        source_type="url",
        status="accepted",
        message="Video URL accepted for analysis validation.",
        url=data.url,
    )


@router.post("/test-video", response_model=VideoTestAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
async def test_video_file(
    file: UploadFile = File(...),
    current_user: AuthenticatedUser = Depends(require_operator),
):
    """Validates an uploaded video payload for analysis testing without loading it into memory."""
    filename = PurePath(file.filename or "").name
    suffix = PurePath(filename).suffix.lower()
    if suffix not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported video file extension.",
        )

    if file.content_type not in ALLOWED_VIDEO_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported video content type.",
        )

    size_bytes = 0
    try:
        while True:
            chunk = await file.read(VIDEO_UPLOAD_CHUNK_BYTES)
            if not chunk:
                break
            size_bytes += len(chunk)
            if size_bytes > VIDEO_UPLOAD_MAX_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Video file exceeds the 250MB upload limit.",
                )
    finally:
        await file.close()

    if size_bytes == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded video file is empty.",
        )

    return VideoTestAcceptedResponse(
        accepted=True,
        job_id=str(uuid.uuid4()),
        source_type="file",
        status="accepted",
        message="Video file accepted for analysis validation.",
        filename=filename,
        size_bytes=size_bytes,
    )

@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: str,
    current_user: AuthenticatedUser = Depends(require_operator),
    db: AsyncSession = Depends(get_db_session)
):
    """Fetches a specific camera configuration by ID."""
    try:
        c_uuid = uuid.UUID(camera_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid camera ID format")
        
    service = CameraService(db)
    camera = await service.get_by_id(c_uuid)
    if not camera:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
    return _to_response_dto(camera)

@router.put("/{camera_id}", response_model=CameraResponse)
async def update_camera(
    camera_id: str,
    data: CameraUpdate,
    current_user: AuthenticatedUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session)
):
    """Updates fields on an existing camera."""
    try:
        c_uuid = uuid.UUID(camera_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid camera ID format")
        
    service = CameraService(db)
    camera = await service.update_camera(
        camera_id=c_uuid,
        name=data.name,
        location=data.location,
        fps=data.fps
    )
    if not camera:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
    await db.commit()
    await db.refresh(camera)
    return _to_response_dto(camera)

@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(
    camera_id: str,
    current_user: AuthenticatedUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session)
):
    """Removes a camera registration."""
    try:
        c_uuid = uuid.UUID(camera_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid camera ID format")
        
    service = CameraService(db)
    deleted = await service.delete_camera(c_uuid)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
    await db.commit()
    return

def _to_response_dto(camera) -> CameraResponse:
    """Helper mapping database Camera to CameraResponse DTO."""
    return CameraResponse(
        id=str(camera.id),
        name=camera.name,
        rtsp_url=camera.rtsp_url,
        location=camera.location,
        status=camera.status,
        fps=camera.fps,
        created_at=camera.created_at.isoformat() + "Z"
    )
