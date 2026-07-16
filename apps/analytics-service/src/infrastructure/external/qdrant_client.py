import os
import logging
import uuid
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

logger = logging.getLogger("analytics_service.qdrant")

class QdrantVectorStore:
    """Infrastructure client wrapper for Qdrant Vector Database operations."""
    def __init__(self):
        host = os.getenv("QDRANT_HOST", "localhost")
        port = int(os.getenv("QDRANT_PORT", "6333"))
        
        # Initialize HTTP client
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = "person_embeddings"
        self._ensure_collection()

    def _ensure_collection(self):
        """Creates the collection for 512-dim OSNet ReID vectors if missing."""
        try:
            collections = self.client.get_collections()
            exist = any(c.name == self.collection_name for c in collections.collections)
            
            if not exist:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=512, # OSNet ReID features size
                        distance=qmodels.Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to check/create Qdrant collection: {e}")

    def upsert_embedding(self, person_id: uuid.UUID, embedding: List[float], metadata: Dict[str, Any]):
        """Inserts or updates a 512-dim embedding associated with a person identity."""
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    qmodels.PointStruct(
                        id=str(person_id),
                        vector=embedding,
                        payload=metadata
                    )
                ]
            )
            logger.debug(f"Upserted embedding vector for person {person_id}")
        except Exception as e:
            logger.error(f"Failed to upsert embedding in Qdrant: {e}")

    def search_similar(self, embedding: List[float], limit: int = 5, score_threshold: float = 0.70) -> List[Dict[str, Any]]:
        """Queries for similar embeddings. Returns list of matches with scores."""
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=embedding,
                limit=limit,
                score_threshold=score_threshold,
                with_payload=True
            )
            
            matches = []
            for res in results:
                matches.append({
                    "person_id": uuid.UUID(res.id),
                    "score": float(res.score),
                    "payload": res.payload
                })
            return matches
        except Exception as e:
            logger.error(f"Failed to query similar vectors in Qdrant: {e}")
            return []
