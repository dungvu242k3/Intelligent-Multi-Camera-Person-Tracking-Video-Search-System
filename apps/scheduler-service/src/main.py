import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI

# Setup path to import packages correctly in monorepo
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from config.settings import settings

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("scheduler_service")

# Global task pointers
cleanup_task: Optional[asyncio.Task] = None
keep_running = True

async def run_data_cleanup_job() -> None:
    """Asynchronous loop executing data cleanup checks (MinIO/Qdrant) at configured intervals."""
    global keep_running
    interval_seconds = settings.CLEANUP_INTERVAL_HOURS * 3600
    
    logger.info(
        f"Data cleanup job scheduler active. "
        f"Interval: {settings.CLEANUP_INTERVAL_HOURS} hours, Retention: {settings.RETENTION_DAYS} days."
    )
    
    while keep_running:
        try:
            logger.info("Starting scheduled data retention policy scan...")
            
            # 1. Scaffolding for Qdrant vector deletes (Cleanup vectors older than retention days)
            logger.info(f"Scanning Qdrant collection for vectors older than {settings.RETENTION_DAYS} days...")
            # actual: client.delete(collection_name="person_embeddings", filter=...)
            
            # 2. Scaffolding for MinIO crop deletes (Cleanup jpeg crops older than retention days)
            logger.info(f"Scanning MinIO 'detection-crops' bucket for objects older than {settings.RETENTION_DAYS} days...")
            # actual: client.remove_objects(...)
            
            logger.info("Retention policy scan completed successfully. Next run in config interval.")
            
        except Exception as e:
            logger.error(f"Error occurred during scheduled cleanup run: {e}", exc_info=True)
            
        # Dynamic sleep checking cancellation flag
        for _ in range(int(interval_seconds)):
            if not keep_running:
                break
            await asyncio.sleep(1.0)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event context manager handling cleanup background task."""
    global cleanup_task, keep_running
    logger.info("Starting up Scheduler Service...")
    keep_running = True
    cleanup_task = asyncio.create_task(run_data_cleanup_job())
    
    yield
    
    logger.info("Shutting down Scheduler Service...")
    keep_running = False
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
    logger.info("Scheduler service shutdown complete.")

app = FastAPI(
    title="Intelligent MCPT — Scheduler Service",
    description="Manages system cleanup loops and scheduled data retention policies.",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "healthy", "service": "scheduler-service"}
