import asyncio
from unittest.mock import MagicMock, patch
import pytest
from src.stream.decoder import HardwareDecoder
from src.stream.rtsp_source import RTSPSource
from src.stream.stream_manager import StreamManager

def test_rtsp_source_uri_parsing() -> None:
    """Verifies hostname and port are extracted correctly from RTSP URIs."""
    source = RTSPSource(
        camera_id="cam_01",
        uri="rtsp://admin:secretPass@192.168.1.100:8554/stream1",
        name="Gate Camera"
    )
    assert source.host == "192.168.1.100"
    assert source.port == 8554
    assert source.name == "Gate Camera"

def test_rtsp_source_uri_default_port() -> None:
    """Verifies port defaults to 554 if omitted from the RTSP URI."""
    source = RTSPSource(
        camera_id="cam_02",
        uri="rtsp://10.0.0.5/live",
        name="Office Camera"
    )
    assert source.host == "10.0.0.5"
    assert source.port == 554

@patch("socket.create_connection")
def test_rtsp_source_connectivity_success(mock_create_conn: MagicMock) -> None:
    """Verifies check_connectivity returns True when socket connection succeeds."""
    source = RTSPSource(camera_id="cam_01", uri="rtsp://192.168.1.100/live")
    mock_create_conn.return_value = MagicMock()

    assert source.check_connectivity() is True
    assert source.last_status == "connected"

@patch("socket.create_connection")
def test_rtsp_source_connectivity_failure(mock_create_conn: MagicMock) -> None:
    """Verifies check_connectivity returns False when socket connection times out."""
    import socket
    source = RTSPSource(camera_id="cam_01", uri="rtsp://192.168.1.100/live")
    mock_create_conn.side_effect = socket.timeout("Connection timed out")

    assert source.check_connectivity() is False
    assert source.last_status == "offline"

def test_stream_manager_registration() -> None:
    """Verifies registration and deregistration of sources in StreamManager."""
    manager = StreamManager()
    
    # Register source
    source = manager.register_source(
        camera_id="cam_01",
        uri="rtsp://192.168.1.100/live",
        name="Front Door"
    )
    assert manager.get_source("cam_01") == source
    assert len(manager.sources) == 1

    # Deregister source
    deregistered = manager.deregister_source("cam_01")
    assert deregistered == source
    assert manager.get_source("cam_01") is None
    assert len(manager.sources) == 0

@pytest.mark.asyncio
async def test_stream_manager_watchdog_disconnect_callback() -> None:
    """Verifies watchdog loop detects connectivity failure and triggers callback."""
    manager = StreamManager(check_interval_seconds=0.01)
    source = manager.register_source(
        camera_id="cam_01",
        uri="rtsp://192.168.1.100/live"
    )

    # Mock connectivity failure
    source.check_connectivity = MagicMock(return_value=False)

    # Register callback mock
    callback_mock = MagicMock()
    manager.register_disconnect_callback(callback_mock)

    # Run the watchdog loop for a brief moment
    await manager.start_watchdog()
    await asyncio.sleep(0.2)
    await manager.stop_watchdog()

    # Assert callback was called with correct camera_id
    assert callback_mock.call_count >= 1
    callback_mock.assert_any_call("cam_01")

def test_hardware_decoder_configuration() -> None:
    """Verifies HardwareDecoder calls set_property with correct options on GStreamer element."""
    decoder = HardwareDecoder(gpu_id=2)
    mock_element = MagicMock()
    mock_element.get_name.return_value = "mock_nvv4l2decoder"

    decoder.configure_properties(mock_element, skip_frames_level=2)

    # Verify nvv4l2decoder properties set correctly
    mock_element.set_property.assert_any_call("gpu-id", 2)
    mock_element.set_property.assert_any_call("skip-frames", 2)
    mock_element.set_property.assert_any_call("low-latency-mode", 1)
