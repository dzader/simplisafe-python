#!/usr/bin/env python3
"""Simple test to verify the async_get_snapshot timeout fix."""

import asyncio
import logging
import time
from aiohttp import ClientSession

import simplipy
from simplipy.errors import SimplipyError

# Enable debug logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Note: This refresh token was valid during previous tests
REFRESH_TOKEN = "RPAXjVAL4GVUc5PY-JP0WrgT23nyxwTfvgOIDp8SDSahJ"


async def test_snapshot_timeout_fix():
    """Test that async_get_snapshot works without timeout issues."""
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

            # Test with indoor/doorbell cameras that support standard streaming
            cameras = [c for c in system.cameras.values() if c.supports_standard_streaming]

            if not cameras:
                logger.error("No cameras with standard streaming support found")
                return

            for camera in cameras:
                logger.info(f"\n=== Testing camera: {camera.name} ===")
                logger.info(f"Type: {camera.camera_type}")
                logger.info(f"Provider: {camera.streaming_provider}/{camera.recording_provider}")
                logger.info(f"Supports standard streaming: {camera.supports_standard_streaming}")
                logger.info(f"Camera status: {camera.status}")
                logger.info(f"Is outdoor camera: {camera.is_outdoor_camera}")

                if not camera.supports_standard_streaming:
                    logger.info("Skipping camera - doesn't support standard streaming")
                    continue

                # Test both methods with timing (longer timeout)
                try:
                    logger.info("Testing async_get_snapshot (fixed version) with 30s timeout...")
                    start_time = time.time()
                    snapshot_data = await camera.async_get_snapshot(timeout=30)
                    end_time = time.time()

                    logger.info(f"SUCCESS: Got snapshot in {end_time - start_time:.2f} seconds")
                    logger.info(f"Snapshot size: {len(snapshot_data)} bytes")

                    # Verify it's valid JPEG data
                    if snapshot_data.startswith(b'\xff\xd8'):
                        logger.info("✓ Valid JPEG header detected")
                    else:
                        logger.warning("⚠ Data doesn't start with JPEG header")

                except Exception as err:
                    logger.error(f"async_get_snapshot failed: {type(err).__name__}: {err}")

                # Test direct snapshot for comparison (longer timeout)
                try:
                    logger.info("Testing async_get_snapshot_direct with 30s timeout...")
                    start_time = time.time()
                    direct_data = await camera.async_get_snapshot_direct(timeout=30)
                    end_time = time.time()

                    logger.info(f"SUCCESS: Got direct snapshot in {end_time - start_time:.2f} seconds")
                    logger.info(f"Direct snapshot size: {len(direct_data)} bytes")

                    # Verify it's valid JPEG data
                    if direct_data.startswith(b'\xff\xd8'):
                        logger.info("✓ Valid JPEG header detected")
                    else:
                        logger.warning("⚠ Data doesn't start with JPEG header")

                except Exception as err:
                    logger.error(f"async_get_snapshot_direct failed: {type(err).__name__}: {err}")

                # Test that we can get the URL at least
                try:
                    url = camera.snapshot_url()
                    logger.info(f"Snapshot URL: {url}")
                except Exception as err:
                    logger.error(f"snapshot_url failed: {err}")

                break  # Test only first camera

        except SimplipyError as err:
            logger.error(f"SimpliSafe API error: {err}")
        except Exception as err:
            logger.error(f"Unexpected error: {err}")


if __name__ == "__main__":
    asyncio.run(test_snapshot_timeout_fix())
