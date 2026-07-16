import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.persistence.database import get_db_session
from infrastructure.persistence.sqlalchemy_tracking_repo import SqlAlchemyTrackingRepository
from packages.contracts.dto.tracking import BBoxDTO, TrailPointDTO, TrackingEventResponse, PersonTrailResponse
from packages.shared.security import AuthenticatedUser, Role, require_roles

router = APIRouter(prefix="/tracking", tags=["tracking"])
require_operator = require_roles(Role.ADMIN, Role.OPERATOR)

@router.get("/events", response_model=List[TrackingEventResponse])
async def get_recent_tracking_events(
    limit: int = Query(default=50, ge=1, le=100, description="Max number of events to return (1-100)"),
    before: str | None = Query(default=None, description="Return events strictly before this ISO-8601 timestamp"),
    current_user: AuthenticatedUser = Depends(require_operator),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieves the most recent tracking event logs."""
    before_dt = None
    if before:
        try:
            before_dt = datetime.fromisoformat(before.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid before timestamp format"
            )
    repo = SqlAlchemyTrackingRepository(db)
    events = await repo.get_recent_events(limit=limit, before=before_dt)
    
    # Map domain entities to DTO responses
    response = []
    for ev in events:
        response.append(
            TrackingEventResponse(
                id=str(ev.id),
                person_id=str(ev.person_id) if ev.person_id else None,
                camera_id=str(ev.camera_id),
                confidence=ev.confidence,
                bbox=BBoxDTO(
                    left=ev.bbox.left,
                    top=ev.bbox.top,
                    width=ev.bbox.width,
                    height=ev.bbox.height
                ),
                crop_path=ev.crop_path,
                timestamp=ev.timestamp.isoformat() + "Z"
            )
        )
    return response

@router.get("/trail/{person_id}", response_model=PersonTrailResponse)
async def get_person_trail(
    person_id: str,
    current_user: AuthenticatedUser = Depends(require_operator),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieves the complete historical trail of a person across all cameras chronologically."""
    try:
        p_uuid = uuid.UUID(person_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid person UUID format"
        )

    repo = SqlAlchemyTrackingRepository(db)
    trail = await repo.get_trail_by_person_id(p_uuid)
    
    if not trail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No tracking trail found for person ID: {person_id}"
        )

    # Compile trail points
    points = []
    for ev in trail:
        points.append(TrailPointDTO(
            event_id=str(ev.id),
            camera_id=str(ev.camera_id),
            timestamp=ev.timestamp.isoformat() + "Z",
            bbox=BBoxDTO(
                left=ev.bbox.left,
                top=ev.bbox.top,
                width=ev.bbox.width,
                height=ev.bbox.height
            ),
            crop_path=ev.crop_path
        ))

    return PersonTrailResponse(
        person_id=person_id,
        trail_points=points
    )
