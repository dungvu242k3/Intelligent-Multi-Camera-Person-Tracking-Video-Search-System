import os
import sys
import logging
from fastapi import FastAPI

# Setup path to import packages correctly in monorepo
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from api.search_routes import router as search_router

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("search_service")

from packages.shared.vector.qdrant import QdrantVectorStore

_is_prod = os.getenv("ENV", "development") == "production"

# FastAPI App definition
app = FastAPI(
    title="Intelligent MCPT — Search Service",
    description="Vector database query interface to identify matching person profiles.",
    version="1.0.0",
    docs_url=None if _is_prod else "/docs",
    redoc_url=None if _is_prod else "/redoc",
)

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
