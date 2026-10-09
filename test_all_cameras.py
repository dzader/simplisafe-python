#!/usr/bin/env python3
"""Test snapshot functionality for all camera types."""

import asyncio
import logging
import time
from aiohttp import ClientSession

import simplipy
from simplipy.errors import SimplipyError

# Enable debug logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REFRESH_TOKEN = "FVo238-EavENCZsXqJ_NZq2Tq_n7z6c3CTfg_iHl9tH4v"


async def test_all_cameras():
    """Test snapshot functionality for all camera types."""
    async with ClientSession() as session:
        try:
            # Create API instance
            logger.info("Creating API instance...")
            api = await simplipy.API.async_from_refresh_token(REFRESH_TOKEN, session=session)

            # Get systems
            logger.info("Getting systems...")
            systems = await api.async_get_systems()

            if not systems:
                logger.error("No systems found")
                return

            system = list(systems.values())[0]
            logger.info(f"Using system: {system.system_id}")

            # Test all cameras
            for camera in system.cameras.values():
                logger.info(f"\n=== Testing camera: {camera.name} ===")
                logger.info(f"Type: {camera.camera_type}")
                logger.info(f"Status: {camera.status}")
                logger.info(f"Is outdoor: {camera.is_outdoor_camera}")
                logger.info(f"Provider: {camera.streaming_provider}/{camera.recording_provider}")
                logger.info(f"Supports standard streaming: {camera.supports_standard_streaming}")

                if camera.status != "online":
                    logger.info("Skipping offline camera")
                    continue

                if not camera.supports_standard_streaming:
                    logger.info("Skipping camera - doesn't support standard streaming")
                    try:
                        # Still test wake-up for outdoor cameras
                        if camera.is_outdoor_camera:
                            logger.info("Testing wake-up for outdoor camera...")
                            wake_success = await camera.async_wake_up()
                            logger.info(f"Wake-up result: {wake_success}")
                    except Exception as err:
                        logger.error(f"Wake-up failed: {err}")
                    continue

                # Test snapshot
                try:
                    logger.info("Testing async_get_snapshot...")
                    start_time = time.time()
                    snapshot_data = await camera.async_get_snapshot(width=640, timeout=30)
                    end_time = time.time()

                    logger.info(f"SUCCESS: Got snapshot in {end_time - start_time:.2f} seconds")
                    logger.info(f"Snapshot size: {len(snapshot_data)} bytes")

                    # Verify it's valid JPEG data
                    if snapshot_data.startswith(b'\xff\xd8'):
                        logger.info("✓ Valid JPEG header detected")
                    else:
                        logger.warning("⚠ Data doesn't start with JPEG header")

                    # Save snapshot
                    filename = f"test_snapshot_{camera.name.replace(' ', '_')}.jpg"
                    with open(filename, "wb") as f:
                        f.write(snapshot_data)
                    logger.info(f"Snapshot saved to: {filename}")

                except Exception as err:
                    logger.error(f"Snapshot failed: {type(err).__name__}: {err}")

        except SimplipyError as err:
            logger.error(f"SimpliSafe API error: {err}")
        except Exception as err:
            logger.error(f"Unexpected error: {err}")


if __name__ == "__main__":
    asyncio.run(test_all_cameras())
