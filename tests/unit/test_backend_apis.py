# ruff: noqa: E402
import sys
import os
import pytest
from datetime import timedelta

# Set monorepo root path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

def test_token_service():
    """Verify TokenService JWT creation, validation, and expiry handling."""
    auth_src = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../apps/auth-service/src/"))
    sys.path.insert(0, auth_src)
    
    # Ensure fresh imports from auth-service context
    from config.settings import settings
    from services.token_service import TokenService
    
    payload = {"sub": "user_123", "email": "test@example.com"}
    token = TokenService.create_access_token(payload)
    
    decoded = TokenService.decode_and_verify_token(token)
    assert decoded is not None
    assert decoded["sub"] == "user_123"
    assert decoded["type"] == "access"
    
    # Test expired token
    expired_token = TokenService.create_access_token(payload, expires_delta=timedelta(seconds=-10))
    assert TokenService.decode_and_verify_token(expired_token) is None
    
    # Cleanup sys.path to avoid side effects
    sys.path.remove(auth_src)

def test_auth_request_schemas():
    """Verify validation constraints on registration schemas."""
    # Prevent cache collisions in monorepo
    for mod in ["api", "config", "services", "models"]:
        sys.modules.pop(mod, None)
        # Also clean nested children
        for key in list(sys.modules.keys()):
            if key.startswith(f"{mod}."):
                sys.modules.pop(key, None)
                
    auth_src = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../apps/auth-service/src/"))
    sys.path.insert(0, auth_src)
    
    from api.auth_routes import RegisterRequest
    from pydantic import ValidationError
    
    # 1. Valid request
    req = RegisterRequest(email="user@test.com", password="Password123", full_name="John Doe")
    assert req.full_name == "John Doe"
    
    # 2. Password missing uppercase
    with pytest.raises(ValidationError) as excinfo:
        RegisterRequest(email="user@test.com", password="password123", full_name="John Doe")
    assert "Password must contain at least one uppercase letter" in str(excinfo.value)
    
    # 3. Password missing digit
    with pytest.raises(ValidationError) as excinfo:
        RegisterRequest(email="user@test.com", password="PasswordNoDigit", full_name="John Doe")
    assert "Password must contain at least one digit" in str(excinfo.value)
    
    # 4. Blank full name
    with pytest.raises(ValidationError) as excinfo:
        RegisterRequest(email="user@test.com", password="Password123", full_name="   ")
    assert "Full name cannot be blank" in str(excinfo.value)
    
    sys.path.remove(auth_src)

def test_camera_request_schemas():
    """Verify validation constraints on camera streaming RTSP/HTTP URLs."""
    # Prevent cache collisions in monorepo
    for mod in ["api", "config", "services", "models"]:
        sys.modules.pop(mod, None)
        # Also clean nested children
        for key in list(sys.modules.keys()):
            if key.startswith(f"{mod}."):
                sys.modules.pop(key, None)
                
    cam_src = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../apps/camera-service/src/"))
    sys.path.insert(0, cam_src)
    
    from api.camera_routes import VideoUrlTestRequest
    from pydantic import ValidationError
    
    # 1. Valid RTSP stream URL
    req = VideoUrlTestRequest(url="rtsp://192.168.1.100/stream1")
    assert req.url == "rtsp://192.168.1.100/stream1"
    
    # 2. Invalid schema (FTP)
    with pytest.raises(ValidationError) as excinfo:
        VideoUrlTestRequest(url="ftp://192.168.1.100/stream1")
    assert "URL must be a valid rtsp://, http://, or https://" in str(excinfo.value)
    
    # 3. URL containing whitespace characters
    with pytest.raises(ValidationError) as excinfo:
        VideoUrlTestRequest(url="rtsp://192.168.1.100/stream 1")
    assert "URL must not contain whitespace" in str(excinfo.value)
    
    sys.path.remove(cam_src)
