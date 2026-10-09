#!/usr/bin/env python3
"""Direct test of camera streaming functionality without external dependencies."""

import sys
import os
from enum import Enum
from typing import Any, cast
from urllib.parse import urlencode

# Define the constants
DEFAULT_AUDIO_ENCODING = "AAC"
DEFAULT_MEDIA_URL_BASE = "https://media.simplisafe.com/v1"
DEFAULT_VIDEO_WIDTH = 1280
DEFAULT_SNAPSHOT_WIDTH = 1280


class StreamFormat(Enum):
    """Define supported stream formats."""
    FLV = "flv"
    MJPEG = "mjpg"


class CameraTypes(Enum):
    """Define camera types based on internal SimpliSafe ID number."""
    CAMERA = 0
    DOORBELL = 1
    OUTDOOR_CAMERA = 2
    UNKNOWN = 99


MODEL_TO_TYPE = {
    "SS001": CameraTypes.CAMERA,
    "SS002": CameraTypes.DOORBELL,
    "SS003": CameraTypes.CAMERA,
    "SSOBCM4": CameraTypes.OUTDOOR_CAMERA,
}


class MockCamera:
    """Mock camera class to test URL generation."""

    def __init__(self, serial: str):
        self.serial = serial
        self._system = MockSystem()

    def video_url(
        self,
        width: int = DEFAULT_VIDEO_WIDTH,
        audio_encoding: str = DEFAULT_AUDIO_ENCODING,
        **kwargs: Any,
    ) -> str:
        """Return the camera video URL."""
        url_params = {"x": width, "audioEncoding": audio_encoding, **kwargs}
        return f"{DEFAULT_MEDIA_URL_BASE}/{self.serial}/flv?{urlencode(url_params)}"

    def snapshot_url(
        self,
        width: int = DEFAULT_SNAPSHOT_WIDTH,
        **kwargs: Any,
    ) -> str:
        """Return the camera snapshot URL."""
        url_params = {"x": width, "fr": 1, **kwargs}
        return f"{DEFAULT_MEDIA_URL_BASE}/{self.serial}/mjpg?{urlencode(url_params)}"

    def stream_url(
        self,
        format_type: StreamFormat = StreamFormat.FLV,
        width: int = DEFAULT_VIDEO_WIDTH,
        audio_encoding: str = DEFAULT_AUDIO_ENCODING,
        **kwargs: Any,
    ) -> str:
        """Return the camera stream URL for different formats."""
        if format_type == StreamFormat.FLV:
            url_params = {"x": width, "audioEncoding": audio_encoding, **kwargs}
        elif format_type == StreamFormat.MJPEG:
            url_params = {"x": width, **kwargs}
        else:
            raise ValueError(f"Unsupported stream format: {format_type}")

        return f"{DEFAULT_MEDIA_URL_BASE}/{self.serial}/{format_type.value}?{urlencode(url_params)}"


class MockSystem:
    """Mock system for testing."""

    def __init__(self):
        self.camera_data = {
            "test_camera_id": {
                "cameraSettings": {
                    "cameraName": "Test Camera"
                }
            }
        }


def test_url_generation():
    """Test that camera URL generation works correctly."""

    print("Testing SimpliSafe Camera Streaming URL generation...")
    print("=" * 60)

    # Create a mock camera
    camera = MockCamera("test_camera_id")

    # Test video URL
    video_url = camera.video_url()
    expected_video = "https://media.simplisafe.com/v1/test_camera_id/flv?x=1280&audioEncoding=AAC"
    assert video_url == expected_video, f"Video URL mismatch: {video_url} != {expected_video}"
    print("✓ Video URL generation works")

    # Test video URL with custom parameters
    video_url_custom = camera.video_url(width=720, audio_encoding="OPUS")
    expected_video_custom = "https://media.simplisafe.com/v1/test_camera_id/flv?x=720&audioEncoding=OPUS"
    assert video_url_custom == expected_video_custom
    print("✓ Video URL with custom parameters works")

    # Test snapshot URL
    snapshot_url = camera.snapshot_url()
    expected_snapshot = "https://media.simplisafe.com/v1/test_camera_id/mjpg?x=1280&fr=1"
    assert snapshot_url == expected_snapshot, f"Snapshot URL mismatch: {snapshot_url} != {expected_snapshot}"
    print("✓ Snapshot URL generation works")

    # Test snapshot URL with custom width
    snapshot_url_custom = camera.snapshot_url(width=640)
    expected_snapshot_custom = "https://media.simplisafe.com/v1/test_camera_id/mjpg?x=640&fr=1"
    assert snapshot_url_custom == expected_snapshot_custom
    print("✓ Snapshot URL with custom width works")

    # Test stream URL - FLV
    flv_url = camera.stream_url(StreamFormat.FLV, width=720, audio_encoding="OPUS")
    expected_flv = "https://media.simplisafe.com/v1/test_camera_id/flv?x=720&audioEncoding=OPUS"
    assert flv_url == expected_flv, f"FLV URL mismatch: {flv_url} != {expected_flv}"
    print("✓ FLV stream URL generation works")

    # Test stream URL - MJPEG
    mjpeg_url = camera.stream_url(StreamFormat.MJPEG, width=640)
    expected_mjpeg = "https://media.simplisafe.com/v1/test_camera_id/mjpg?x=640"
    assert mjpeg_url == expected_mjpeg, f"MJPEG URL mismatch: {mjpeg_url} != {expected_mjpeg}"
    print("✓ MJPEG stream URL generation works")

    # Test stream URL with additional parameters
    flv_url_extra = camera.stream_url(StreamFormat.FLV, width=1920, custom_param="test")
    expected_flv_extra = "https://media.simplisafe.com/v1/test_camera_id/flv?x=1920&audioEncoding=AAC&custom_param=test"
    assert flv_url_extra == expected_flv_extra
    print("✓ Stream URL with additional parameters works")

    # Test unsupported format error
    try:
        class UnsupportedFormat(Enum):
            INVALID = "invalid"
        camera.stream_url(UnsupportedFormat.INVALID)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unsupported stream format" in str(e)
        print("✓ Unsupported format error handling works")

    print("\n" + "=" * 60)
    print("All tests passed! 🎉")
    print("\nExample Generated URLs:")
    print("-" * 30)
    print(f"Video (default):     {video_url}")
    print(f"Video (custom):      {video_url_custom}")
    print(f"Snapshot (default):  {snapshot_url}")
    print(f"Snapshot (custom):   {snapshot_url_custom}")
    print(f"FLV stream:          {flv_url}")
    print(f"MJPEG stream:        {mjpeg_url}")
    print(f"FLV with extras:     {flv_url_extra}")

    print("\nStream Format Support:")
    print("-" * 30)
    print(f"FLV format:   {StreamFormat.FLV.value} (supports audio)")
    print(f"MJPEG format: {StreamFormat.MJPEG.value} (video only)")

    print("\nAudio Encoding Options:")
    print("-" * 30)
    print("• AAC (default) - Advanced Audio Coding")
    print("• OPUS - Open source audio codec")
    print("• Empty string - Uses Speex codec")


if __name__ == "__main__":
    test_url_generation()
