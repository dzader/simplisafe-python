#!/usr/bin/env python3
"""
Quick test to check camera types and basic info.
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


async def check_cameras():
    """Check camera information."""

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

            if not system_with_cameras:
                logger.info("ℹ️  No cameras found in any system")
                return True

            logger.info(f"✅ Found system '{system_with_cameras.address}' with {len(system_with_cameras.cameras)} camera(s)")

            # List cameras with detailed info
            for camera in system_with_cameras.cameras.values():
                logger.info(f"  📷 Camera: {camera.name}")
                logger.info(f"     Serial: {camera.serial}")
                logger.info(f"     Status: {camera.status}")
                logger.info(f"     Model: {getattr(camera, 'model', 'Unknown')}")
                logger.info(f"     Type: {camera.camera_type.name}")
                logger.info(f"     Is Outdoor: {camera.is_outdoor_camera}")

                # Test URL generation
                video_url = camera.video_url()
                snapshot_url = camera.snapshot_url()
                logger.info(f"     Video URL: {video_url}")
                logger.info(f"     Snapshot URL: {snapshot_url}")

                logger.info("")

            logger.info("🎉 Camera info check completed successfully!")
            return True

        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    asyncio.run(check_cameras())
