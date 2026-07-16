import os
import sys
import logging
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager

# Setup path to import packages correctly in monorepo
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from api.search_routes import router as search_router
from packages.shared.api_errors import register_exception_handlers
from packages.shared.vector.qdrant import QdrantVectorStore

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("search_service")

_is_prod = os.getenv("ENV", "development") == "production"

def validate_internal_service_key() -> None:
    key = os.getenv("INTERNAL_SERVICE_KEY", "")
    if _is_prod and (len(key) < 32 or key == "change_this_internal_key_in_production"):
        raise RuntimeError("INTERNAL_SERVICE_KEY must be set to a strong production secret")

@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_internal_service_key()
    yield

# FastAPI App definition
app = FastAPI(
    title="Intelligent MCPT — Search Service",
    description="Vector database query interface to identify matching person profiles.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if _is_prod else "/docs",
    redoc_url=None if _is_prod else "/redoc",
)
register_exception_handlers(app, "search-service")

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Register routes
app.include_router(search_router, prefix="/api/v1")

@app.get("/health", tags=["system"])
async def health_check():
    """P3 #17: Verifies vector store connectivity for readiness probes."""
    try:
        store = QdrantVectorStore()
        # Probe Qdrant collection listing to verify connection
        await store.client.get_collections()
        return {"status": "healthy", "service": "search-service", "qdrant": "connected"}
    except Exception:
        return {"status": "degraded", "service": "search-service", "qdrant": "disconnected"}

@app.get("/metrics", tags=["system"])
async def metrics():
    return {"message": "Metrics placeholder for search-service"}
