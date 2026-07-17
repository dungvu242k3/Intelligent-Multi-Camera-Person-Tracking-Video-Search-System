# ruff: noqa: E402
import sys
import os
from datetime import datetime, timedelta
import uuid

# Setup PYTHONPATH for packages
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from packages.domain.entities.alert import Alert
from packages.domain.entities.person import Person
from packages.domain.entities.tracking_event import BoundingBox, TrackingEvent
from packages.domain.enums.alert_severity import AlertSeverity

def test_alert_entity():
    alert_id = uuid.uuid4()
    camera_id = uuid.uuid4()
    alert = Alert(
        type="fire",
        severity=AlertSeverity.CRITICAL,
        title="Fire Alert!",
        timestamp=datetime.utcnow(),
        id=alert_id,
        camera_id=camera_id,
    )
    
    assert alert.id == alert_id
    assert alert.camera_id == camera_id
    assert alert.type == "fire"
    assert alert.severity == AlertSeverity.CRITICAL
    assert alert.is_read is False
    
    alert.mark_as_read()
    assert alert.is_read is True

def test_person_entity():
    person_id = uuid.uuid4()
    t1 = datetime.utcnow()
    t2 = t1 + timedelta(seconds=10)
    t3 = t1 - timedelta(seconds=5)
    
    person = Person(
        id=person_id,
        display_name="Test Person",
        first_seen=t1,
        last_seen=t1,
        total_appearances=1
    )
    
    assert person.id == person_id
    assert person.total_appearances == 1
    
    # Update with future event
    person.update_appearance(t2)
    assert person.last_seen == t2
    assert person.first_seen == t1
    assert person.total_appearances == 2
    
    # Update with past event
    person.update_appearance(t3)
    assert person.first_seen == t3
    assert person.last_seen == t2
    assert person.total_appearances == 3

def test_bounding_box_geometry():
    bbox1 = BoundingBox(left=10.0, top=10.0, width=50.0, height=100.0)
    bbox2 = BoundingBox(left=20.0, top=20.0, width=50.0, height=100.0)
    
    assert bbox1.area() == 5000.0
    assert bbox1.center() == (35.0, 60.0)
    
    # Calculate IoU
    # Intersection: left=20, top=20, width=40 (60-20), height=90 (110-20) -> area=3600
    # Union: 5000 + 5000 - 3600 = 6400
    # IoU: 3600 / 6400 = 0.5625
    assert bbox1.iou(bbox2) == 0.5625
    
    # Disjoint boxes
    bbox3 = BoundingBox(left=100.0, top=100.0, width=10.0, height=10.0)
    assert bbox1.iou(bbox3) == 0.0

def test_tracking_event_entity():
    camera_id = uuid.uuid4()
    person_id = uuid.uuid4()
    timestamp = datetime.utcnow()
    bbox = BoundingBox(left=10.0, top=10.0, width=50.0, height=100.0)
    
    event = TrackingEvent(
        camera_id=camera_id,
        confidence=0.85,
        bbox=bbox,
        timestamp=timestamp,
        person_id=person_id,
        crop_path="/data/crops/1.jpg",
        embedding=[0.1] * 512
    )
    
    assert event.camera_id == camera_id
    assert event.person_id == person_id
    assert event.confidence == 0.85
    assert event.bbox == bbox
    assert event.crop_path == "/data/crops/1.jpg"
    assert len(event.embedding) == 512
