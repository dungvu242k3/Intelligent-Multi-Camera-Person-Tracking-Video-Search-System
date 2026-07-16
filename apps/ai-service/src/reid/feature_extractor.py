"""
ReID Feature Extractor — post-processes raw DeepStream SGIE tensor output
into normalized 512-d embedding vectors stored in a per-camera gallery.

DeepStream extracts features inside CUDA; this module handles CPU-side post-processing.
"""
from __future__ import annotations
import ctypes
import logging
from typing import List, Optional


try:
    import pyds
    _PYDS_AVAILABLE = True
except ImportError:
    _PYDS_AVAILABLE = False

from utils.embedding import l2_normalize

logger = logging.getLogger("ai_service.reid")

# Output layer name configured in sgie_reid.txt  →  output-blob-names=features
REID_LAYER_NAME = "features"
EMBEDDING_DIM = 512


def extract_embedding_from_obj_meta(obj_meta) -> List[float]:
    """Extracts a 512-d L2-normalized ReID embedding from DeepStream object metadata.
    
    The SGIE ReID model writes output tensors into `obj_meta.obj_user_meta_list`
    as `NvDsInferTensorMeta` entries. This function walks that linked list,
    finds the `features` layer, and returns a float list.

    Returns empty list if no tensor output is found.
    """
    if not _PYDS_AVAILABLE:
        return []

    l_user = obj_meta.obj_user_meta_list
    while l_user is not None:
        try:
            user_meta = pyds.NvDsUserMeta.cast(l_user.data)
        except StopIteration:
            break

        if user_meta.base_meta.meta_type == pyds.NVDSINFER_TENSOR_OUTPUT_META:
            try:
                tensor_meta = pyds.NvDsInferTensorMeta.cast(user_meta.user_meta_data)
                for i in range(tensor_meta.num_output_layers):
                    layer = pyds.get_nvds_LayerInfo(tensor_meta, i)
                    if layer.layerName == REID_LAYER_NAME:
                        raw_ptr = layer.buffer
                        float_arr = ctypes.cast(
                            raw_ptr,
                            ctypes.POINTER(ctypes.c_float * EMBEDDING_DIM)
                        ).contents
                        raw_embedding = [float(x) for x in float_arr]
                        return l2_normalize(raw_embedding)
            except Exception as e:
                logger.error(f"Error parsing ReID tensor metadata: {e}")

        try:
            l_user = l_user.next
        except StopIteration:
            break

    return []


class ReIDFeatureExtractor:
    """High-level helper that wraps the raw tensor extraction logic.
    Validates the embedding dimension and applies L2 normalization.
    """

    def __init__(self, embedding_dim: int = EMBEDDING_DIM):
        self.embedding_dim = embedding_dim

    def extract(self, obj_meta) -> Optional[List[float]]:
        """Returns L2-normalized embedding or None if extraction fails."""
        embedding = extract_embedding_from_obj_meta(obj_meta)
        if not embedding:
            return None
        if len(embedding) != self.embedding_dim:
            logger.warning(
                f"Unexpected embedding dimension: got {len(embedding)}, "
                f"expected {self.embedding_dim}"
            )
            return None
        return embedding
