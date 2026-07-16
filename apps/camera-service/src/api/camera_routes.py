import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.persistence.database import get_db_session
from services.camera_service import CameraService
from packages.contracts.dto.camera import CameraCreate, CameraUpdate, CameraResponse, CameraStatusSummaryResponse

router = APIRouter(prefix="/cameras", tags=["cameras"])

@router.post("", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
async def create_camera(
    data: CameraCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Registers a new camera RTSP stream."""
    service = CameraService(db)
    # Check if duplicate RTSP URL exists
    existing = await service.get_by_rtsp_url(data.rtsp_url)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A camera with this RTSP URL is already registered."
        )
    camera = await service.create_camera(
        name=data.name,
        rtsp_url=data.rtsp_url,
        location=data.location,
        fps=data.fps
    )
    return _to_response_dto(camera)

@router.get("", response_model=List[CameraResponse])
async def list_cameras(
    db: AsyncSession = Depends(get_db_session)
):
    """Lists all registered cameras."""
    service = CameraService(db)
    cameras = await service.list_all_cameras()
    return [_to_response_dto(c) for c in cameras]

@router.get("/status-summary", response_model=CameraStatusSummaryResponse)
async def get_status_summary(
    db: AsyncSession = Depends(get_db_session)
):
    """Fetches stats on online vs offline cameras."""
    service = CameraService(db)
    cameras = await service.list_all_cameras()
    total = len(cameras)
    online = sum(1 for c in cameras if c.status == "CONNECTED")
    offline = total - online
    return CameraStatusSummaryResponse(
        total=total,
        online=online,
        offline=offline
    )

@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: str,
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
    return _to_response_dto(camera)

@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(
    camera_id: str,
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
