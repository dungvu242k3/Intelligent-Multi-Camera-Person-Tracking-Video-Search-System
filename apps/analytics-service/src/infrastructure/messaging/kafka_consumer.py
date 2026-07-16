import json
import logging
import asyncio
import os
from typing import Callable, Coroutine
from confluent_kafka import Consumer, KafkaError

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
            'enable.auto.commit': True
        }
        self.consumer = Consumer(conf)
        self.running = False
        logger.info(f"Kafka Consumer initialized with group: {group_id}")

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

                # Parse JSON payload
                try:
                    payload = json.loads(msg.value().decode('utf-8'))
                    # Dispatch to usecase async callback
                    await process_callback(payload)
                except Exception as e:
                    logger.error(f"Error parsing or processing Kafka event message: {e}")
        finally:
            self.close()

    def stop(self):
        """Signals the poll loop to terminate."""
        self.running = False

    def close(self):
        """Closes the Kafka consumer connection."""
        logger.info("Closing Kafka consumer...")
        self.consumer.close()
