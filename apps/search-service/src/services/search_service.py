import logging
from typing import List, Dict, Any
from packages.shared.vector.qdrant import QdrantVectorStore

logger = logging.getLogger("search_service.business")

class SearchService:
    """Orchestrates similarity search algorithms on Qdrant database."""
    def __init__(self, vector_store: QdrantVectorStore):
        self.vector_store = vector_store

    async def search_by_image_embedding(self, embedding: List[float], limit: int = 10, threshold: float = 0.70) -> List[Dict[str, Any]]:
        """Queries for visually matching persons using vector embeddings."""
        if not embedding or len(embedding) != 512:
            logger.warning(f"Invalid embedding dimension size submitted: {len(embedding)}")
            return []
            
        # Await the async vector query
        matches = await self.vector_store.search_similar(
            embedding=embedding,
            limit=limit,
            score_threshold=threshold
        )
        return matches
