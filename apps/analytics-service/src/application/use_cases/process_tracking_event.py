import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from packages.domain.entities.person import Person
from packages.domain.entities.tracking_event import TrackingEvent, BoundingBox
from apps.analytics-service.src.infrastructure.persistence.sqlalchemy_person_repo import SqlAlchemyPersonRepository
from apps.analytics-service.src.infrastructure.persistence.sqlalchemy_tracking_repo import SqlAlchemyTrackingRepository
from apps.analytics-service.src.infrastructure.external.qdrant_client import QdrantVectorStore

logger = logging.getLogger("analytics_service.use_cases")

class ProcessTrackingEventUseCase:
    """Application use case to orchestrate business flow upon receiving raw detection events."""
    def __init__(
        self,
        person_repo: SqlAlchemyPersonRepository,
        tracking_repo: SqlAlchemyTrackingRepository,
        vector_store: QdrantVectorStore,
        kafka_producer # Passed in dynamically
    ):
        self.person_repo = person_repo
        self.tracking_repo = tracking_repo
        self.vector_store = vector_store
        self.kafka_producer = kafka_producer

    async def execute(self, event_data: Dict[str, Any]):
        """Processes a single raw detection message from Kafka."""
        try:
            camera_id = uuid.UUID(event_data["camera_id"])
            frame_num = event_data["frame_number"]
            timestamp_str = event_data["timestamp"]
            # Parse timestamp to datetime
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            
            detection = event_data["detection"]
            class_id = detection["class_id"]
            object_type = detection["type"]
            confidence = detection["confidence"]
            crop_path = detection.get("crop_path")
            
            bbox_raw = detection["bbox"]
            bbox = BoundingBox(
                left=bbox_raw["left"],
                top=bbox_raw["top"],
                width=bbox_raw["width"],
                height=bbox_raw["height"]
            )

            # --- BRANCH 1: FIRE & SMOKE DETECTIONS ---
            if object_type in ["fire", "smoke"]:
                await self._handle_fire_detection(camera_id, confidence, crop_path, timestamp)
                return

            # --- BRANCH 2: PERSON DETECTIONS (WITH ReID EMBEDDINGS) ---
            if object_type == "person":
                embedding = detection.get("embedding", [])
                await self._handle_person_detection(
                    camera_id=camera_id,
                    confidence=confidence,
                    bbox=bbox,
                    crop_path=crop_path,
                    embedding=embedding,
                    timestamp=timestamp
                )
                return

            # --- BRANCH 3: GENERAL OBJECT DETECTIONS ---
            logger.info(f"General object detected: {object_type} on camera {camera_id} with confidence {confidence}")

        except Exception as e:
            logger.error(f"Error executing ProcessTrackingEventUseCase: {e}", exc_info=True)

    async def _handle_person_detection(
        self,
        camera_id: uuid.UUID,
        confidence: float,
        bbox: BoundingBox,
        crop_path: str,
        embedding: list,
        timestamp: datetime
    ):
        """Matches person detections using Qdrant vector search and stores trail logs."""
        person_id: Optional[uuid.UUID] = None
        
        # 1. If ReID embedding is available, perform vector similarity search
        if embedding and len(embedding) == 512:
            matches = self.vector_store.search_similar(
                embedding=embedding,
                limit=1,
                score_threshold=0.75 # Match similarity threshold
            )
            if matches:
                person_id = matches[0]["person_id"]
                logger.info(f"ReID match found! Person ID: {person_id} (Score: {matches[0]['score']})")

        # 2. Get existing or create new Person entity
        if person_id:
            person = await self.person_repo.get_by_id(person_id)
            if person:
                person.update_appearance(timestamp)
                await self.person_repo.upsert_person(person)
            else:
                # Fallback if vector database and SQL DB desynced
                person = Person(id=person_id, first_seen=timestamp, last_seen=timestamp)
                await self.person_repo.upsert_person(person)
        else:
            # Create a completely new identity
            person = Person(first_seen=timestamp, last_seen=timestamp)
            person = await self.person_repo.upsert_person(person)
            person_id = person.id
            logger.info(f"Created new person identity: {person_id}")

            # Index the embedding in Qdrant for future ReID matches
            if embedding and len(embedding) == 512:
                self.vector_store.upsert_embedding(
                    person_id=person_id,
                    embedding=embedding,
                    metadata={"first_seen": timestamp.isoformat()}
                )

        # 3. Save relational tracking event log
        tracking_event = TrackingEvent(
            person_id=person_id,
            camera_id=camera_id,
            confidence=confidence,
            bbox=bbox,
            crop_path=crop_path,
            timestamp=timestamp
        )
        await self.tracking_repo.save_event(tracking_event)

    async def _handle_fire_detection(self, camera_id: uuid.UUID, confidence: float, crop_path: str, timestamp: datetime):
        """Dispatches fire/smoke detection alerts immediately to Kafka."""
        logger.warning(f"CRITICAL: Fire/Smoke detected on camera {camera_id}! Confidence: {confidence}")
        
        alert_payload = {
            "alert_id": str(uuid.uuid4()),
            "type": "fire",
            "severity": "emergency",
            "title": "🚨 Cảnh Báo Hỏa Hoạn!",
            "description": f"Phát hiện dấu hiệu lửa/khói với độ tin cậy {confidence:.2f}!",
            "camera_id": str(camera_id),
            "crop_path": crop_path,
            "timestamp": timestamp.isoformat() + "Z"
        }
        
        # Publish to alert-events Kafka topic immediately
        self.kafka_producer.send_event(
            topic="alert-events",
            key=str(camera_id),
            event_data=alert_payload
        )
