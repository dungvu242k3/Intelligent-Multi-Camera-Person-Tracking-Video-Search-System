# ruff: noqa: E402
import sys
import os
from unittest.mock import MagicMock
# Mock cv2, asyncpg, and confluent_kafka before importing anything else
sys.modules['cv2'] = MagicMock()
sys.modules['asyncpg'] = MagicMock()
sys.modules['confluent_kafka'] = MagicMock()

# Setup paths to prioritize this service's source and packages
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../apps/analytics-service/src")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../apps/notification-service/src")))

# Evict config modules to prevent collision
sys.modules.pop("config.settings", None)
sys.modules.pop("config", None)

import pytest
import uuid
import json
import asyncio
import importlib.util
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone

# Import targets
from application.use_cases.process_tracking_event import ProcessTrackingEventUseCase

# Dynamically import notification main to avoid 'main' namespace collisions
spec = importlib.util.spec_from_file_location(
    "notification_main",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../apps/notification-service/src/main.py"))
)
notification_main = importlib.util.module_from_spec(spec)
sys.modules["notification_main"] = notification_main
spec.loader.exec_module(notification_main)

from notification_main import consume_alerts, settings as notification_settings

@pytest.mark.asyncio
async def test_fire_event_use_case_publishes_alert_to_kafka():
    """Verifies that a fire detection event routes correctly and publishes to Kafka alert-events."""
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

    camera_uuid = uuid.uuid4()
    payload = {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "camera_id": str(camera_uuid),
        "frame_number": 512,
        "detection": {
            "type": "fire",
            "confidence": 0.99,
            "bbox": {"left": 20.0, "top": 30.0, "width": 100.0, "height": 100.0},
            "crop_path": "crops/cam1/fire_alert.jpg"
        }
    }

    # Act
    await usecase.execute(payload)

    # Assert
    # Person repository and vector search must NOT be touched for fire detections
    mock_person_repo.get_by_id.assert_not_called()
    mock_vector_store.search_similar.assert_not_called()

    # Kafka producer must emit to alert-events
    mock_kafka_producer.send_event.assert_called_once()
    args, kwargs = mock_kafka_producer.send_event.call_args
    assert kwargs.get("topic") == "alert-events"
    assert kwargs.get("key") == str(camera_uuid)
    
    event_data = kwargs.get("event_data")
    assert event_data["type"] == "fire"
    assert event_data["severity"] == "emergency"
    assert event_data["camera_id"] == str(camera_uuid)
    assert event_data["crop_path"] == "crops/cam1/fire_alert.jpg"


@pytest.mark.asyncio
async def test_notification_service_consumes_alert_and_posts_to_gateway():
    """Verifies notification-service alert consumption and gateway forwarding."""
    # We mock the confluent_kafka Consumer/Producer used in main.py of notification-service
    mock_msg = MagicMock()
    mock_msg.error.return_value = None
    
    alert_payload = {
        "alert_id": "test-alert-123",
        "type": "fire",
        "severity": "emergency",
        "title": "🚨 Cảnh Báo Hỏa Hoạn!",
        "description": "Phát hiện dấu hiệu lửa/khói!",
        "camera_id": str(uuid.uuid4()),
        "crop_path": "crops/cam1/fire_alert.jpg",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    mock_msg.value.return_value = json.dumps(alert_payload).encode('utf-8')
    mock_msg.key.return_value = b"cam_1"
    mock_msg.partition.return_value = 0
    mock_msg.offset.return_value = 100

    # Mock the consumer.poll method to yield the mock message once, then None to stop
    mock_consumer = MagicMock()
    poll_calls = [mock_msg, None]
    
    def mock_poll(*args, **kwargs):
        if poll_calls:
            return poll_calls.pop(0)
        return None
    mock_consumer.poll = mock_poll

    # Set up patch paths
    consumer_patch = patch('notification_main.Consumer', return_value=mock_consumer)
    producer_patch = patch('notification_main.Producer')
    
    # Mock HTTP client to intercept the post to gateway
    mock_response = MagicMock()
    mock_response.status_code = 200
    http_post_mock = AsyncMock(return_value=mock_response)

    with consumer_patch, producer_patch, patch('httpx.AsyncClient.post', new=http_post_mock):
        # Override settings for safety
        notification_settings.GATEWAY_ALERTS_URL = "http://mock-gateway/alerts"
        notification_settings.INTERNAL_SERVICE_KEY = "test_secret_key"

        # Run consume loop for a short period
        # Set keep_running = False in a background task after a short sleep to break the loop
        notification_main.keep_running = True
        
        async def stop_loop_soon():
            await asyncio.sleep(0.1)
            notification_main.keep_running = False
            
        asyncio.create_task(stop_loop_soon())
        await consume_alerts()

        # Verify that HTTP post was called with correct payload
        http_post_mock.assert_called_once()
        post_args, post_kwargs = http_post_mock.call_args
        assert post_args[0] == "http://mock-gateway/alerts"
        assert post_kwargs["headers"]["X-Internal-Service-Key"] == "test_secret_key"
        
        posted_json = post_kwargs["json"]
        assert posted_json["alert_type"] == "fire"
        assert posted_json["message"]["alert_id"] == "test-alert-123"
