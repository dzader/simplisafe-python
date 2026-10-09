#!/usr/bin/env python3
"""
Test script to verify camera streaming functionality with your credentials.
"""

import asyncio
import logging
import sys
from aiohttp import ClientSession
from simplipy import API
from simplipy.device.camera import StreamFormat

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Your refresh token from the get_refresh_token script
REFRESH_TOKEN = "FVo238-EavENCZsXqJ_NZq2Tq_n7z6c3CTfg_iHl9tH4v"


async def test_camera_streaming():
    """Test camera streaming functionality."""

    async with ClientSession() as session:
        try:
            # Authenticate with SimpliSafe using refresh token
            logger.info("Authenticating with SimpliSafe...")
            simplisafe = await API.async_from_refresh_token(
                REFRESH_TOKEN,
                session=session,
            )
            logger.info("✅ Authentication successful!")

            # Get systems
            logger.info("Fetching systems...")
            systems = await simplisafe.async_get_systems()

            if not systems:
                logger.error("❌ No systems found")
                return False

            logger.info(f"✅ Found {len(systems)} system(s)")

            # Find first system with cameras
            system_with_cameras = None
            for system in systems.values():
                logger.info(f"System: {system.address}")
                if system.cameras:
                    system_with_cameras = system
                    break
                else:
                    logger.info("  No cameras in this system")

            if not system_with_cameras:
                logger.info("ℹ️  No cameras found in any system")
                logger.info("This is normal if you don't have SimpliSafe cameras")
                return True

            logger.info(f"✅ Found system '{system_with_cameras.address}' with {len(system_with_cameras.cameras)} camera(s)")

            # List cameras
            for camera in system_with_cameras.cameras.values():
                logger.info(f"  📷 Camera: {camera.name}")
                logger.info(f"     Serial: {camera.serial}")
                logger.info(f"     Status: {camera.status}")
                logger.info(f"     Type: {camera.camera_type.name}")

                # Test URL generation
                video_url = camera.video_url()
                snapshot_url = camera.snapshot_url()
                logger.info(f"     Video URL: {video_url}")
                logger.info(f"     Snapshot URL: {snapshot_url}")

                # Test snapshot if camera is online
                if camera.status == "online":
                    try:
                        logger.info(f"     📸 Taking test snapshot...")
                        snapshot_data = await camera.async_get_snapshot(width=640)
                        logger.info(f"     ✅ Snapshot successful: {len(snapshot_data)} bytes")

                        # Save snapshot
                        filename = f"test_snapshot_{camera.serial}.jpg"
                        with open(filename, "wb") as f:
                            f.write(snapshot_data)
                        logger.info(f"     💾 Snapshot saved to: {filename}")

                    except Exception as e:
                        logger.warning(f"     ⚠️  Snapshot failed: {e}")
                else:
                    logger.info(f"     ⚠️  Camera offline, skipping snapshot test")

                logger.info("")

            logger.info("🎉 Camera streaming test completed successfully!")
            return True

        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """Main entry point."""
    print("SimpliSafe Camera Streaming Test")
    print("=" * 40)
    print()

    success = await test_camera_streaming()

    if success:
        print("\n✅ Test completed successfully!")
        print("\nYour camera streaming functionality is working!")
        print("\nNext steps:")
        print("1. Use save_camera_stream.py to record video streams")
        print("2. Check the CAMERA_STREAMING_EXAMPLES.md for more examples")
        print("3. Integrate camera streaming into your own projects")
    else:
        print("\n❌ Test failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
