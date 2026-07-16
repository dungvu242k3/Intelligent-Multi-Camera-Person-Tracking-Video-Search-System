"""
Bounding-box utility functions used by crop_saver and MTMC association.
"""
from __future__ import annotations
from typing import Tuple
import numpy as np


def clip_bbox(left: float, top: float, width: float, height: float,
              frame_w: int, frame_h: int) -> Tuple[int, int, int, int]:
    """Clips bbox coordinates to image boundaries.
    Returns (x_min, y_min, x_max, y_max) in integer pixel coordinates.
    """
    x_min = max(0, int(left))
    y_min = max(0, int(top))
    x_max = min(frame_w, int(left + width))
    y_max = min(frame_h, int(top + height))
    return x_min, y_min, x_max, y_max


def bbox_iou(a: Tuple[float, float, float, float],
             b: Tuple[float, float, float, float]) -> float:
    """Intersection-over-Union for two (x_min, y_min, x_max, y_max) boxes."""
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    if inter_x2 <= inter_x1 or inter_y2 <= inter_y1:
        return 0.0
    inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    union = area_a + area_b - inter_area
    return inter_area / union if union > 0 else 0.0


def bbox_area(left: float, top: float, width: float, height: float) -> float:
    return max(0.0, width) * max(0.0, height)


def bbox_center(left: float, top: float, width: float, height: float) -> Tuple[float, float]:
    return left + width / 2.0, top + height / 2.0
