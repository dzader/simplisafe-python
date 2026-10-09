#!/usr/bin/env python3
"""Simple test to verify camera streaming URL generation without dependencies."""

import sys
import os

# Add the simplipy module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock the required dependencies to test URL generation
class MockDeviceV3:
    def __init__(self, serial):
        self._serial = serial

class MockSystemV3:
    def __init__(self):
        self.camera_data = {
            "test_camera_id": {
                "cameraSettings": {
                    "cameraName": "Test Camera",
                    "shutterAway": "open",
                    "shutterHome": "closed",
                    "shutterOff": "closed"
                },
                "status": "online",
                "subscription": {"enabled": True},
                "model": "SS001"
            }
        }

# Monkey patch the imports
import simplipy.device.camera as camera_module
camera_module.DeviceV3 = MockDeviceV3

from simplipy.device.camera import Camera, StreamFormat

def test_url_generation():
    """Test that camera URL generation works correctly."""

    # Create a mock camera
    camera = Camera()
    camera._serial = "test_camera_id"
    camera._system = MockSystemV3()

    print("Testing URL generation...")

    # Test video URL
    video_url = camera.video_url()
    expected_video = "https://media.simplisafe.com/v1/test_camera_id/flv?x=1280&audioEncoding=AAC"
    assert video_url == expected_video, f"Video URL mismatch: {video_url} != {expected_video}"
    print("✓ Video URL generation works")

    # Test snapshot URL
    snapshot_url = camera.snapshot_url()
    expected_snapshot = "https://media.simplisafe.com/v1/test_camera_id/mjpg?x=1280&fr=1"
    assert snapshot_url == expected_snapshot, f"Snapshot URL mismatch: {snapshot_url} != {expected_snapshot}"
    print("✓ Snapshot URL generation works")

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

    # Test camera properties
    assert camera.name == "Test Camera"
    assert camera.serial == "test_camera_id"
    assert camera.status == "online"
    assert camera.subscription_enabled == True
    assert camera.shutter_open_when_away == True
    assert camera.shutter_open_when_home == False
    assert camera.shutter_open_when_off == False
    print("✓ Camera properties work")

    print("\nAll tests passed! 🎉")
    print("\nGenerated URLs:")
    print(f"Video:    {video_url}")
    print(f"Snapshot: {snapshot_url}")
    print(f"FLV:      {flv_url}")
    print(f"MJPEG:    {mjpeg_url}")

if __name__ == "__main__":
    test_url_generation()
