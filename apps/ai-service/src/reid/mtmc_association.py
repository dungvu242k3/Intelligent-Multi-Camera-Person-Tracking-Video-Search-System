"""
Multi-Target Multi-Camera (MTMC) Person Re-Identification Association.

Core algorithm:
  1. Maintain an in-memory gallery of known persons (person_id → avg embedding).
  2. For each new embedding received from a camera, compute cosine similarity against all gallery entries.
  3. If similarity > MATCH_THRESHOLD → same person (re-identify cross-camera).
  4. If no match → new person (assign new UUID, create gallery entry).
  5. Periodically flush updated embeddings to Qdrant vector store.
"""
from __future__ import annotations
import logging
import threading
import uuid

from typing import Dict, List, Optional, Tuple



from utils.embedding import cosine_similarity, average_embeddings

logger = logging.getLogger("ai_service.mtmc")

# Cosine similarity threshold — above this value = same person
MATCH_THRESHOLD = 0.75
# Maximum gallery entries per person (rolling window to handle appearance drift)
MAX_EMBEDDINGS_PER_PERSON = 10


class PersonGallery:
    """Thread-safe in-memory Re-ID gallery.
    Maps person_uuid → list of recent embedding vectors.
    """

    def __init__(self, match_threshold: float = MATCH_THRESHOLD):
        self.threshold = match_threshold
        self._gallery: Dict[str, List[List[float]]] = {}  # person_id → embeddings
        self._lock = threading.Lock()

    def match_or_create(self, embedding: List[float]) -> Tuple[str, bool]:
        """Finds the best matching person or creates a new gallery entry.
        
        Returns:
            (person_id, is_new_person)
        """
        with self._lock:
            best_id: Optional[str] = None
            best_sim: float = -1.0

            for person_id, embeddings in self._gallery.items():
                avg_emb = average_embeddings(embeddings)
                sim = cosine_similarity(embedding, avg_emb)
                if sim > best_sim:
                    best_sim = sim
                    best_id = person_id

            if best_id and best_sim >= self.threshold:
                # Existing person — update gallery with new embedding sample
                self._gallery[best_id].append(embedding)
                if len(self._gallery[best_id]) > MAX_EMBEDDINGS_PER_PERSON:
                    self._gallery[best_id].pop(0)  # Sliding window
                logger.debug(
                    f"Re-identified person {best_id} (similarity={best_sim:.4f})"
                )
                return best_id, False
            else:
                # New person
                new_id = str(uuid.uuid4())
                self._gallery[new_id] = [embedding]
                logger.info(
                    f"New person registered: {new_id} "
                    f"(best_sim={best_sim:.4f}, threshold={self.threshold})"
                )
                return new_id, True

    def get_average_embedding(self, person_id: str) -> Optional[List[float]]:
        """Returns the averaged (gallery) embedding for a known person."""
        with self._lock:
            embeddings = self._gallery.get(person_id)
            if not embeddings:
                return None
            return average_embeddings(embeddings)

    def size(self) -> int:
        with self._lock:
            return len(self._gallery)

    def all_ids(self) -> List[str]:
        with self._lock:
            return list(self._gallery.keys())


class MTMCAssociator:
    """High-level MTMC orchestrator.
    
    Associates tracking_id (per-camera local ID) with global person_uuid via
    embedding similarity. Maintains a per-camera map to avoid redundant Qdrant
    lookups for already-identified tracks.
    """

    def __init__(self, gallery: Optional[PersonGallery] = None):
        self.gallery = gallery or PersonGallery()
        # (camera_id, tracking_id) → person_uuid
        self._track_to_person: Dict[Tuple[str, int], str] = {}
        self._lock = threading.Lock()

    def associate(
        self,
        camera_id: str,
        tracking_id: int,
        embedding: List[float],
    ) -> Tuple[str, bool]:
        """Resolves a (camera, track) pair to a global person UUID.
        
        Returns:
            (person_uuid, is_new_person)
        """
        key = (camera_id, tracking_id)

        with self._lock:
            # Cache hit — track already resolved during this session
            if key in self._track_to_person:
                return self._track_to_person[key], False

        # Gallery match (may create new person)
        person_id, is_new = self.gallery.match_or_create(embedding)

        with self._lock:
            self._track_to_person[key] = person_id

        return person_id, is_new

    def cleanup_lost_tracks(self, active_keys: List[Tuple[str, int]]):
        """Removes stale track→person mappings for tracks that no longer exist."""
        with self._lock:
            stale = [k for k in self._track_to_person if k not in active_keys]
            for k in stale:
                del self._track_to_person[k]
        if stale:
            logger.debug(f"Cleaned up {len(stale)} stale track mappings")
