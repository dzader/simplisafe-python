#!/usr/bin/env python3
"""
Test our improved camera snapshot method with timeout.
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


async def test_improved_snapshot():
    """Test the improved snapshot method with timeout."""

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

            # Test first online camera with different timeouts
            for camera in system_with_cameras.cameras.values():
                if camera.status == "online":
                    logger.info(f"Testing camera: {camera.name}")

                    try:
                        logger.info("   📸 Taking snapshot with 15s timeout...")
                        # Use the new timeout parameter (should work with our updated method)
                        snapshot_data = await camera.async_get_snapshot(width=320, timeout=15)
                        logger.info(f"   ✅ Snapshot successful: {len(snapshot_data)} bytes")

                        # Save snapshot
                        filename = f"timeout_test_{camera.name.replace(' ', '_')}.jpg"
                        with open(filename, "wb") as f:
                            f.write(snapshot_data)
                        logger.info(f"   💾 Snapshot saved to: {filename}")

                        return True

                    except Exception as e:
                        logger.error(f"   ❌ Snapshot failed: {e}")

            return False

        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    print("Testing Improved Camera Snapshot with Timeout")
    print("=" * 45)
    asyncio.run(test_improved_snapshot())
