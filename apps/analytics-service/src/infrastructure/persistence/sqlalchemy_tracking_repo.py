import uuid
from typing import Any, List, Optional, cast
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from packages.domain.entities.tracking_event import TrackingEvent, BoundingBox
from infrastructure.persistence.models import TrackingEventModel

class SqlAlchemyTrackingRepository:
    """SQLAlchemy Repository implementation handling TrackingEvent entities."""
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_event(self, event: TrackingEvent) -> TrackingEvent:
        """Persists a new TrackingEvent entity.
        Note: Transaction commits are managed by the orchestrator unit-of-work.
        """
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

    async def get_recent_events(self, limit: int = 50, before: Optional[datetime] = None) -> List[TrackingEvent]:
        """Fetches the most recent tracking logs."""
        stmt = select(TrackingEventModel)
        if before is not None:
            stmt = stmt.where(TrackingEventModel.timestamp < before)
        stmt = stmt.order_by(TrackingEventModel.timestamp.desc()).limit(limit)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    def _to_entity(self, model: TrackingEventModel) -> TrackingEvent:
        """Maps persistent model back to clean domain entity."""
        model_any = cast(Any, model)
        return TrackingEvent(
            id=model_any.id,
            person_id=model_any.person_id,
            camera_id=model_any.camera_id,
            confidence=model_any.confidence,
            crop_path=model_any.crop_path,
            timestamp=model_any.timestamp,
            bbox=BoundingBox(
                left=model_any.bbox_left,
                top=model_any.bbox_top,
                width=model_any.bbox_width,
                height=model_any.bbox_height
            )
        )
