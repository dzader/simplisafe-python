#!/usr/bin/env python3
"""
Test script to verify camera wake-up and streaming functionality.
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


async def test_camera_functionality():
    """Test camera functionality including wake-up for outdoor cameras."""

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
                if system.cameras:
                    system_with_cameras = system
                    break

            if not system_with_cameras:
                logger.info("ℹ️  No cameras found in any system")
                return True

            logger.info(f"✅ Found system '{system_with_cameras.address}' with {len(system_with_cameras.cameras)} camera(s)")

            # Test different camera types
            indoor_cameras = []
            outdoor_cameras = []

            for camera in system_with_cameras.cameras.values():
                if camera.is_outdoor_camera:
                    outdoor_cameras.append(camera)
                else:
                    indoor_cameras.append(camera)

            # Test indoor cameras first (should work without wake-up)
            logger.info(f"\n=== Testing {len(indoor_cameras)} Indoor Camera(s) ===")
            for camera in indoor_cameras:
                logger.info(f"📷 Testing camera: {camera.name} ({camera.camera_type.name})")
                logger.info(f"   Status: {camera.status}")

                if camera.status == "online":
                    try:
                        logger.info("   📸 Taking snapshot...")
                        snapshot_data = await camera.async_get_snapshot(width=320)
                        logger.info(f"   ✅ Snapshot successful: {len(snapshot_data)} bytes")

                        # Save snapshot
                        filename = f"indoor_snapshot_{camera.name.replace(' ', '_')}.jpg"
                        with open(filename, "wb") as f:
                            f.write(snapshot_data)
                        logger.info(f"   💾 Snapshot saved to: {filename}")

                    except Exception as e:
                        logger.warning(f"   ⚠️  Snapshot failed: {e}")
                else:
                    logger.info("   ⚠️  Camera offline, skipping snapshot test")

            # Test outdoor cameras (should use wake-up logic)
            logger.info(f"\n=== Testing {len(outdoor_cameras)} Outdoor Camera(s) ===")
            for camera in outdoor_cameras:
                logger.info(f"📷 Testing outdoor camera: {camera.name}")
                logger.info(f"   Status: {camera.status}")
                logger.info(f"   Is Outdoor: {camera.is_outdoor_camera}")

                try:
                    logger.info("   🔌 Attempting to wake up camera...")
                    wake_success = await camera.async_wake_up()

                    if wake_success:
                        logger.info("   ✅ Camera wake-up successful!")

                        # Try to take a snapshot now that it's awake
                        logger.info("   📸 Taking snapshot from woken camera...")
                        snapshot_data = await camera.async_get_snapshot(width=320)
                        logger.info(f"   ✅ Snapshot successful: {len(snapshot_data)} bytes")

                        # Save snapshot
                        filename = f"outdoor_snapshot_{camera.name.replace(' ', '_')}.jpg"
                        with open(filename, "wb") as f:
                            f.write(snapshot_data)
                        logger.info(f"   💾 Snapshot saved to: {filename}")

                    else:
                        logger.warning("   ⚠️  Camera wake-up failed")

                        # Still try to take a snapshot - might work anyway
                        logger.info("   📸 Trying snapshot anyway...")
                        try:
                            snapshot_data = await camera.async_get_snapshot(width=320)
                            logger.info(f"   ✅ Snapshot successful despite wake-up failure: {len(snapshot_data)} bytes")

                            filename = f"outdoor_snapshot_{camera.name.replace(' ', '_')}_no_wakeup.jpg"
                            with open(filename, "wb") as f:
                                f.write(snapshot_data)
                            logger.info(f"   💾 Snapshot saved to: {filename}")
                        except Exception as e:
                            logger.warning(f"   ❌ Snapshot also failed: {e}")

                except Exception as e:
                    logger.error(f"   ❌ Error testing outdoor camera: {e}")

            logger.info("\n🎉 Camera functionality test completed!")
            return True

        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """Main entry point."""
    print("SimpliSafe Camera Wake-up and Streaming Test")
    print("=" * 50)
    print()

    success = await test_camera_functionality()

    if success:
        print("\n✅ Test completed!")
        print("\nResults:")
        print("- Indoor cameras should work immediately")
        print("- Outdoor cameras require wake-up before use")
        print("- Check the saved snapshot files to verify functionality")
    else:
        print("\n❌ Test failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
