import pytest
from datetime import datetime, timedelta, timezone
from packages.domain.entities.tracking_event import BoundingBox, TrackingEvent
from packages.domain.entities.person import Person

def test_bounding_box_area():
    """Verifies that bounding box area is calculated correctly."""
    bbox = BoundingBox(left=10.0, top=20.0, width=50.0, height=30.0)
    assert bbox.area() == 1500.0

def test_bounding_box_center():
    """Verifies that bounding box center coordinate is calculated correctly."""
    bbox = BoundingBox(left=10.0, top=20.0, width=50.0, height=30.0)
    assert bbox.center() == (35.0, 35.0)

def test_bounding_box_iou():
    """Tests the Intersection over Union (IoU) calculation logic."""
    bbox1 = BoundingBox(left=0.0, top=0.0, width=10.0, height=10.0)
    bbox2 = BoundingBox(left=5.0, top=0.0, width=10.0, height=10.0)
    
    # Intersection is 5x10 = 50
    # Union is 100 + 100 - 50 = 150
    # IoU = 50 / 150 = 0.3333...
    assert pytest.approx(bbox1.iou(bbox2), 0.0001) == 0.3333

def test_person_appearance_updates():
    """Verifies that updating a person's appearances correctly adjusts timestamps and count."""
    first_seen = datetime.now(timezone.utc) - timedelta(minutes=10)
    person = Person(first_seen=first_seen, last_seen=first_seen)
    
    new_seen = datetime.now(timezone.utc)
    person.update_appearance(new_seen)
    
    assert person.total_appearances == 2
    assert person.first_seen == first_seen
    assert person.last_seen == new_seen
