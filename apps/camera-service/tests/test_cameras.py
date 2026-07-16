from services.health_checker import RtspHealthChecker

def test_rtsp_host_port_parsing():
    """Verifies that RTSP URL strings are correctly parsed into host and port."""
    checker = RtspHealthChecker(db_session_maker=None)
    
    # Test standard RTSP url
    host, port = checker._parse_rtsp_host_port("rtsp://192.168.1.100:554/stream1")
    assert host == "192.168.1.100"
    assert port == 554

    # Test RTSP url with credentials
    host, port = checker._parse_rtsp_host_port("rtsp://admin:pass123@mycamera.local:8554/live")
    assert host == "mycamera.local"
    assert port == 8554

    # Test RTSP url without explicit port (default 554)
    host, port = checker._parse_rtsp_host_port("rtsp://10.0.0.5/live")
    assert host == "10.0.0.5"
    assert port == 554
