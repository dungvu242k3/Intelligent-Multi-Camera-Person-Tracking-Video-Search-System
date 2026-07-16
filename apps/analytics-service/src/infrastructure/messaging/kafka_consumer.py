import json
import logging
import asyncio
import os
from typing import Callable, Coroutine
from confluent_kafka import Consumer, KafkaError, Producer

logger = logging.getLogger("analytics_service.kafka_consumer")

class KafkaEventConsumer:
    """High-performance confluent-kafka consumer runner.
    Subscribes to detection-events and delegates processing to the registered usecase callback.
    """
    def __init__(self, bootstrap_servers: str, group_id: str = "analytics-service-group"):
        conf = {
            'bootstrap.servers': bootstrap_servers,
            'group.id': group_id,
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False
        }
        self.consumer = Consumer(conf)
        self.dlq_producer = Producer({'bootstrap.servers': bootstrap_servers})
        self.max_attempts = int(os.getenv("KAFKA_PROCESSING_MAX_ATTEMPTS", "3"))
        self.running = False
        logger.info(f"Kafka Consumer initialized with group: {group_id}")

    def _send_to_dlq(self, topic: str, msg, error: Exception) -> None:
        dlq_topic = f"{topic}.DLQ"
        payload = {
            "source_topic": topic,
            "partition": msg.partition(),
            "offset": msg.offset(),
            "error": str(error),
            "raw_value": msg.value().decode("utf-8", errors="replace") if msg.value() else None,
        }
        self.dlq_producer.produce(
            dlq_topic,
            key=msg.key(),
            value=json.dumps(payload).encode("utf-8"),
        )
        self.dlq_producer.flush(5.0)
        logger.error(f"Kafka event moved to DLQ topic {dlq_topic} at offset {msg.offset()}")

    async def start_listening(self, topic: str, process_callback: Callable[[dict], Coroutine]):
        """Starts the infinite polling loop. Runs asynchronously without blocking."""
        self.consumer.subscribe([topic])
        self.running = True
        logger.info(f"Subscribed to topic: {topic}. Listening for events...")

        # Run the sync polling inside an executor thread or loop to keep it async friendly
        loop = asyncio.get_event_loop()
        try:
            while self.running:
                # Poll message synchronously (non-blocking for small timeouts)
                msg = await loop.run_in_executor(None, self.consumer.poll, 1.0)
                
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition event
                        continue
                    else:
                        logger.error(f"Kafka Consumer Error: {msg.error()}")
                        break

                try:
                    payload = json.loads(msg.value().decode('utf-8'))
                except Exception as e:
                    logger.error(f"Error parsing Kafka event message: {e}")
                    self._send_to_dlq(topic, msg, e)
                    self.consumer.commit(message=msg, asynchronous=False)
                    continue

                processed = False
                last_error = None
                for attempt in range(1, self.max_attempts + 1):
                    try:
                        await process_callback(payload)
                        processed = True
                        break
                    except Exception as e:
                        last_error = e
                        logger.error(
                            f"Error processing Kafka event message on attempt {attempt}/{self.max_attempts}: {e}",
                            exc_info=True,
                        )
                        await asyncio.sleep(min(2 ** attempt, 10))

                if processed:
                    self.consumer.commit(message=msg, asynchronous=False)
                else:
                    self._send_to_dlq(topic, msg, last_error or RuntimeError("Unknown processing failure"))
                    self.consumer.commit(message=msg, asynchronous=False)
        finally:
            self.close()

    def stop(self):
        """Signals the poll loop to terminate."""
        self.running = False

    def close(self):
        """Closes the Kafka consumer connection."""
        logger.info("Closing Kafka consumer...")
        self.consumer.close()
