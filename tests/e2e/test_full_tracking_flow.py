import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from application.use_cases.process_tracking_event import ProcessTrackingEventUseCase
from packages.domain.entities.person import Person
from events.event_schemas import TrackingEvent, DetectionPayload, BoundingBox

@pytest.mark.asyncio
async def test_end_to_end_tracking_and_db_flow():
    """Simulates end-to-end telemetry event dispatch, usecase ingestion, and db persistence."""
    # Arrange: Mock infrastructure boundaries
    mock_person_repo = AsyncMock()
    mock_tracking_repo = AsyncMock()
    mock_vector_store = AsyncMock()
    mock_kafka_producer = MagicMock()

    camera_id = uuid.uuid4()
    person_id = uuid.uuid4()
    event_id = str(uuid.uuid4())

    # Set mock behavior
    mock_vector_store.search_similar.return_value = [
        {"person_id": person_id, "score": 0.88, "payload": {"name": "Identified Subject"}}
    ]
    mock_person_repo.get_by_id.return_value = Person(
        id=person_id,
        first_seen=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc)
    )

    # Instantiate Clean Arch UseCase
    usecase = ProcessTrackingEventUseCase(
        person_repo=mock_person_repo,
        tracking_repo=mock_tracking_repo,
        vector_store=mock_vector_store,
        kafka_producer=mock_kafka_producer
    )

    # Construct DeepStream Event Payload simulation
    raw_event = {
        "event_id": event_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "camera_id": str(camera_id),
        "frame_number": 512,
        "detection": {
            "type": "person",
            "confidence": 0.94,
            "bbox": {"left": 20.0, "top": 30.0, "width": 80.0, "height": 180.0},
            "embedding": [0.0] * 512,
            "crop_path": "crops/cam_0/person_42.jpg"
        }
    }

    # Act: Run usecase (emulating the consumer listener)
    await usecase.execute(raw_event)

    # Assert: Verify database interactions
    mock_vector_store.search_similar.assert_called_once()
    mock_person_repo.get_by_id.assert_called_once_with(person_id, for_update=True)
    mock_person_repo.upsert_person.assert_called_once()
    mock_tracking_repo.save_event.assert_called_once()
