from fastapi import APIRouter, Depends, HTTPException, status
from packages.shared.vector.qdrant import QdrantVectorStore
from services.search_service import SearchService
from packages.contracts.dto.search import SearchByImageRequest, SearchResponse, SearchResult

router = APIRouter(prefix="/search", tags=["search"])

# Dependency provider for Qdrant store
def get_qdrant_store() -> QdrantVectorStore:
    return QdrantVectorStore()

@router.post("/by-image", response_model=SearchResponse)
async def search_by_image(
    data: SearchByImageRequest,
    store: QdrantVectorStore = Depends(get_qdrant_store)
):
    """Searches the Qdrant database for similar person identities matching the target ReID vector."""
    if len(data.embedding) != 512:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Embedding vector must be exactly 512 dimensions."
        )
    if data.threshold < 0.50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Similarity threshold must be 0.50 or higher to prevent resource exhaustion."
        )

    service = SearchService(store)
    matches = await service.search_by_image_embedding(
        embedding=data.embedding,
        limit=data.limit,
        threshold=data.threshold
    )

    results = []
    for match in matches:
        results.append(
            SearchResult(
                person_id=str(match["person_id"]),
                score=match["score"],
                payload=match.get("payload", {})
            )
        )

    return SearchResponse(results=results)
