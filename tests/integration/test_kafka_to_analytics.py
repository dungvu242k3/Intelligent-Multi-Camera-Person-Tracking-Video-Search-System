import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from application.use_cases.process_tracking_event import ProcessTrackingEventUseCase
from packages.domain.entities.person import Person

@pytest.mark.asyncio
async def test_process_person_tracking_event_flow():
    """Tests use case processing for a person detection event, matching ReID vectors."""
    # Arrange
    mock_person_repo = AsyncMock()
    mock_tracking_repo = AsyncMock()
    mock_vector_store = AsyncMock()
    mock_kafka_producer = MagicMock()

    camera_uuid = uuid.uuid4()
    person_uuid = uuid.uuid4()

    # Setup mock behavior
    mock_vector_store.search_similar.return_value = [
        {"person_id": person_uuid, "score": 0.89}
    ]
    
    mock_person_repo.get_by_id.return_value = Person(
        id=person_uuid, 
        first_seen=datetime.now(timezone.utc), 
        last_seen=datetime.now(timezone.utc)
    )

    usecase = ProcessTrackingEventUseCase(
        person_repo=mock_person_repo,
        tracking_repo=mock_tracking_repo,
        vector_store=mock_vector_store,
        kafka_producer=mock_kafka_producer
    )

    payload = {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "camera_id": str(camera_uuid),
        "frame_number": 100,
        "detection": {
            "type": "person",
            "confidence": 0.95,
            "bbox": {"left": 10.0, "top": 20.0, "width": 100.0, "height": 200.0},
            "embedding": [0.0] * 512,
            "crop_path": "crops/cam1/person_1.jpg"
        }
    }

    # Act
    await usecase.execute(payload)

    # Assert
    mock_vector_store.search_similar.assert_called_once()
    mock_person_repo.get_by_id.assert_called_once_with(person_uuid, for_update=True)
    mock_person_repo.upsert_person.assert_called_once()
    mock_tracking_repo.save_event.assert_called_once()

@pytest.mark.asyncio
async def test_process_fire_event_flow():
    """Tests usecase routing for a critical fire detection event."""
    # Arrange
    mock_person_repo = AsyncMock()
    mock_tracking_repo = AsyncMock()
    mock_vector_store = AsyncMock()
    mock_kafka_producer = MagicMock()

    usecase = ProcessTrackingEventUseCase(
        person_repo=mock_person_repo,
        tracking_repo=mock_tracking_repo,
        vector_store=mock_vector_store,
        kafka_producer=mock_kafka_producer
    )

    camera_uuid = uuid.uuid4()
    payload = {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "camera_id": str(camera_uuid),
        "frame_number": 102,
        "detection": {
            "type": "fire",
            "confidence": 0.98,
            "bbox": {"left": 25.0, "top": 45.0, "width": 80.0, "height": 80.0},
            "crop_path": "crops/cam2/fire_1.jpg"
        }
    }

    # Act
    await usecase.execute(payload)

    # Assert
    # Person repo should NOT be queried on fire alarms
    mock_person_repo.get_by_id.assert_not_called()
    mock_vector_store.search_similar.assert_not_called()
    
    # Kafka producer should emit an alert event
    mock_kafka_producer.send_event.assert_called_once()
