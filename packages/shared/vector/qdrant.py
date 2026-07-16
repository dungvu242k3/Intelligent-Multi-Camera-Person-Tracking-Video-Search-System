import os
import logging
import uuid
from typing import List, Dict, Any
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels

logger = logging.getLogger("shared.qdrant")

class QdrantVectorStore:
    """Infrastructure client wrapper for Qdrant Vector Database operations."""
    def __init__(self):
        host = os.getenv("QDRANT_HOST", "localhost")
        port = int(os.getenv("QDRANT_PORT", "6333"))
        
        self.client = AsyncQdrantClient(host=host, port=port)
        self.collection_name = "person_embeddings"
        self._collection_checked = False

    async def _ensure_collection(self):
        if self._collection_checked:
            return
        try:
            collections = await self.client.get_collections()
            exist = any(c.name == self.collection_name for c in collections.collections)
            
            if not exist:
                await self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=512,
                        distance=qmodels.Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            self._collection_checked = True
        except Exception as e:
            logger.error(f"Failed to check/create Qdrant collection: {e}")
            raise

    async def upsert_embedding(self, person_id: uuid.UUID, embedding: List[float], metadata: Dict[str, Any]):
        await self._ensure_collection()
        try:
            await self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    qmodels.PointStruct(
                        id=str(person_id),
                        vector=embedding,
                        payload=metadata
                    )
                ]
            )
        except Exception as e:
            logger.error(f"Failed to upsert embedding in Qdrant: {e}")
            raise

    async def search_similar(self, embedding: List[float], limit: int = 5, score_threshold: float = 0.70) -> List[Dict[str, Any]]:
        await self._ensure_collection()
        try:
            results = await self.client.search(
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
