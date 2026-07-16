import json
import logging
from typing import Dict, Any
from confluent_kafka import Producer

logger = logging.getLogger("shared.kafka")

class KafkaEventProducer:
    """Synchronous high-performance wrapper for confluent-kafka producer."""
    def __init__(self, bootstrap_servers: str, client_id: str = "shared-producer"):
        conf = {
            'bootstrap.servers': bootstrap_servers,
            'client.id': client_id,
            'queue.buffering.max.messages': 100000,
            'queue.buffering.max.ms': 10,
            'linger.ms': 5,
            'acks': 1
        }
        self.producer = Producer(conf)
        logger.info(f"Kafka Producer initialized for bootstrap servers: {bootstrap_servers}")

    def _delivery_report(self, err, msg):
        if err is not None:
            logger.error(f"Message delivery failed: {err}")

    def send_event(self, topic: str, key: str, event_data: Dict[str, Any]):
        """Publishes metadata to a specific Kafka topic."""
        try:
            payload = json.dumps(event_data).encode('utf-8')
            self.producer.produce(
                topic=topic,
                key=key.encode('utf-8') if key else None,
                value=payload,
                callback=self._delivery_report
            )
            self.producer.poll(0)
        except Exception as e:
            logger.error(f"Failed to queue event to Kafka: {e}")

    def flush(self, timeout: float = 1.0):
        """Flushes the internal buffering queue before exit."""
        self.producer.flush(timeout)
