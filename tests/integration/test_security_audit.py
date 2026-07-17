# ruff: noqa: E402
import sys
import os

# Evict config/service modules to prevent collision
for mod in ["api", "config", "services", "models", "events"]:
    sys.modules.pop(mod, None)
    for key in list(sys.modules.keys()):
        if key.startswith(f"{mod}."):
            sys.modules.pop(key, None)

# Setup PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../apps/gateway/src/")))

from fastapi.testclient import TestClient
from apps.gateway.src.main import app
from apps.gateway.src.config.settings import settings

def test_security_headers_middleware():
    """Verify that HTTP security headers are set correctly by gateway middleware."""
    client = TestClient(app)
    # Perform a request
    response = client.get("/health")
    
    # Assert headers are set correctly
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert "default-src 'self'" in response.headers.get("Content-Security-Policy", "")
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

def test_openapi_docs_disabled_in_production(monkeypatch):
    """Verify that OpenAPI documentation endpoints are disabled when ENV = production."""
    # Force production settings context
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", "secure_secret_key_at_least_32_chars_long_123456")
    monkeypatch.setenv("INTERNAL_SERVICE_KEY", "secure_internal_key_at_least_32_chars_long_123456")
    monkeypatch.setattr(settings, "ENV", "production")
    
    # Clean sys.path and sys.modules to resolve only gateway settings
    old_path = sys.path.copy()
    sys.path = [p for p in sys.path if "camera-service" not in p and "notification-service" not in p and "analytics-service" not in p]
    sys.modules.pop("config.settings", None)
    sys.modules.pop("config", None)
    
    # Reload or check application attributes
    from importlib import reload
    import config.settings
    reload(config.settings)
    import apps.gateway.src.main as gateway_main
    reload(gateway_main)
    
    # Restore path
    sys.path = old_path
    
    prod_client = TestClient(gateway_main.app)
    
    # Docs should return 404
    res_docs = prod_client.get("/docs")
    assert res_docs.status_code == 404
    
    res_redoc = prod_client.get("/redoc")
    assert res_redoc.status_code == 404

def test_dotenv_gitignore_compliance():
    """Verify that sensitive config files are ignored in .gitignore."""
    gitignore_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.gitignore"))
    assert os.path.exists(gitignore_path)
    
    with open(gitignore_path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
        
    ignored_patterns = [line.strip() for line in lines if line.strip() and not line.startswith("#")]
    
    # Check for env files
    has_env_ignore = any(".env" in pattern for pattern in ignored_patterns)
    assert has_env_ignore is True
