"""
NvDCF Tracker configuration helper.
Generates/validates the YAML tracker config that DeepStream nvtracker reads at runtime.
"""
from __future__ import annotations
import logging
import os
import yaml
from dataclasses import dataclass


logger = logging.getLogger("ai_service.tracker")


@dataclass
class NvDCFTrackerConfig:
    """Mirrors the fields expected by libnvds_nvmultiobjecttracker.so."""
    # Basic tracker dimensions (must match muxer frame resolution for accuracy)
    tracker_width: int = 640
    tracker_height: int = 384
    gpu_id: int = 0

    # Algorithm: 2 = NvDCF (recommended for accuracy), 3 = IOU (fast)
    tracker_algorithm: int = 2

    # Feature extraction: 1 = Color Names (CN), 2 = HOG, 3 = CNN
    visual_feature_method: int = 1

    # Target management
    max_targets_per_stream: int = 100
    min_detector_confidence: float = 0.25
    probation_age: int = 3             # Frames before track is promoted from probation
    max_shadow_tracking_age: int = 30  # Frames to maintain lost track before deletion
    active_min_fps: float = 15.0

    # Search region
    search_region_scale: float = 1.5


def load_tracker_config(path: str) -> NvDCFTrackerConfig:
    """Reads a tracker YAML config and returns an NvDCFTrackerConfig instance."""
    if not os.path.isfile(path):
        logger.warning(f"Tracker config not found at {path} — using defaults")
        return NvDCFTrackerConfig()

    with open(path, "r") as f:
        raw = yaml.safe_load(f) or {}

    # Map snake_case YAML keys → dataclass fields
    return NvDCFTrackerConfig(
        tracker_width=raw.get("tracker-width", 640),
        tracker_height=raw.get("tracker-height", 384),
        gpu_id=raw.get("gpu-id", 0),
        tracker_algorithm=raw.get("trackerAlgorithm", 2),
        visual_feature_method=raw.get("visualFeatureMethod", 1),
        max_targets_per_stream=raw.get("maxTargetsPerStream", 100),
        min_detector_confidence=raw.get("minDetectorConfidence", 0.25),
        probation_age=raw.get("probationAge", 3),
        max_shadow_tracking_age=raw.get("maxShadowTrackingAge", 30),
        active_min_fps=raw.get("activeMinFPS", 15.0),
        search_region_scale=raw.get("searchRegionScale", 1.5),
    )
