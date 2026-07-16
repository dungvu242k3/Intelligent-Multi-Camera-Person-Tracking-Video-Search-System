import asyncio
import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
import httpx
from confluent_kafka import Consumer, KafkaError

# Setup path to import packages correctly in monorepo
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from config.settings import settings

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

async def consume_alerts():
    """Asynchronous loop consuming alert messages from Kafka and posting to Gateway."""
    global keep_running
    
    # Configure Kafka Consumer
    conf = {
        'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
        'group.id': settings.KAFKA_GROUP_ID,
        'auto.offset.reset': 'latest',
        'enable.auto.commit': True
    }
    
    try:
        consumer = Consumer(conf)
        consumer.subscribe([settings.KAFKA_TOPIC_ALERTS])
        logger.info(f"Subscribed to Kafka alerts topic: {settings.KAFKA_TOPIC_ALERTS}")
    except Exception as e:
        logger.error(f"Failed to initialize Kafka Consumer: {e}")
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

                # Process valid message
                raw_payload = msg.value().decode('utf-8')
                alert_data = json.loads(raw_payload)
                logger.info(f"Consumed alert event from Kafka: {alert_data.get('alert_id', 'unknown')}")

                # Forward alert to Gateway WebSocket publisher endpoint
                gateway_payload = {
                    "alert_type": alert_data.get("alert_type", "general_alert"),
                    "message": alert_data
                }
                
                response = await client.post(settings.GATEWAY_ALERTS_URL, json=gateway_payload)
                if response.status_code == 200:
                    logger.info("Successfully forwarded alert event payload to Gateway.")
                else:
                    logger.error(f"Failed to forward alert to Gateway. Status: {response.status_code}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in alert processing loop: {e}", exc_info=True)
                await asyncio.sleep(2.0)

        # Clean shutdown
        try:
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
            await alert_task
        except asyncio.CancelledError:
            pass
    logger.info("Notification service shutdown complete.")

app = FastAPI(
    title="Intelligent MCPT — Notification Service",
    description="Listens to Kafka alert topics and pushes real-time WebSocket alerts via API Gateway.",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "healthy", "service": "notification-service"}
