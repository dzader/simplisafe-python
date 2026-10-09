#!/usr/bin/env python3
"""
Test the outdoor camera wake-up functionality.
"""

import asyncio
import logging
from aiohttp import ClientSession
from simplipy import API

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Your refresh token from the get_refresh_token script
REFRESH_TOKEN = "FVo238-EavENCZsXqJ_NZq2Tq_n7z6c3CTfg_iHl9tH4v"


async def test_outdoor_camera_wakeup():
    """Test the outdoor camera wake-up functionality."""

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
            systems = await simplisafe.async_get_systems()
            system_with_cameras = None
            for system in systems.values():
                if system.cameras:
                    system_with_cameras = system
                    break

            if not system_with_cameras:
                logger.info("No cameras found")
                return

            # Find outdoor cameras
            outdoor_cameras = [
                camera for camera in system_with_cameras.cameras.values()
                if camera.is_outdoor_camera
            ]

            if not outdoor_cameras:
                logger.info("No outdoor cameras found")
                return

            logger.info(f"Found {len(outdoor_cameras)} outdoor camera(s)")

            # Test wake-up on each outdoor camera
            for camera in outdoor_cameras:
                logger.info(f"\n🔋 Testing outdoor camera: {camera.name}")
                logger.info(f"   Status: {camera.status}")
                logger.info(f"   Type: {camera.camera_type.name}")
                logger.info(f"   Is Outdoor: {camera.is_outdoor_camera}")

                try:
                    logger.info("   🔌 Attempting to wake up camera...")
                    start_time = asyncio.get_event_loop().time()

                    wake_success = await camera.async_wake_up()

                    end_time = asyncio.get_event_loop().time()
                    duration = end_time - start_time

                    if wake_success:
                        logger.info(f"   ✅ Camera wake-up successful! (took {duration:.1f}s)")

                        # Try to take a snapshot now that it might be awake
                        logger.info("   📸 Attempting snapshot from woken camera...")
                        try:
                            snapshot_data = await camera.async_get_snapshot_direct(width=320, timeout=15)
                            logger.info(f"   ✅ Snapshot after wake-up successful: {len(snapshot_data)} bytes")

                            # Save snapshot
                            filename = f"outdoor_wakeup_{camera.name.replace(' ', '_')}.jpg"
                            with open(filename, "wb") as f:
                                f.write(snapshot_data)
                            logger.info(f"   💾 Snapshot saved to: {filename}")

                        except Exception as e:
                            logger.warning(f"   ⚠️  Snapshot after wake-up failed: {e}")
                    else:
                        logger.warning(f"   ⚠️  Camera wake-up failed (took {duration:.1f}s)")

                except Exception as e:
                    logger.error(f"   ❌ Error during wake-up test: {e}")

            logger.info("\n🎉 Outdoor camera wake-up test completed!")

        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("SimpliSafe Outdoor Camera Wake-up Test")
    print("=" * 38)
    asyncio.run(test_outdoor_camera_wakeup())
