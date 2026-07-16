from fastapi import APIRouter, Depends, HTTPException, status
from packages.shared.vector.qdrant import QdrantVectorStore
from services.search_service import SearchService
from packages.contracts.dto.search import SearchByImageRequest, SearchResponse, SearchResult
from packages.shared.security import AuthenticatedUser, Role, require_roles

router = APIRouter(prefix="/search", tags=["search"])
require_operator = require_roles(Role.ADMIN, Role.OPERATOR)
qdrant_store = QdrantVectorStore()

# Dependency provider for Qdrant store
def get_qdrant_store() -> QdrantVectorStore:
    return qdrant_store

@router.post("/by-image", response_model=SearchResponse)
async def search_by_image(
    data: SearchByImageRequest,
    current_user: AuthenticatedUser = Depends(require_operator),
    store: QdrantVectorStore = Depends(get_qdrant_store)
):
    """Searches the Qdrant database for similar person identities matching the target ReID vector."""
    if len(data.embedding) != 512:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Embedding vector must be exactly 512 dimensions."
        )
    threshold = data.threshold if data.threshold is not None else 0.70
    limit = data.limit if data.limit is not None else 5
    if threshold < 0.50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Similarity threshold must be 0.50 or higher to prevent resource exhaustion."
        )

    service = SearchService(store)
    matches = await service.search_by_image_embedding(
        embedding=data.embedding,
        limit=limit,
        threshold=threshold
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
