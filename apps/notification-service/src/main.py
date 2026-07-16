import asyncio
import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Request
import httpx
from confluent_kafka import Consumer, KafkaError, Producer

# Setup path to import packages correctly in monorepo
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from config.settings import settings
from packages.shared.api_errors import register_exception_handlers

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("notification_service")

# Global pointer to manage background loop
alert_task: Optional[asyncio.Task] = None
keep_running = True
consumer_ready = False

async def consume_alerts():
    """Asynchronous loop consuming alert messages from Kafka and posting to Gateway."""
    global keep_running, consumer_ready
    
    # Configure Kafka Consumer
    conf = {
        'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
        'group.id': settings.KAFKA_GROUP_ID,
        'auto.offset.reset': 'latest',
        'enable.auto.commit': False
    }
    
    try:
        consumer = Consumer(conf)
        dlq_producer = Producer({'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS})
        consumer.subscribe([settings.KAFKA_TOPIC_ALERTS])
        consumer_ready = True
        logger.info(f"Subscribed to Kafka alerts topic: {settings.KAFKA_TOPIC_ALERTS}")
    except Exception as e:
        logger.error(f"Failed to initialize Kafka Consumer: {e}")
        consumer_ready = False
        return

    # HTTP client to send alerts to the Gateway
    async with httpx.AsyncClient(timeout=10.0) as client:
        loop = asyncio.get_running_loop()
        
        while keep_running:
            try:
                # poll() is blocking, run in executor to keep event loop free
                msg = await loop.run_in_executor(None, consumer.poll, 1.0)
                
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        logger.error(f"Kafka error occurred: {msg.error()}")
                        await asyncio.sleep(2.0)
                        continue

                try:
                    raw_payload = msg.value().decode('utf-8')
                    alert_data = json.loads(raw_payload)
                except Exception as e:
                    logger.error(f"Invalid alert event payload, forwarding to DLQ: {e}")
                    dlq_producer.produce(
                        f"{settings.KAFKA_TOPIC_ALERTS}.DLQ",
                        key=msg.key(),
                        value=json.dumps({
                            "source_topic": settings.KAFKA_TOPIC_ALERTS,
                            "partition": msg.partition(),
                            "offset": msg.offset(),
                            "error": str(e),
                            "raw_value": msg.value().decode("utf-8", errors="replace") if msg.value() else None,
                        }).encode("utf-8"),
                    )
                    dlq_producer.flush(5.0)
                    consumer.commit(message=msg, asynchronous=False)
                    continue

                logger.info("Consumed alert event from Kafka.", extra={"alert_id": alert_data.get("alert_id", "unknown")})

                # Forward alert to Gateway WebSocket publisher endpoint
                gateway_payload = {
                    "alert_type": alert_data.get("alert_type") or alert_data.get("type", "general_alert"),
                    "message": alert_data
                }

                forwarded = False
                for attempt in range(1, 4):
                    response = await client.post(
                        settings.GATEWAY_ALERTS_URL,
                        json=gateway_payload,
                        headers={"X-Internal-Service-Key": settings.INTERNAL_SERVICE_KEY},
                    )
                    if response.status_code == 200:
                        forwarded = True
                        break
                    logger.error(f"Failed to forward alert to Gateway. Status: {response.status_code}. Attempt {attempt}/3")
                    await asyncio.sleep(min(2 ** attempt, 8))

                if forwarded:
                    consumer.commit(message=msg, asynchronous=False)
                    logger.info("Successfully forwarded alert event payload to Gateway.")
                else:
                    dlq_producer.produce(
                        f"{settings.KAFKA_TOPIC_ALERTS}.DLQ",
                        key=msg.key(),
                        value=json.dumps({
                            "source_topic": settings.KAFKA_TOPIC_ALERTS,
                            "partition": msg.partition(),
                            "offset": msg.offset(),
                            "error": "Gateway forwarding failed after retries",
                            "payload": alert_data,
                        }).encode("utf-8"),
                    )
                    dlq_producer.flush(5.0)
                    consumer.commit(message=msg, asynchronous=False)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in alert processing loop: {e}", exc_info=True)
                await asyncio.sleep(2.0)

        # Clean shutdown
        try:
            consumer_ready = False
            consumer.close()
            logger.info("Closed Kafka Consumer connection successfully.")
        except Exception as e:
            logger.error(f"Error closing Kafka Consumer: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event context manager handling Kafka consumer task."""
    global alert_task, keep_running
    logger.info("Starting up Notification Service...")
    keep_running = True
    alert_task = asyncio.create_task(consume_alerts())
    
    yield
    
    logger.info("Shutting down Notification Service...")
    keep_running = False
    if alert_task:
        alert_task.cancel()
        try:
            await asyncio.wait_for(alert_task, timeout=15.0)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass
    logger.info("Notification service shutdown complete.")

_is_prod = settings.ENV == "production"

app = FastAPI(
    title="Intelligent MCPT — Notification Service",
    description="Listens to Kafka alert topics and pushes real-time WebSocket alerts via API Gateway.",
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

@app.get("/health", tags=["system"])
async def health_check():
    return {
        "status": "healthy" if consumer_ready else "degraded",
        "service": "notification-service",
        "kafka_consumer": "subscribed" if consumer_ready else "unavailable",
    }
