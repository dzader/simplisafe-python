#!/usr/bin/env python3
"""
Test actual media access for SimpliSafe cameras.
This test will try to actually fetch snapshots and streaming data.
"""

import asyncio
import logging
import aiohttp
from simplipy import API
from simplipy.device.camera import StreamFormat

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Your refresh token
REFRESH_TOKEN = "FVo238-EavENCZsXqJ_NZq2Tq_n7z6c3CTfg_iHl9tH4v"


async def test_actual_media_access():
    """Test actual media access for cameras."""

    async with aiohttp.ClientSession() as session:
        try:
            print("🔐 Authenticating with SimpliSafe...")
            simplisafe = await API.async_from_refresh_token(REFRESH_TOKEN, session=session)
            print("✅ Authentication successful!")

            print("\n📡 Fetching systems...")
            systems = await simplisafe.async_get_systems()

            system_with_cameras = None
            for system in systems.values():
                if system.cameras:
                    system_with_cameras = system
                    break

            if not system_with_cameras:
                print("❌ No cameras found")
                return

            print(f"✅ Found system with {len(system_with_cameras.cameras)} camera(s)")

            # Test with first online camera
            test_camera = None
            for camera in system_with_cameras.cameras.values():
                if camera.status == "online":
                    test_camera = camera
                    break

            if not test_camera:
                print("❌ No online cameras found")
                return

            print(f"\n📷 Testing camera: {test_camera.name}")
            print(f"  Status: {test_camera.status}")
            print(f"  Type: {test_camera.camera_type.name}")
            print(f"  Is Outdoor: {test_camera.is_outdoor_camera}")

            # Test direct HTTP access to the media URL
            snapshot_url = test_camera.snapshot_url(width=320)
            print(f"\n🔗 Snapshot URL: {snapshot_url}")

            print("\n🔍 Testing direct HTTP access to media URL...")

            try:
                timeout = aiohttp.ClientTimeout(total=10)
                headers = {
                    "Authorization": f"Bearer {simplisafe.access_token}",
                    "User-Agent": "simplipy",
                    "Accept": "*/*",
                }

                print(f"  Request headers: {headers}")
                print(f"  URL: {snapshot_url}")

                async with session.get(snapshot_url, headers=headers, timeout=timeout) as resp:
                    print(f"  Response status: {resp.status}")
                    print(f"  Response headers: {dict(resp.headers)}")

                    if resp.status == 200:
                        content_length = resp.headers.get('content-length', 'unknown')
                        content_type = resp.headers.get('content-type', 'unknown')
                        print(f"  Content-Type: {content_type}")
                        print(f"  Content-Length: {content_length}")

                        # Read first 100 bytes to see if it's valid image data
                        partial_data = await resp.content.read(100)
                        print(f"  First 20 bytes: {partial_data[:20]}")

                        # Check if it looks like JPEG data
                        if partial_data.startswith(b'\xff\xd8\xff'):
                            print("  ✅ Response appears to be valid JPEG data!")
                        else:
                            print("  ⚠️  Response doesn't appear to be JPEG data")
                            print(f"  Raw data: {partial_data}")
                    else:
                        error_text = await resp.text()
                        print(f"  ❌ HTTP {resp.status}: {error_text}")

            except asyncio.TimeoutError:
                print("  ❌ Request timed out")
            except Exception as e:
                print(f"  ❌ Error: {e}")

            # Test with the camera's built-in snapshot method
            print("\n📸 Testing camera snapshot method...")
            try:
                snapshot_data = await test_camera.async_get_snapshot_direct(width=320, timeout=10)
                print(f"  ✅ Snapshot retrieved! Size: {len(snapshot_data)} bytes")

                # Save to file for verification
                with open("test_snapshot.jpg", "wb") as f:
                    f.write(snapshot_data)
                print("  💾 Saved snapshot as 'test_snapshot.jpg'")

            except Exception as e:
                print(f"  ❌ Snapshot method failed: {e}")

            # Test streaming (just first few chunks)
            print("\n🎥 Testing streaming...")
            try:
                chunk_count = 0
                total_bytes = 0

                print("  Starting FLV stream...")
                async for chunk in test_camera.async_stream_data(
                    format_type=StreamFormat.FLV,
                    width=320,
                    chunk_size=1024
                ):
                    chunk_count += 1
                    total_bytes += len(chunk)
                    print(f"  Chunk {chunk_count}: {len(chunk)} bytes")

                    # Only test first few chunks
                    if chunk_count >= 5:
                        print(f"  ✅ Streaming works! Received {chunk_count} chunks, {total_bytes} total bytes")
                        break

            except Exception as e:
                print(f"  ❌ Streaming failed: {e}")

        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("SimpliSafe Camera Media Access Test")
    print("=" * 40)
    asyncio.run(test_actual_media_access())
