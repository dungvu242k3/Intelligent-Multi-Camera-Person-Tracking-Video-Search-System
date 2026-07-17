import sys
import os

# Setup paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../apps/search-service/src")))

# Evict config/service modules to prevent collision
for mod in ["api", "config", "services", "models", "events"]:
    sys.modules.pop(mod, None)
    for key in list(sys.modules.keys()):
        if key.startswith(f"{mod}."):
            sys.modules.pop(key, None)

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from services.search_service import SearchService
from api.search_routes import search_by_image
from packages.contracts.dto.search import SearchByImageRequest

@pytest.mark.asyncio
async def test_search_service_queries_qdrant_vector_store():
    """Verifies that SearchService properly passes query vectors to Qdrant."""
    # Arrange
    mock_store = AsyncMock()
    mock_store.search_similar.return_value = [
        {"person_id": "p-1234", "score": 0.94, "payload": {"name": "Test Subject"}}
    ]

    service = SearchService(mock_store)
    query_vector = [0.2] * 512

    # Act
    results = await service.search_by_image_embedding(query_vector, limit=3, threshold=0.80)

    # Assert
    assert len(results) == 1
    assert results[0]["person_id"] == "p-1234"
    assert results[0]["score"] == 0.94
    mock_store.search_similar.assert_called_once_with(
        embedding=query_vector,
        limit=3,
        score_threshold=0.80
    )

@pytest.mark.asyncio
async def test_search_by_image_route_validation():
    """Verifies search endpoint validates input embedding dimensions and thresholds."""
    from pydantic import ValidationError
    # Pydantic validates dimensions at constructor/serializer level in pydantic v2
    # So creating the object with invalid size will raise ValidationError
    with pytest.raises(ValidationError):
        SearchByImageRequest(
            embedding=[0.1] * 100, # 100 dimensions instead of 512
            limit=5,
            threshold=0.75
        )

@pytest.mark.asyncio
async def test_search_by_image_validation_bounds():
    """Verifies validation bounds on threshold and limits."""
    # Threshold below 0.50 should fail custom route validation
    request = SearchByImageRequest(
        embedding=[0.0] * 512,
        limit=5,
        threshold=0.45 # Below 0.50 threshold
    )
    mock_store = AsyncMock()
    mock_user = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        await search_by_image(request, current_user=mock_user, store=mock_store)
    
    assert exc_info.value.status_code == 400
    assert "threshold must be 0.50 or higher" in exc_info.value.detail
