"""
Non-Maximum Suppression (NMS) — CPU implementation for post-processing.
Used by custom_parser when DeepStream's built-in NMS is not applicable.
"""
from __future__ import annotations
from typing import List, Tuple
import numpy as np


def nms(
    boxes: List[Tuple[float, float, float, float]],
    scores: List[float],
    iou_threshold: float = 0.45,
) -> List[int]:
    """Standard NMS — returns indices of surviving boxes (sorted by score desc).
    
    Args:
        boxes: list of (x_min, y_min, x_max, y_max) in absolute or normalized coords
        scores: confidence scores per box
        iou_threshold: boxes with IoU > threshold are suppressed

    Returns:
        List of surviving box indices
    """
    if not boxes:
        return []

    boxes_arr = np.array(boxes, dtype=np.float32)
    scores_arr = np.array(scores, dtype=np.float32)

    x1 = boxes_arr[:, 0]
    y1 = boxes_arr[:, 1]
    x2 = boxes_arr[:, 2]
    y2 = boxes_arr[:, 3]
    areas = (x2 - x1) * (y2 - y1)

    order = scores_arr.argsort()[::-1]
    keep = []

    while order.size > 0:
        i = order[0]
        keep.append(int(i))

        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        inter_w = np.maximum(0.0, xx2 - xx1)
        inter_h = np.maximum(0.0, yy2 - yy1)
        inter_area = inter_w * inter_h

        iou = inter_area / (areas[i] + areas[order[1:]] - inter_area + 1e-9)
        surviving = np.where(iou <= iou_threshold)[0]
        order = order[surviving + 1]

    return keep


def soft_nms(
    boxes: List[Tuple[float, float, float, float]],
    scores: List[float],
    iou_threshold: float = 0.45,
    sigma: float = 0.5,
    score_threshold: float = 0.001,
) -> List[int]:
    """Soft-NMS with Gaussian weight decay (better for crowded scenes)."""
    if not boxes:
        return []

    boxes_arr = np.array(boxes, dtype=np.float32)
    scores_arr = np.array(scores, dtype=np.float32).copy()
    indices = list(range(len(boxes)))
    keep = []

    while len(indices) > 0:
        max_idx = int(np.argmax(scores_arr[indices]))
        i = indices[max_idx]
        keep.append(i)
        indices.pop(max_idx)

        for j in list(indices):
            x1 = max(boxes_arr[i, 0], boxes_arr[j, 0])
            y1 = max(boxes_arr[i, 1], boxes_arr[j, 1])
            x2 = min(boxes_arr[i, 2], boxes_arr[j, 2])
            y2 = min(boxes_arr[i, 3], boxes_arr[j, 3])
            inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
            area_i = (boxes_arr[i, 2] - boxes_arr[i, 0]) * (boxes_arr[i, 3] - boxes_arr[i, 1])
            area_j = (boxes_arr[j, 2] - boxes_arr[j, 0]) * (boxes_arr[j, 3] - boxes_arr[j, 1])
            iou = inter / (area_i + area_j - inter + 1e-9)
            scores_arr[j] *= np.exp(-(iou ** 2) / sigma)
            if scores_arr[j] < score_threshold:
                indices.remove(j)

    return keep
