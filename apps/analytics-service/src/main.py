import os
import sys
import logging
import asyncio
from typing import Optional
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Setup path to import packages correctly in monorepo
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from presentation.api.v1.tracking_routes import router as tracking_router
from infrastructure.persistence.database import engine, AsyncSessionLocal
from infrastructure.persistence.sqlalchemy_person_repo import SqlAlchemyPersonRepository
from infrastructure.persistence.sqlalchemy_tracking_repo import SqlAlchemyTrackingRepository
from packages.shared.vector.qdrant import QdrantVectorStore
from infrastructure.messaging.kafka_consumer import KafkaEventConsumer
from application.use_cases.process_tracking_event import ProcessTrackingEventUseCase
from packages.shared.messaging.kafka import KafkaEventProducer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("analytics_service")

# Global instances for background task management
consumer_instance: Optional[KafkaEventConsumer] = None
consumer_task: Optional[asyncio.Task] = None
kafka_producer_instance: Optional[KafkaEventProducer] = None

async def start_kafka_consumer():
    """Background loop listening for raw DeepStream detection events from Kafka."""
    global consumer_instance, kafka_producer_instance
    
    broker = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    topic = os.getenv("KAFKA_DETECTION_TOPIC", "detection-events")
    
    # Initialize infrastructure dependencies
    vector_store = QdrantVectorStore()
    kafka_producer_instance = KafkaEventProducer(bootstrap_servers=broker, client_id="analytics-alert-producer")
    consumer_instance = KafkaEventConsumer(bootstrap_servers=broker, group_id="analytics-service-consumers")
    
    async def process_message_callback(payload: dict):
        """Async callback for each parsed event message."""
        async with AsyncSessionLocal() as session:
            try:
                # Instantiate layered Clean Arch classes inside transaction boundary
                person_repo = SqlAlchemyPersonRepository(session)
                tracking_repo = SqlAlchemyTrackingRepository(session)
                
                usecase = ProcessTrackingEventUseCase(
                    person_repo=person_repo,
                    tracking_repo=tracking_repo,
                    vector_store=vector_store,
                    kafka_producer=kafka_producer_instance
                )
                
                # Execute use case
                await usecase.execute(payload)
                await session.commit()
            except Exception as e:
                logger.error(f"Failed to execute process event transaction: {e}")
                await session.rollback()

    # Start infinite polling loop
    try:
        await consumer_instance.start_listening(topic, process_message_callback)
    except asyncio.CancelledError:
        logger.info("Kafka consumer background task cancelled.")
    except Exception as e:
        logger.critical(f"Fatal error in Kafka consumer: {e}", exc_info=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle context manager handling startup and shutdown routines."""
    global consumer_task, consumer_instance, kafka_producer_instance
    
    logger.info("Starting up Analytics Service...")
    # Start Kafka consumer in background task (runs on the asyncio event loop)
    consumer_task = asyncio.create_task(start_kafka_consumer())
    
    yield
    
    logger.info("Shutting down Analytics Service...")
    # 1. Stop consumer polling loop
    if consumer_instance:
        consumer_instance.stop()
    
    # 2. Cancel background task
    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
            
    # 3. Flush Kafka alerts producer
    if kafka_producer_instance:
        kafka_producer_instance.flush(timeout=2.0)
        
    # 4. Dispose database engine pool
    await engine.dispose()
    logger.info("Service cleanup completed.")

_is_prod = os.getenv("ENV", "development") == "production"

# FastAPI Application definition
app = FastAPI(
    title="Intelligent MCPT — Analytics Service",
    description="Processes tracking telemetry events, updates person galleries, and triggers alerts.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if _is_prod else "/docs",
    redoc_url=None if _is_prod else "/redoc",
)

# Mount API Routers
app.include_router(tracking_router, prefix="/api/v1")

from sqlalchemy import text

@app.get("/health", tags=["system"])
async def health_check():
    """P3 #17: Verifies database connectivity for readiness probes."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "healthy", "service": "analytics-service", "db": "connected"}
    except Exception:
        return {"status": "degraded", "service": "analytics-service", "db": "disconnected"}

@app.get("/metrics", tags=["system"])
async def metrics():
    """Placeholder endpoint for exporting Prometheus metrics."""
    return {"message": "Metrics endpoint placeholder. Prometheus integration enabled."}
