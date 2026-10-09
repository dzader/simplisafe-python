#!/usr/bin/env python3
"""
Test script to debug camera snapshot URL responses.
"""

import asyncio
import logging
from aiohttp import ClientSession
from simplipy import API

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Your refresh token from the get_refresh_token script
REFRESH_TOKEN = "FVo238-EavENCZsXqJ_NZq2Tq_n7z6c3CTfg_iHl9tH4v"


async def debug_camera_urls():
    """Debug camera snapshot URLs."""

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

            # Test first online camera
            for camera in system_with_cameras.cameras.values():
                if camera.status == "online":
                    logger.info(f"Testing camera: {camera.name}")

                    # Get snapshot URL
                    snapshot_url = camera.snapshot_url(width=320)
                    logger.info(f"Snapshot URL: {snapshot_url}")

                    # Try to make a direct HTTP request to debug
                    headers = {
                        "Authorization": f"Bearer {simplisafe.access_token}",
                        "User-Agent": "simplipy",
                    }

                    logger.info("Making direct HTTP request...")
                    try:
                        async with session.get(snapshot_url, headers=headers, timeout=5) as resp:
                            logger.info(f"HTTP Status: {resp.status}")
                            logger.info(f"Response Headers: {dict(resp.headers)}")

                            if resp.status == 200:
                                content_length = resp.headers.get('content-length', 'unknown')
                                logger.info(f"Content-Length: {content_length}")

                                # Read a small chunk to verify it's image data
                                chunk = await resp.content.read(100)
                                logger.info(f"First 100 bytes: {chunk[:20]}...")

                                if chunk.startswith(b'\xff\xd8'):
                                    logger.info("✅ Looks like JPEG data!")
                                else:
                                    logger.warning("⚠️  Doesn't look like JPEG data")
                            else:
                                text = await resp.text()
                                logger.error(f"Error response: {text}")

                    except asyncio.TimeoutError:
                        logger.error("❌ Direct HTTP request timed out")
                    except Exception as e:
                        logger.error(f"❌ Direct HTTP request failed: {e}")

                    # Only test one camera
                    break

        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("Camera URL Debug Test")
    print("=" * 25)
    asyncio.run(debug_camera_urls())
