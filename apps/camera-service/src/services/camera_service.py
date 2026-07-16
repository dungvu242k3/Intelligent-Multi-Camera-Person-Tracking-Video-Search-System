import uuid
from typing import Any, List, Optional, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from models.camera import Camera

class CameraService:
    """Handles core CRUD database operations and status management for cameras."""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_camera(self, name: str, rtsp_url: str, location: Optional[str] = None, fps: int = 30) -> Camera:
        """Registers a new camera feed."""
        camera = Camera(
            name=name,
            rtsp_url=rtsp_url,
            location=location,
            fps=fps,
            status="DISCONNECTED"
        )
        self.db.add(camera)
        await self.db.flush()
        await self.db.refresh(camera)
        return camera

    async def get_by_id(self, camera_id: uuid.UUID) -> Optional[Camera]:
        """Fetches camera info by ID."""
        result = await self.db.execute(select(Camera).where(Camera.id == camera_id))
        return result.scalar_one_or_none()

    async def get_by_rtsp_url(self, rtsp_url: str) -> Optional[Camera]:
        """Fetches camera info by RTSP URL (to prevent duplicates)."""
        result = await self.db.execute(select(Camera).where(Camera.rtsp_url == rtsp_url))
        return result.scalar_one_or_none()

    async def list_all_cameras(self, limit: Optional[int] = None, offset: int = 0) -> List[Camera]:
        """Returns all registered camera feeds."""
        stmt = select(Camera).order_by(Camera.created_at.desc(), Camera.id).offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_status_counts(self) -> tuple[int, int]:
        """Returns total and connected camera counts without loading all rows."""
        total_result = await self.db.execute(select(func.count(Camera.id)))
        online_result = await self.db.execute(
            select(func.count(Camera.id)).where(Camera.status == "CONNECTED")
        )
        return int(total_result.scalar_one()), int(online_result.scalar_one())

    async def update_camera(self, camera_id: uuid.UUID, name: Optional[str] = None, location: Optional[str] = None, fps: Optional[int] = None) -> Optional[Camera]:
        """Modifies camera settings."""
        camera = await self.get_by_id(camera_id)
        if not camera:
            return None
        
        if name is not None:
            cast(Any, camera).name = name
        if location is not None:
            cast(Any, camera).location = location
        if fps is not None:
            cast(Any, camera).fps = fps
            
        await self.db.flush()
        await self.db.refresh(camera)
        return camera

    async def update_status(self, camera_id: uuid.UUID, status: str) -> Optional[Camera]:
        """Directly updates a camera's connection status (CONNECTED, DISCONNECTED, etc.)."""
        camera = await self.get_by_id(camera_id)
        if not camera:
            return None
        cast(Any, camera).status = status
        await self.db.flush()
        return camera

    async def delete_camera(self, camera_id: uuid.UUID) -> bool:
        """Deletes a camera registration."""
        camera = await self.get_by_id(camera_id)
        if not camera:
            return False
        await self.db.delete(camera)
        await self.db.flush()
        return True
