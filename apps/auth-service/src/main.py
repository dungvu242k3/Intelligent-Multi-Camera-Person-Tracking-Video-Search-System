import os
import sys
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Setup path to import packages correctly in monorepo
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from api.auth_routes import router as auth_router, engine

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("auth_service")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event context manager for handling startup and database shutdown."""
    logger.info("Starting up Auth Service...")
    yield
    logger.info("Shutting down Auth Service...")
    await engine.dispose()
    logger.info("Auth service database engine disposed.")

app = FastAPI(
    title="Intelligent MCPT — Auth Service",
    description="Manages user credential registrations, logins, and token validation checks.",
    version="1.0.0",
    lifespan=lifespan
)

# Register endpoints
app.include_router(auth_router, prefix="/api/v1/auth")

@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "healthy", "service": "auth-service"}

@app.get("/metrics", tags=["system"])
async def metrics():
    return {"message": "Metrics placeholder for auth-service"}
