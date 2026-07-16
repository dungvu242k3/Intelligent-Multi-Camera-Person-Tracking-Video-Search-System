import os
import sys
import logging
from fastapi import FastAPI

# Setup path to import packages correctly in monorepo
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from apps.search-service.src.api.search_routes import router as search_router

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("search_service")

# FastAPI App definition
app = FastAPI(
    title="Intelligent MCPT — Search Service",
    description="Vector database query interface to identify matching person profiles.",
    version="1.0.0"
)

# Register routes
app.include_router(search_router, prefix="/api/v1")

@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "healthy", "service": "search-service"}

@app.get("/metrics", tags=["system"])
async def metrics():
    return {"message": "Metrics placeholder for search-service"}
