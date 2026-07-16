import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

# Import target
from src.jobs.cleanup_job import execute_cleanup_job
from src.config.settings import settings


@pytest.mark.asyncio
@patch("src.jobs.cleanup_job.create_async_engine")
@patch("src.jobs.cleanup_job.MinioStorageClient")
@patch("src.jobs.cleanup_job.QdrantVectorStore")
async def test_execute_cleanup_job_flows(
    mock_qdrant_cls: MagicMock,
    mock_minio_cls: MagicMock,
    mock_create_engine: MagicMock
) -> None:
    """Verifies that cleanup job queries the database and invokes deletion methods on MinIO and Qdrant."""
    # 1. Setup Mock clients
    mock_qdrant = MagicMock()
    mock_qdrant.delete_embeddings = AsyncMock()
    mock_qdrant_cls.return_value = mock_qdrant

    mock_minio = MagicMock()
    mock_minio.delete_object = MagicMock()
    mock_minio_cls.return_value = mock_minio

    # 2. Setup mock DB session
    mock_session = AsyncMock()
    
    # Mock data returned by DB
    mock_tracking_rows = [
        ("id1", "person_1", "detection-crops/person/id1.jpg"),
        ("id2", "person_2", "detection-crops/person/id2.jpg")
    ]
    mock_fire_rows = [
        ("id3", "detection-crops/fire/id3.jpg")
    ]
    mock_person_rows = [
        ("person_1",),
        ("person_2",)
    ]

    # Configure session execute return values
    mock_result_tracking = MagicMock()
    mock_result_tracking.all.return_value = mock_tracking_rows

    mock_result_fire = MagicMock()
    mock_result_fire.all.return_value = mock_fire_rows

    mock_result_person = MagicMock()
    mock_result_person.all.return_value = mock_person_rows

    # Mock execute calls sequentially
    mock_session.execute.side_effect = [
        mock_result_tracking,
        mock_result_fire,
        mock_result_person,
        MagicMock(rowcount=0), # for alert delete
        MagicMock(), # for tracking_events delete
        MagicMock(), # for fire_events delete
        MagicMock(), # for persons delete
    ]

    # Patch local get_session_maker function in cleanup_job module
    with patch("src.jobs.cleanup_job.get_session_maker") as mock_get_session_maker:
        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__.return_value = mock_session
        mock_get_session_maker.return_value = mock_session_maker
        
        # 3. Execute
        await execute_cleanup_job()

        # 4. Assert Qdrant delete was called with expired person IDs
        mock_qdrant.delete_embeddings.assert_called_once_with(["person_1", "person_2"])

        # 5. Assert MinIO deletes were called
        # Crops: detection-crops/person/id1.jpg, detection-crops/person/id2.jpg, detection-crops/fire/id3.jpg
        assert mock_minio.delete_object.call_count == 3
        mock_minio.delete_object.assert_any_call("detection-crops", "person/id1.jpg")
        mock_minio.delete_object.assert_any_call("detection-crops", "person/id2.jpg")
        mock_minio.delete_object.assert_any_call("detection-crops", "fire/id3.jpg")

        # 6. Assert DB commit was called
        mock_session.commit.assert_called_once()
