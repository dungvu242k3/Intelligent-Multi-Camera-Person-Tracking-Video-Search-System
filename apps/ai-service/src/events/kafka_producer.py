import json
import logging
from typing import Dict, Any
from confluent_kafka import Producer

logger = logging.getLogger("ai_service.kafka")

class KafkaEventProducer:
    """Synchronous high-performance wrapper for confluent-kafka producer.
    DeepStream probes run in C-threads, so synchronous callback queues are preferred
    to avoid event-loop thread context switching.
    """
    def __init__(self, bootstrap_servers: str, client_id: str = "ai-service-producer"):
        conf = {
            'bootstrap.servers': bootstrap_servers,
            'client.id': client_id,
            'queue.buffering.max.messages': 100000,
            'queue.buffering.max.ms': 10, # low latency batching
            'linger.ms': 5,
            'acks': 1 # Wait for leader ack (performance-resilience balance)
        }
        self.producer = Producer(conf)
        logger.info(f"Kafka Producer initialized for bootstrap servers: {bootstrap_servers}")

    def _delivery_report(self, err, msg):
        """Optional delivery callback to log success/failures."""
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            # Successfully delivered
            pass

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
            # Polls the producer queue to trigger callbacks
            self.producer.poll(0)
        except Exception as e:
            logger.error(f"Failed to queue event to Kafka: {e}")

    def flush(self, timeout: float = 1.0):
        """Flushes the internal buffering queue before exit."""
        self.producer.flush(timeout)
