import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.persistence.database import get_db_session
from infrastructure.persistence.sqlalchemy_tracking_repo import SqlAlchemyTrackingRepository
from packages.contracts.dto.tracking import TrackingEventResponse, PersonTrailResponse

router = APIRouter(prefix="/tracking", tags=["tracking"])

@router.get("/events", response_model=List[TrackingEventResponse])
async def get_recent_tracking_events(
    limit: int = 50,
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieves the most recent tracking event logs."""
    repo = SqlAlchemyTrackingRepository(db)
    events = await repo.get_recent_events(limit=limit)
    
    # Map domain entities to DTO responses
    response = []
    for ev in events:
        response.append(
            TrackingEventResponse(
                id=str(ev.id),
                person_id=str(ev.person_id) if ev.person_id else None,
                camera_id=str(ev.camera_id),
                confidence=ev.confidence,
                bbox={
                    "left": ev.bbox.left,
                    "top": ev.bbox.top,
                    "width": ev.bbox.width,
                    "height": ev.bbox.height
                },
                crop_path=ev.crop_path,
                timestamp=ev.timestamp.isoformat() + "Z"
            )
        )
    return response

@router.get("/trail/{person_id}", response_model=PersonTrailResponse)
async def get_person_trail(
    person_id: str,
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
        points.append({
            "event_id": str(ev.id),
            "camera_id": str(ev.camera_id),
            "timestamp": ev.timestamp.isoformat() + "Z",
            "bbox": {
                "left": ev.bbox.left,
                "top": ev.bbox.top,
                "width": ev.bbox.width,
                "height": ev.bbox.height
            },
            "crop_path": ev.crop_path
        })

    return PersonTrailResponse(
        person_id=person_id,
        trail_points=points
    )
