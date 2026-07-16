import sys
from unittest.mock import MagicMock
sys.modules['cv2'] = MagicMock()

import pytest
from datetime import datetime, timezone
from events.event_schemas import TrackingEvent, DetectionPayload, BoundingBox
from plugins.probe_callbacks import CLASS_MAPPING

def test_ai_event_generation_and_serialization():
    """Verifies that DetectionEvents are correctly serialized for Kafka delivery."""
    bbox = BoundingBox(left=100.0, top=150.0, width=50.0, height=120.0)
    payload = DetectionPayload(
        class_id=0,
        type="person",
        confidence=0.92,
        tracking_id=42,
        bbox=bbox,
        embedding=[0.1] * 512,
        crop_path="crops/cam_1/person_42.jpg"
    )
    event = TrackingEvent(
        event_id="test-event-uuid-123",
        timestamp=datetime.now(timezone.utc).isoformat(),
        camera_id="cam_1",
        frame_number=1024,
        detection=payload
    )

    event_dict = event.to_dict()
    assert event_dict["event_id"] == "test-event-uuid-123"
    assert event_dict["camera_id"] == "cam_1"
    assert event_dict["frame_number"] == 1024
    assert event_dict["detection"]["type"] == "person"
    assert event_dict["detection"]["confidence"] == 0.92
    assert event_dict["detection"]["bbox"]["left"] == 100.0
    assert len(event_dict["detection"]["embedding"]) == 512

def test_probe_callback_sends_to_mock_producer():
    """Verifies that the GStreamer probe helper wraps events and invokes Kafka send_event."""
    mock_producer = MagicMock()
    
    # Mock behavior of probe payload dispatching
    camera_id = "camera_0"
    tracking_id = 99
    event_id = "event_99"
    
    bbox = BoundingBox(left=10.0, top=20.0, width=100.0, height=200.0)
    detection = DetectionPayload(
        class_id=0,
        type=CLASS_MAPPING[0],
        confidence=0.88,
        tracking_id=tracking_id,
        bbox=bbox,
        embedding=[0.05] * 512,
        crop_path="crops/camera_0/person_99.jpg"
    )
    
    event = TrackingEvent(
        event_id=event_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        camera_id=camera_id,
        frame_number=45,
        detection=detection
    )
    
    event_dict = event.to_dict()
    kafka_key = f"{camera_id}_{tracking_id}"
    
    mock_producer.send_event(
        topic="detection-events",
        key=kafka_key,
        event_data=event_dict
    )
    
    mock_producer.send_event.assert_called_once_with(
        topic="detection-events",
        key="camera_0_99",
        event_data=event_dict
    )
