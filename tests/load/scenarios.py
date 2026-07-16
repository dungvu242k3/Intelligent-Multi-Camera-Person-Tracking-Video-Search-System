import random
from typing import Dict, Any, List

def generate_mock_embedding(dimension: int = 512) -> List[float]:
    """Generates a randomized 512-dimensional embedding vector matching ReID patterns."""
    return [random.uniform(-1.0, 1.0) for _ in range(dimension)]

def get_login_payload() -> Dict[str, str]:
    """Returns a valid login payload for Operator access."""
    return {
        "email": "operator@example.test",
        "password": "StrongPass1"
    }

def get_mock_camera_payload() -> Dict[str, Any]:
    """Returns a randomized camera configuration payload for Camera CRUD testing."""
    cam_id = random.randint(100, 999)
    return {
        "name": f"Surveillance Cam-{cam_id}",
        "rtsp_url": f"rtsp://192.168.1.{random.randint(10, 250)}:554/stream",
        "location": f"Zone-{random.choice(['A', 'B', 'C', 'D'])}",
        "is_active": True
    }
