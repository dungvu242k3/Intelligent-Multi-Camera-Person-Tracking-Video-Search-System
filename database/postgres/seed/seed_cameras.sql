-- =====================================================
-- Seed: Sample Cameras
-- Multi-Camera Person Tracking System
-- =====================================================
-- Sample cameras for development and testing.
-- RTSP URLs use rtsp://localhost pattern — replace in production.
-- =====================================================

INSERT INTO cameras (id, name, rtsp_url, location, status, fps)
VALUES
    (
        uuid_generate_v4(),
        'Entrance Camera - Main Gate',
        'rtsp://192.168.1.101:554/stream1',
        'Building A - Main Entrance',
        'DISCONNECTED',
        25
    ),
    (
        uuid_generate_v4(),
        'Parking Lot Camera - Zone A',
        'rtsp://192.168.1.102:554/stream1',
        'Outdoor Parking - Zone A',
        'DISCONNECTED',
        15
    ),
    (
        uuid_generate_v4(),
        'Lobby Camera - Floor 1',
        'rtsp://192.168.1.103:554/ch01',
        'Building A - Lobby Level 1',
        'DISCONNECTED',
        30
    )
ON CONFLICT (rtsp_url) DO NOTHING;
