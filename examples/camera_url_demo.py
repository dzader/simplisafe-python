#!/usr/bin/env python3
"""
Demo script showing SimpliSafe camera streaming URL formats.

This script demonstrates the URL formats used for SimpliSafe camera streaming
without requiring actual authentication. It shows how the library generates
URLs for different streaming scenarios.
"""

from urllib.parse import urlencode

# Constants from the library
DEFAULT_AUDIO_ENCODING = "AAC"
DEFAULT_MEDIA_URL_BASE = "https://media.simplisafe.com/v1"
DEFAULT_VIDEO_WIDTH = 1280


def demo_camera_urls():
    """Demonstrate SimpliSafe camera URL generation."""

    print("SimpliSafe Camera Streaming URL Demo")
    print("=" * 50)
    print()

    # Example camera UUID (this would come from your actual camera)
    camera_uuid = "your-camera-uuid-here"

    print(f"Camera UUID: {camera_uuid}")
    print()

    # Basic video streaming URL (FLV format with audio)
    print("1. Basic Video Streaming (FLV with AAC audio):")
    video_params = {"x": 1280, "audioEncoding": "AAC"}
    video_url = f"{DEFAULT_MEDIA_URL_BASE}/{camera_uuid}/flv?{urlencode(video_params)}"
    print(f"   {video_url}")
    print("   - Format: FLV (Flash Video)")
    print("   - Resolution: 1280px wide")
    print("   - Audio: AAC encoding")
    print()

    # Lower resolution streaming
    print("2. Lower Resolution Streaming (720p):")
    video_720_params = {"x": 720, "audioEncoding": "AAC"}
    video_720_url = f"{DEFAULT_MEDIA_URL_BASE}/{camera_uuid}/flv?{urlencode(video_720_params)}"
    print(f"   {video_720_url}")
    print("   - Better for slower connections")
    print()

    # OPUS audio encoding
    print("3. Alternative Audio Encoding (OPUS):")
    opus_params = {"x": 1280, "audioEncoding": "OPUS"}
    opus_url = f"{DEFAULT_MEDIA_URL_BASE}/{camera_uuid}/flv?{urlencode(opus_params)}"
    print(f"   {opus_url}")
    print("   - Uses OPUS audio codec")
    print()

    # No audio encoding (Speex)
    print("4. Speex Audio (no audioEncoding parameter):")
    speex_params = {"x": 1280}
    speex_url = f"{DEFAULT_MEDIA_URL_BASE}/{camera_uuid}/flv?{urlencode(speex_params)}"
    print(f"   {speex_url}")
    print("   - Uses default Speex audio codec")
    print()

    # MJPEG snapshot
    print("5. Single Frame Snapshot (MJPEG):")
    snapshot_params = {"x": 1280, "fr": 1}
    snapshot_url = f"{DEFAULT_MEDIA_URL_BASE}/{camera_uuid}/mjpg?{urlencode(snapshot_params)}"
    print(f"   {snapshot_url}")
    print("   - Format: MJPEG (Motion JPEG)")
    print("   - Single frame (fr=1)")
    print("   - No audio")
    print()

    # MJPEG continuous
    print("6. MJPEG Video Stream (no audio):")
    mjpeg_params = {"x": 640}
    mjpeg_url = f"{DEFAULT_MEDIA_URL_BASE}/{camera_uuid}/mjpg?{urlencode(mjpeg_params)}"
    print(f"   {mjpeg_url}")
    print("   - Format: MJPEG continuous")
    print("   - Resolution: 640px wide")
    print("   - Video only, no audio")
    print()

    print("Usage with Python requests:")
    print("-" * 30)
    print("""
import requests

headers = {
    'Authorization': 'Bearer YOUR_ACCESS_TOKEN',
    'User-Agent': 'SimpliSafe/2105010 CFNetwork/1325.0.1 Darwin/21.1.0'
}

# For snapshot
response = requests.get(snapshot_url, headers=headers)
if response.status_code == 200:
    with open('snapshot.jpg', 'wb') as f:
        f.write(response.content)

# For streaming (save to file)
response = requests.get(video_url, headers=headers, stream=True)
if response.status_code == 200:
    with open('stream.flv', 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024):
            f.write(chunk)
""")

    print("Usage with aiohttp (async):")
    print("-" * 30)
    print("""
import aiohttp

headers = {
    'Authorization': 'Bearer YOUR_ACCESS_TOKEN'
}

# For snapshot
async with aiohttp.ClientSession() as session:
    async with session.get(snapshot_url, headers=headers) as resp:
        if resp.status == 200:
            snapshot_data = await resp.read()
            with open('snapshot.jpg', 'wb') as f:
                f.write(snapshot_data)

# For streaming
async with aiohttp.ClientSession() as session:
    async with session.get(video_url, headers=headers) as resp:
        if resp.status == 200:
            with open('stream.flv', 'wb') as f:
                async for chunk in resp.content.iter_chunked(1024):
                    f.write(chunk)
""")

    print("Notes:")
    print("-" * 30)
    print("• You need a valid SimpliSafe access token")
    print("• The camera must be online and accessible")
    print("• Streaming may require an active SimpliSafe subscription")
    print("• Privacy shutter settings may affect access")
    print("• FLV files can be played with VLC or ffmpeg")
    print("• MJPEG streams work with most browsers and players")


if __name__ == "__main__":
    demo_camera_urls()
