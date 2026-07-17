# ruff: noqa: E402
import sys
import os
from unittest.mock import MagicMock
# Mock cv2 before importing GStreamer/Callbacks
sys.modules['cv2'] = MagicMock()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../apps/analytics-service/src")))

import pytest
import uuid
from unittest.mock import AsyncMock
from datetime import datetime, timezone

from application.use_cases.process_tracking_event import ProcessTrackingEventUseCase
from packages.domain.entities.person import Person

@pytest.mark.asyncio
async def test_full_person_detection_flow_e2e():
    """Simulates a full end-to-end person detection flow and checks mapping logic."""
    # Arrange
    mock_person_repo = AsyncMock()
    mock_tracking_repo = AsyncMock()
    mock_vector_store = AsyncMock()
    mock_kafka_producer = MagicMock()

    camera_id = uuid.uuid4()
    existing_person_id = uuid.uuid4()

    # Configure mock person repo to return an existing person when requested
    first_seen = datetime.now(timezone.utc)
    existing_person = Person(id=existing_person_id, first_seen=first_seen, last_seen=first_seen)
    mock_person_repo.get_by_id.return_value = existing_person

    # Simulating Qdrant vector search matching the existing person
    mock_vector_store.search_similar.return_value = [
        {"person_id": existing_person_id, "score": 0.92}
    ]

    usecase = ProcessTrackingEventUseCase(
        person_repo=mock_person_repo,
        tracking_repo=mock_tracking_repo,
        vector_store=mock_vector_store,
        kafka_producer=mock_kafka_producer
    )

    event_payload = {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "camera_id": str(camera_id),
        "frame_number": 2048,
        "detection": {
            "type": "person",
            "confidence": 0.96,
            "bbox": {"left": 100.0, "top": 200.0, "width": 80.0, "height": 160.0},
            "embedding": [0.15] * 512,
            "crop_path": f"crops/{camera_id}/person_{existing_person_id}.jpg"
        }
    }

    # Act
    await usecase.execute(event_payload)

    # Assert
    # 1. Similarity search was called with correct embedding
    mock_vector_store.search_similar.assert_called_once_with(
        embedding=[0.15] * 512,
        limit=1,
        score_threshold=0.75
    )

    # 2. Person repo retrieved the matched person and locked the row
    mock_person_repo.get_by_id.assert_called_once_with(existing_person_id, for_update=True)

    # 3. Person repo saved/updated the person entity
    mock_person_repo.upsert_person.assert_called_once()
    upserted_person = mock_person_repo.upsert_person.call_args[0][0]
    assert upserted_person.id == existing_person_id
    assert upserted_person.total_appearances == 2  # Incremented

    # 4. Tracking event repo persisted the tracking trace log
    mock_tracking_repo.save_event.assert_called_once()
    saved_event = mock_tracking_repo.save_event.call_args[0][0]
    assert saved_event.person_id == existing_person_id
    assert saved_event.camera_id == camera_id
    assert saved_event.confidence == 0.96
    assert saved_event.bbox.left == 100.0
