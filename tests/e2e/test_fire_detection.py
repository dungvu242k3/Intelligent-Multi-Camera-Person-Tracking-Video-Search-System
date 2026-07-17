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

@pytest.mark.asyncio
async def test_fire_detection_triggers_critical_alert_e2e():
    """Simulates a fire/smoke detection pipeline event triggering emergency alerts."""
    # Arrange
    mock_person_repo = AsyncMock()
    mock_tracking_repo = MagicMock()
    mock_vector_store = AsyncMock()
    mock_kafka_producer = MagicMock()

    usecase = ProcessTrackingEventUseCase(
        person_repo=mock_person_repo,
        tracking_repo=mock_tracking_repo,
        vector_store=mock_vector_store,
        kafka_producer=mock_kafka_producer
    )

    camera_id = uuid.uuid4()
    event_payload = {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "camera_id": str(camera_id),
        "frame_number": 1024,
        "detection": {
            "type": "smoke",
            "confidence": 0.88,
            "bbox": {"left": 50.0, "top": 60.0, "width": 100.0, "height": 100.0},
            "crop_path": "crops/cam_2/smoke_alarm.jpg"
        }
    }

    # Act
    await usecase.execute(event_payload)

    # Assert
    # 1. No person DB operations or vector storage queries should happen for fires
    mock_person_repo.get_by_id.assert_not_called()
    mock_vector_store.search_similar.assert_not_called()

    # 2. Alert must be published directly to alert-events Kafka topic
    mock_kafka_producer.send_event.assert_called_once()
    _, kwargs = mock_kafka_producer.send_event.call_args
    assert kwargs["topic"] == "alert-events"
    assert kwargs["key"] == str(camera_id)
    
    alert_payload = kwargs["event_data"]
    assert alert_payload["type"] == "fire"
    assert alert_payload["severity"] == "emergency"
    assert alert_payload["camera_id"] == str(camera_id)
    assert alert_payload["crop_path"] == "crops/cam_2/smoke_alarm.jpg"
    assert "🚨 Cảnh Báo Hỏa Hoạn!" in alert_payload["title"]
