import os
import sys
import logging
import asyncio
from typing import Optional
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager

# Setup path to import packages correctly in monorepo
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from api.camera_routes import router as camera_router
from services.health_checker import RtspHealthChecker
from infrastructure.persistence.database import engine, AsyncSessionLocal
from config.settings import settings
from packages.shared.api_errors import register_exception_handlers

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("camera_service")

# Global pointers to manage background loop
health_checker: Optional[RtspHealthChecker] = None
health_task: Optional[asyncio.Task] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event context manager for starting the RTSP status checks."""
    global health_checker, health_task
    
    logger.info("Starting up Camera Service...")
    
    # Wait for database readiness before executing background tasks
    from packages.shared.db_startup import wait_for_db
    await wait_for_db(settings.DATABASE_URL)
    
    # Initialize and execute the background checker task
    health_checker = RtspHealthChecker(AsyncSessionLocal)
    health_task = asyncio.create_task(health_checker.start_monitoring())
    
    yield
    
    logger.info("Shutting down Camera Service...")
    if health_checker:
        health_checker.stop()
    if health_task:
        health_task.cancel()
        try:
            await health_task
        except asyncio.CancelledError:
            pass
            
    await engine.dispose()
    logger.info("Camera service cleanup complete.")

_is_prod = os.getenv("ENV", "development") == "production"

# FastAPI instance definition
app = FastAPI(
    title="Intelligent MCPT — Camera Service",
    description="Registers video stream paths and monitors camera feed connectivity in real time.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if _is_prod else "/docs",
    redoc_url=None if _is_prod else "/redoc",
)
register_exception_handlers(app, settings.SERVICE_NAME)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Register endpoints
app.include_router(camera_router, prefix="/api/v1")

from sqlalchemy import text

@app.get("/health", tags=["system"])
async def health_check():
    """P3 #17: Verifies database connectivity for readiness probes."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "healthy", "service": "camera-service", "db": "connected"}
    except Exception:
        return {"status": "degraded", "service": "camera-service", "db": "disconnected"}

@app.get("/metrics", tags=["system"])
async def metrics():
    return {"message": "Metrics placeholder for camera-service"}

