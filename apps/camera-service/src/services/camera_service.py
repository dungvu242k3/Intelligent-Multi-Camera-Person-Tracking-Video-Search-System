import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
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
        await self.db.commit()
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

    async def list_all_cameras(self) -> List[Camera]:
        """Returns all registered camera feeds."""
        result = await self.db.execute(select(Camera))
        return list(result.scalars().all())

    async def update_camera(self, camera_id: uuid.UUID, name: Optional[str] = None, location: Optional[str] = None, fps: Optional[int] = None) -> Optional[Camera]:
        """Modifies camera settings."""
        camera = await self.get_by_id(camera_id)
        if not camera:
            return None
        
        if name is not None:
            camera.name = name
        if location is not None:
            camera.location = location
        if fps is not None:
            camera.fps = fps
            
        await self.db.commit()
        await self.db.refresh(camera)
        return camera

    async def update_status(self, camera_id: uuid.UUID, status: str) -> Optional[Camera]:
        """Directly updates a camera's connection status (CONNECTED, DISCONNECTED, etc.)."""
        camera = await self.get_by_id(camera_id)
        if not camera:
            return None
        camera.status = status
        await self.db.commit()
        return camera

    async def delete_camera(self, camera_id: uuid.UUID) -> bool:
        """Deletes a camera registration."""
        camera = await self.get_by_id(camera_id)
        if not camera:
            return False
        await self.db.delete(camera)
        await self.db.commit()
        return True
