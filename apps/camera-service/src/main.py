import os
import sys
import logging
import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Setup path to import packages correctly in monorepo
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from api.camera_routes import router as camera_router
from services.health_checker import RtspHealthChecker
from infrastructure.persistence.database import engine, AsyncSessionLocal

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

# FastAPI instance definition
app = FastAPI(
    title="Intelligent MCPT — Camera Service",
    description="Registers video stream paths and monitors camera feed connectivity in real time.",
    version="1.0.0",
    lifespan=lifespan
)

# Register endpoints
app.include_router(camera_router, prefix="/api/v1")

@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "healthy", "service": "camera-service"}

@app.get("/metrics", tags=["system"])
async def metrics():
    return {"message": "Metrics placeholder for camera-service"}
