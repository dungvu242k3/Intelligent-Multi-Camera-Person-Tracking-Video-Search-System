"""
Embedding vector utilities for ReID feature post-processing.
All operations are CPU-side NumPy only (GPU work already done in TensorRT/DeepStream).
"""
from __future__ import annotations
import numpy as np
from typing import List


def l2_normalize(embedding: List[float]) -> List[float]:
    """L2-normalize an embedding vector to unit length.
    Required before cosine-similarity or nearest-neighbour search in Qdrant.
    """
    vec = np.array(embedding, dtype=np.float32)
    norm = np.linalg.norm(vec)
    if norm < 1e-12:
        return embedding  # Zero vector — skip normalization
    return (vec / norm).tolist()


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Returns cosine similarity between two pre-normalized vectors (fast dot product)."""
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    return float(np.dot(va, vb))


def average_embeddings(embeddings: List[List[float]]) -> List[float]:
    """Averages a list of embedding vectors element-wise and L2-normalizes the result.
    Used when merging multiple crops of the same track ID into a single gallery entry.
    """
    if not embeddings:
        return []
    arr = np.array(embeddings, dtype=np.float32)
    mean_vec = arr.mean(axis=0)
    norm = np.linalg.norm(mean_vec)
    if norm < 1e-12:
        return mean_vec.tolist()
    return (mean_vec / norm).tolist()


def embedding_distance(a: List[float], b: List[float]) -> float:
    """Euclidean distance between two embedding vectors (lower = more similar)."""
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    return float(np.linalg.norm(va - vb))
