import uuid
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from packages.domain.entities.tracking_event import TrackingEvent, BoundingBox
from apps.analytics-service.src.infrastructure.persistence.models import TrackingEventModel

class SqlAlchemyTrackingRepository:
    """SQLAlchemy Repository implementation handling TrackingEvent entities."""
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_event(self, event: TrackingEvent) -> TrackingEvent:
        """Persists a new TrackingEvent entity."""
        model = TrackingEventModel(
            id=event.id,
            person_id=event.person_id,
            camera_id=event.camera_id,
            bbox_left=event.bbox.left,
            bbox_top=event.bbox.top,
            bbox_width=event.bbox.width,
            bbox_height=event.bbox.height,
            confidence=event.confidence,
            crop_path=event.crop_path,
            timestamp=event.timestamp
        )
        self.session.add(model)
        await self.session.commit()
        return event

    async def get_trail_by_person_id(self, person_id: uuid.UUID) -> List[TrackingEvent]:
        """Retrieves chronological tracking event logs for a given Person."""
        result = await self.session.execute(
            select(TrackingEventModel)
            .where(TrackingEventModel.person_id == person_id)
            .order_by(TrackingEventModel.timestamp.asc())
        )
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def get_recent_events(self, limit: int = 50) -> List[TrackingEvent]:
        """Fetches the most recent tracking logs."""
        result = await self.session.execute(
            select(TrackingEventModel)
            .order_by(TrackingEventModel.timestamp.desc())
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    def _to_entity(self, model: TrackingEventModel) -> TrackingEvent:
        """Maps persistent model back to clean domain entity."""
        return TrackingEvent(
            id=model.id,
            person_id=model.person_id,
            camera_id=model.camera_id,
            confidence=model.confidence,
            crop_path=model.crop_path,
            timestamp=model.timestamp,
            bbox=BoundingBox(
                left=model.bbox_left,
                top=model.bbox_top,
                width=model.bbox_width,
                height=model.bbox_height
            )
        )
