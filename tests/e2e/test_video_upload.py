# ruff: noqa: E402
import sys
import os
from unittest.mock import MagicMock
# Mock asyncpg to avoid import-time connection errors
sys.modules['asyncpg'] = MagicMock()

# Setup paths to prioritize this service's source and packages
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../apps/camera-service/src")))

# Evict config/api modules to prevent collision with other service tests
for mod in ["api", "config", "services", "models", "events"]:
    sys.modules.pop(mod, None)
    for key in list(sys.modules.keys()):
        if key.startswith(f"{mod}."):
            sys.modules.pop(key, None)
sys.modules.pop("main", None)

# Import security package and mock require_roles to bypass all auth checks
import packages.shared.security
from packages.shared.security import AuthenticatedUser, Role

mock_operator = AuthenticatedUser(
    user_id="test-operator-id",
    role=Role.OPERATOR
)

# Mock require_roles to return a dependency that always yields our mock operator
packages.shared.security.require_roles = lambda *args, **kwargs: lambda: mock_operator

import io
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

# Import router after patching require_roles
from api.camera_routes import router as camera_router

# Initialize test app
app = FastAPI()
app.include_router(camera_router)

def test_end_to_end_video_upload_validation_flow():
    """E2E flow test to verify video upload payloads, content types, and status checks."""
    file_content = b"fake-mpeg4-avi-stream-data"
    file_like = io.BytesIO(file_content)

    client = TestClient(app)
    response = client.post(
        "/cameras/test-video",
        files={"file": ("validation_footage.mp4", file_like, "video/mp4")}
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    data = response.json()
    assert data["accepted"] is True
    assert data["source_type"] == "file"
    assert data["status"] == "accepted"
    assert data["filename"] == "validation_footage.mp4"
    assert data["size_bytes"] == len(file_content)
    assert "job_id" in data
