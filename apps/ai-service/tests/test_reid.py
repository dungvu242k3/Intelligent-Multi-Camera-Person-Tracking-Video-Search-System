from unittest.mock import MagicMock, patch
import pytest
from src.utils.embedding import l2_normalize, cosine_similarity, average_embeddings, embedding_distance
from src.reid.feature_extractor import ReIDFeatureExtractor


def test_l2_normalize_valid_vector() -> None:
    """Verifies that vector is normalized to unit length."""
    vec = [3.0, 4.0]
    normed = l2_normalize(vec)
    assert normed == pytest.approx([0.6, 0.8])


def test_l2_normalize_zero_vector() -> None:
    """Verifies that zero vector returns original vector without throwing division-by-zero."""
    vec = [0.0, 0.0]
    normed = l2_normalize(vec)
    assert normed == [0.0, 0.0]


def test_cosine_similarity() -> None:
    """Verifies cosine similarity dot product calculation for identical and orthogonal vectors."""
    a = [1.0, 0.0]
    b = [1.0, 0.0]
    c = [0.0, 1.0]
    assert pytest.approx(cosine_similarity(a, b)) == 1.0
    assert pytest.approx(cosine_similarity(a, c)) == 0.0


def test_average_embeddings() -> None:
    """Verifies average embedding merges multiple vectors element-wise and normalizes."""
    vecs = [
        [1.0, 0.0],
        [0.0, 1.0]
    ]
    avg = average_embeddings(vecs)
    # Average of vectors: [0.5, 0.5] -> L2 normalized: [sqrt(0.5), sqrt(0.5)]
    expected = [0.5 ** 0.5, 0.5 ** 0.5]
    assert pytest.approx(avg[0]) == expected[0]
    assert pytest.approx(avg[1]) == expected[1]


def test_embedding_distance() -> None:
    """Verifies Euclidean distance between vectors."""
    a = [0.0, 0.0]
    b = [3.0, 4.0]
    assert pytest.approx(embedding_distance(a, b)) == 5.0


def test_reid_extractor_dimension_validation() -> None:
    """Verifies ReIDFeatureExtractor rejects embeddings that don't match configured dimension."""
    extractor = ReIDFeatureExtractor(embedding_dim=512)
    
    # Mock obj_meta
    obj_meta = MagicMock()
    
    # Override extract_embedding_from_obj_meta to return a mock vector
    with patch("src.reid.feature_extractor.extract_embedding_from_obj_meta") as mock_extract:
        # Invalid dimension case
        mock_extract.return_value = [0.1] * 256
        res = extractor.extract(obj_meta)
        assert res is None
        
        # Valid dimension case
        mock_extract.return_value = [0.1] * 512
        res = extractor.extract(obj_meta)
        assert res == [0.1] * 512
