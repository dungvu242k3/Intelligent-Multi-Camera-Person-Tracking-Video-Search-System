import os
import tempfile

from src.tracker.nvdcf_tracker import load_tracker_config, NvDCFTrackerConfig


def test_tracker_config_default_values() -> None:
    """Verifies that the NvDCFTrackerConfig instantiates with correct default values."""
    config = NvDCFTrackerConfig()
    assert config.tracker_width == 640
    assert config.tracker_height == 384
    assert config.gpu_id == 0
    assert config.tracker_algorithm == 2  # NvDCF
    assert config.visual_feature_method == 1  # CN
    assert config.max_targets_per_stream == 100
    assert config.min_detector_confidence == 0.25
    assert config.probation_age == 3
    assert config.max_shadow_tracking_age == 30
    assert config.active_min_fps == 15.0
    assert config.search_region_scale == 1.5


def test_load_tracker_config_nonexistent_file() -> None:
    """Verifies that loading a nonexistent file gracefully returns default config."""
    config = load_tracker_config("nonexistent_path.yml")
    assert isinstance(config, NvDCFTrackerConfig)
    assert config.tracker_width == 640


def test_load_tracker_config_valid_file() -> None:
    """Verifies that a valid tracker YAML configuration is correctly loaded and parsed."""
    yaml_content = """
tracker-width: 1280
tracker-height: 720
gpu-id: 1
trackerAlgorithm: 3
visualFeatureMethod: 2
maxTargetsPerStream: 50
minDetectorConfidence: 0.5
probationAge: 5
maxShadowTrackingAge: 15
activeMinFPS: 20.0
searchRegionScale: 2.0
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(yaml_content)
        temp_path = f.name

    try:
        config = load_tracker_config(temp_path)
        assert config.tracker_width == 1280
        assert config.tracker_height == 720
        assert config.gpu_id == 1
        assert config.tracker_algorithm == 3
        assert config.visual_feature_method == 2
        assert config.max_targets_per_stream == 50
        assert config.min_detector_confidence == 0.5
        assert config.probation_age == 5
        assert config.max_shadow_tracking_age == 15
        assert config.active_min_fps == 20.0
        assert config.search_region_scale == 2.0
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
