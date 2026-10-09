#!/usr/bin/env python3
"""
Simple test script with timeout to check camera responsiveness.
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


async def quick_camera_test():
    """Quick test with short timeout."""

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

            # Find first system with cameras
            system_with_cameras = None
            for system in systems.values():
                if system.cameras:
                    system_with_cameras = system
                    break

            if not system_with_cameras:
                logger.info("ℹ️  No cameras found in any system")
                return True

            logger.info(f"✅ Found system with {len(system_with_cameras.cameras)} camera(s)")

            # Test only the first online camera with a short timeout
            for camera in system_with_cameras.cameras.values():
                logger.info(f"📷 Testing camera: {camera.name} ({camera.camera_type.name})")
                logger.info(f"   Status: {camera.status}")

                if camera.status == "online":
                    try:
                        logger.info("   📸 Taking quick snapshot (10s timeout)...")
                        # Use the new timeout parameter
                        snapshot_data = await camera.async_get_snapshot(width=320, timeout=10)
                        logger.info(f"   ✅ Snapshot successful: {len(snapshot_data)} bytes")

                        # Save snapshot
                        filename = f"quick_test_{camera.name.replace(' ', '_')}.jpg"
                        with open(filename, "wb") as f:
                            f.write(snapshot_data)
                        logger.info(f"   💾 Snapshot saved to: {filename}")

                        # Only test one camera for now
                        return True

                    except Exception as e:
                        logger.warning(f"   ⚠️  Snapshot failed: {e}")
                        # Try the next camera
                        continue
                else:
                    logger.info("   ⚠️  Camera offline, skipping")

            logger.info("No online cameras responded successfully")
            return False

        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    print("Quick Camera Test (10s timeout)")
    print("=" * 35)
    asyncio.run(quick_camera_test())
