import pytest
from pydantic import ValidationError
from packages.contracts.dto.camera import CameraCreate

def test_camera_create_validation_success():
    """Verifies that valid data successfully creates a CameraCreate DTO."""
    data = {
        "name": "Cam Front Door",
        "rtsp_url": "rtsp://admin:pass@192.168.1.100:554/stream1",
        "location": "Front Door Gate",
        "fps": 30
    }
    camera = CameraCreate(**data)
    assert camera.name == "Cam Front Door"
    assert camera.fps == 30

def test_camera_create_validation_failure():
    """Verifies that invalid data raises pydantic validation exceptions."""
    # Invalid FPS (greater than 120)
    invalid_data = {
        "name": "Cam Test",
        "rtsp_url": "rtsp://127.0.0.1/stream",
        "fps": 200
    }
    with pytest.raises(ValidationError):
        CameraCreate(**invalid_data)

    # Missing name
    invalid_data_2 = {
        "rtsp_url": "rtsp://127.0.0.1/stream"
    }
    with pytest.raises(ValidationError):
        CameraCreate(**invalid_data_2)
