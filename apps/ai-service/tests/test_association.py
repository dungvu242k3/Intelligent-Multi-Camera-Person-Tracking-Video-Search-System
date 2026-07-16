
from src.reid.mtmc_association import PersonGallery, MTMCAssociator
from src.reid.spatial_constraints import SpatialConstraintValidator, CameraLocation


def test_person_gallery_match_or_create() -> None:
    """Verifies that PersonGallery matches identical/similar embeddings or creates new identities."""
    gallery = PersonGallery(match_threshold=0.75)
    
    # 1. Start empty, add an embedding
    emb1 = [1.0, 0.0]
    pid1, is_new1 = gallery.match_or_create(emb1)
    assert is_new1 is True
    assert gallery.size() == 1
    
    # 2. Add an identical embedding -> should match the first person
    pid2, is_new2 = gallery.match_or_create(emb1)
    assert is_new2 is False
    assert pid2 == pid1
    assert gallery.size() == 1

    # 3. Add an orthogonal embedding -> should create a new person
    emb3 = [0.0, 1.0]
    pid3, is_new3 = gallery.match_or_create(emb3)
    assert is_new3 is True
    assert pid3 != pid1
    assert gallery.size() == 2


def test_mtmc_associator_caching_and_cleanup() -> None:
    """Verifies that MTMCAssociator caches track-to-person resolutions and cleans up old tracks."""
    associator = MTMCAssociator()
    emb = [1.0, 0.0]
    
    # First association -> misses cache, queries gallery
    pid1, is_new1 = associator.associate(camera_id="cam_A", tracking_id=42, embedding=emb)
    assert is_new1 is True
    
    # Second association of the same track -> hit cache immediately without querying gallery
    pid2, is_new2 = associator.associate(camera_id="cam_A", tracking_id=42, embedding=[0.0, 1.0])
    assert is_new2 is False
    assert pid2 == pid1
    
    # Cleanup lost tracks
    # If track (cam_A, 42) is no longer active, it should be removed from the local track_to_person map
    associator.cleanup_lost_tracks(active_keys=[("cam_A", 100)])
    
    # Associate same track again -> since it was cleaned up, it should query gallery and get matched or created
    # Note: we use the same embedding as before, so it matches in the gallery
    pid3, is_new3 = associator.associate(camera_id="cam_A", tracking_id=42, embedding=emb)
    assert is_new3 is False
    assert pid3 == pid1  # same person ID from gallery


def test_spatial_constraint_validator() -> None:
    """Verifies that transitions are validated based on physical distance and walking speed constraints."""
    validator = SpatialConstraintValidator(max_speed_mps=2.0)
    
    # Register two cameras 200m apart
    # Lat/Lon coords representing ~200m distance
    cam_a = CameraLocation(camera_id="cam_A", lat=21.0285, lon=105.8542) # Hanoi center
    cam_b = CameraLocation(camera_id="cam_B", lat=21.0303, lon=105.8542) # ~200m North
    
    validator.register_camera(cam_a)
    validator.register_camera(cam_b)
    
    t1 = "2026-07-16T12:00:00Z"
    
    # Case 1: same camera is always feasible
    assert validator.is_feasible("cam_A", t1, "cam_A", t1) is True
    
    # Case 2: 200m in 10 seconds (20 m/s) -> physically impossible for a walking human (limit is 2.0 m/s)
    t2_impossible = "2026-07-16T12:00:10Z"
    assert validator.is_feasible("cam_A", t1, "cam_B", t2_impossible) is False
    
    # Case 3: 200m in 150 seconds (1.33 m/s) -> physically possible
    t2_possible = "2026-07-16T12:02:30Z"
    assert validator.is_feasible("cam_A", t1, "cam_B", t2_possible) is True
