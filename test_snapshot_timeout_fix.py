#!/usr/bin/env python3
"""Test script to verify the timeout fix for async_get_snapshot."""

import asyncio
import logging
import time
from aiohttp import ClientSession

import simplipy
from simplipy.errors import SimplipyError

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

AUTH_CODE = "RDTOM6Zn-NwwIYAf5sO9R45KtmeRCKLCGJdMNmAJO9b0g"
CODE_VERIFIER = "8UBZPoMqzcKAeCLgFymZ2X6CJ9LToUZyZp3Zn725WVKmup9EFqw"


async def test_snapshot_timeout_fix():
    """Test that async_get_snapshot works without timeout issues."""
    async with ClientSession() as session:
        try:
            # Create API instance
            logger.info("Creating API instance...")
            api = await simplipy.API.async_from_auth(AUTH_CODE, CODE_VERIFIER, session=session)

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

                if not camera.supports_standard_streaming:
                    logger.info("Skipping camera - doesn't support standard streaming")
                    continue

                # Test both methods with timing
                try:
                    logger.info("Testing async_get_snapshot (fixed version)...")
                    start_time = time.time()
                    snapshot_data = await camera.async_get_snapshot(timeout=15)
                    end_time = time.time()

                    logger.info(f"SUCCESS: Got snapshot in {end_time - start_time:.2f} seconds")
                    logger.info(f"Snapshot size: {len(snapshot_data)} bytes")

                    # Verify it's valid JPEG data
                    if snapshot_data.startswith(b'\xff\xd8'):
                        logger.info("✓ Valid JPEG header detected")
                    else:
                        logger.warning("⚠ Data doesn't start with JPEG header")

                except Exception as err:
                    logger.error(f"async_get_snapshot failed: {err}")

                # Compare with direct method
                try:
                    logger.info("Testing async_get_snapshot_direct for comparison...")
                    start_time = time.time()
                    direct_data = await camera.async_get_snapshot_direct(timeout=15)
                    end_time = time.time()

                    logger.info(f"SUCCESS: Got direct snapshot in {end_time - start_time:.2f} seconds")
                    logger.info(f"Direct snapshot size: {len(direct_data)} bytes")

                    # Compare sizes
                    if len(snapshot_data) == len(direct_data):
                        logger.info("✓ Both methods returned same size data")
                    else:
                        logger.warning(f"⚠ Size mismatch: {len(snapshot_data)} vs {len(direct_data)}")

                except Exception as err:
                    logger.error(f"async_get_snapshot_direct failed: {err}")

                # Test short timeout to verify timeout handling works
                try:
                    logger.info("Testing with very short timeout (1 second)...")
                    start_time = time.time()
                    await camera.async_get_snapshot(timeout=1)
                    end_time = time.time()
                    logger.warning(f"Unexpected success with 1 second timeout in {end_time - start_time:.2f} seconds")
                except asyncio.TimeoutError:
                    end_time = time.time()
                    logger.info(f"✓ Correctly timed out after {end_time - start_time:.2f} seconds")
                except Exception as err:
                    end_time = time.time()
                    logger.info(f"✓ Got expected error after {end_time - start_time:.2f} seconds: {err}")

                break  # Test only first camera

        except SimplipyError as err:
            logger.error(f"SimpliSafe API error: {err}")
        except Exception as err:
            logger.error(f"Unexpected error: {err}")


if __name__ == "__main__":
    asyncio.run(test_snapshot_timeout_fix())
