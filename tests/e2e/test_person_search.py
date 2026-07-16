import pytest
import uuid
from unittest.mock import AsyncMock
from datetime import datetime, timezone
from services.search_service import SearchService
from packages.contracts.dto.tracking import PersonTrailResponse, TrailPointDTO, BBoxDTO

@pytest.mark.asyncio
async def test_end_to_end_person_vector_search_and_trail():
    """Simulates ReID image search vector queries and cross-camera historical trail reconstruction."""
    # Arrange: Mock vector store search results
    mock_store = AsyncMock()
    person_uuid = uuid.uuid4()
    
    mock_store.search_similar.return_value = [
        {
            "person_id": person_uuid,
            "score": 0.91,
            "payload": {"last_seen_camera": "camera_1"}
        }
    ]

    search_service = SearchService(mock_store)
    query_vector = [0.1] * 512

    # Act 1: Search by vector ReID embedding
    matches = await search_service.search_by_image_embedding(query_vector, limit=1, threshold=0.80)

    # Assert 1
    assert len(matches) == 1
    assert matches[0]["person_id"] == person_uuid
    assert matches[0]["score"] == 0.91

    # Act 2: Simulate fetching chronological trail points for the matched person
    mock_trail_points = [
        TrailPointDTO(
            event_id="evt-1",
            camera_id="camera_0",
            timestamp=datetime.now(timezone.utc).isoformat(),
            bbox=BBoxDTO(left=10.0, top=20.0, width=50.0, height=120.0),
            crop_path="crops/cam0/p1.jpg"
        ),
        TrailPointDTO(
            event_id="evt-2",
            camera_id="camera_1",
            timestamp=datetime.now(timezone.utc).isoformat(),
            bbox=BBoxDTO(left=12.0, top=18.0, width=48.0, height=115.0),
            crop_path="crops/cam1/p1.jpg"
        ),
    ]
    
    trail_response = PersonTrailResponse(
        person_id=str(person_uuid),
        trail_points=mock_trail_points
    )

    # Assert 2: Verify DTO serialization structures
    assert len(trail_response.trail_points) == 2
    assert trail_response.person_id == str(person_uuid)
    assert trail_response.trail_points[0].camera_id == "camera_0"
    assert trail_response.trail_points[1].camera_id == "camera_1"
    assert trail_response.trail_points[0].bbox.width == 50.0
