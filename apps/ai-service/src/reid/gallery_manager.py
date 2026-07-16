"""
Qdrant vector store integration for person gallery persistence.
Handles upsert of ReID embeddings and nearest-neighbor search.
"""
from __future__ import annotations
import logging
from typing import List, Optional, Dict, Any
import uuid

logger = logging.getLogger("ai_service.reid.gallery")

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qdrant_models
    _QDRANT_AVAILABLE = True
except ImportError:
    _QDRANT_AVAILABLE = False
    logger.warning("qdrant-client not installed — gallery persistence disabled.")


COLLECTION_NAME = "person_embeddings"
VECTOR_SIZE = 512


class PersonGalleryManager:
    """Persists ReID embeddings in Qdrant.
    Provides upsert and search operations needed by the MTMC associator.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection: str = COLLECTION_NAME,
    ):
        self._collection = collection
        self._client: Optional[Any] = None

        if not _QDRANT_AVAILABLE:
            return

        try:
            self._client = QdrantClient(host=host, port=port)
            self._ensure_collection()
            logger.info(f"Connected to Qdrant at {host}:{port}, "
                        f"collection='{collection}'")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            self._client = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_collection(self):
        """Creates the Qdrant collection if it doesn't already exist."""
        collections = [c.name for c in self._client.get_collections().collections]
        if self._collection not in collections:
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=qdrant_models.VectorParams(
                    size=VECTOR_SIZE,
                    distance=qdrant_models.Distance.COSINE,
                ),
            )
            logger.info(f"Created Qdrant collection '{self._collection}'")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def upsert_embedding(
        self,
        person_uuid: str,
        embedding: List[float],
        payload: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Upserts a 512-d embedding vector for a given person UUID."""
        if not self._client:
            return False
        try:
            # Use a deterministic point_id derived from person_uuid
            point_id = str(uuid.UUID(person_uuid).int % (2**63))
            self._client.upsert(
                collection_name=self._collection,
                points=[
                    qdrant_models.PointStruct(
                        id=int(point_id),
                        vector=embedding,
                        payload={
                            "person_id": person_uuid,
                            **(payload or {}),
                        },
                    )
                ],
            )
            return True
        except Exception as e:
            logger.error(f"Qdrant upsert failed for person {person_uuid}: {e}")
            return False

    def search_similar(
        self,
        embedding: List[float],
        limit: int = 5,
        score_threshold: float = 0.75,
    ) -> List[Dict[str, Any]]:
        """Returns top-k persons most similar to the query embedding."""
        if not self._client:
            return []
        try:
            results = self._client.search(
                collection_name=self._collection,
                query_vector=embedding,
                limit=limit,
                score_threshold=score_threshold,
                with_payload=True,
            )
            return [
                {"person_id": r.payload.get("person_id"), "score": r.score}
                for r in results
            ]
        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            return []

    def delete_person(self, person_uuid: str) -> bool:
        """Deletes a person's embedding from the Qdrant collection."""
        if not self._client:
            return False
        try:
            point_id = int(str(uuid.UUID(person_uuid).int % (2**63)))
            self._client.delete(
                collection_name=self._collection,
                points_selector=qdrant_models.PointIdsList(points=[point_id]),
            )
            return True
        except Exception as e:
            logger.error(f"Qdrant delete failed for {person_uuid}: {e}")
            return False
