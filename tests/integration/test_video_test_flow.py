# ruff: noqa: E402
import sys
import os
from unittest.mock import MagicMock
# Mock asyncpg to avoid import-time connection errors
sys.modules['asyncpg'] = MagicMock()

# Setup paths to prioritize this service's source and packages
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../apps/camera-service/src")))

# Evict config modules to prevent collision with other service tests
sys.modules.pop("config.settings", None)
sys.modules.pop("config", None)
sys.modules.pop("api.camera_routes", None)
sys.modules.pop("api", None)
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

def test_test_url_valid_request():
    """Verifies that a valid stream URL returns a 202 Accepted status."""
    client = TestClient(app)
    response = client.post(
        "/cameras/test-url",
        json={"url": "rtsp://192.168.1.50:554/live.sdp"}
    )
    assert response.status_code == status.HTTP_202_ACCEPTED
    data = response.json()
    assert data["accepted"] is True
    assert data["source_type"] == "url"
    assert data["status"] == "accepted"
    assert "job_id" in data

def test_test_url_invalid_scheme():
    """Verifies that URLs with invalid schemes (e.g. ftp://) trigger validation error."""
    client = TestClient(app)
    response = client.post(
        "/cameras/test-url",
        json={"url": "ftp://files.server.com/video.mp4"}
    )
    # Pydantic validation error or FastAPI request validation error returns 422
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_test_video_valid_file_upload():
    """Verifies that uploading a valid MP4 file successfully generates a test job acceptance."""
    # Mock file binary
    file_content = b"fake-mp4-stream-data"
    file_like = io.BytesIO(file_content)

    client = TestClient(app)
    response = client.post(
        "/cameras/test-video",
        files={"file": ("test_video.mp4", file_like, "video/mp4")}
    )
    
    assert response.status_code == status.HTTP_202_ACCEPTED
    data = response.json()
    assert data["accepted"] is True
    assert data["source_type"] == "file"
    assert data["filename"] == "test_video.mp4"
    assert data["size_bytes"] == len(file_content)

def test_test_video_unsupported_extension():
    """Verifies that uploading an invalid extension (e.g. txt) returns 415 error."""
    file_like = io.BytesIO(b"some-text-content")

    client = TestClient(app)
    response = client.post(
        "/cameras/test-video",
        files={"file": ("notes.txt", file_like, "text/plain")}
    )
    
    assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    assert "Unsupported video file extension" in response.json()["detail"]

def test_test_video_empty_file():
    """Verifies that uploading an empty file returns 422 error."""
    file_like = io.BytesIO(b"")

    client = TestClient(app)
    response = client.post(
        "/cameras/test-video",
        files={"file": ("empty.mp4", file_like, "video/mp4")}
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "empty" in response.json()["detail"].lower()
