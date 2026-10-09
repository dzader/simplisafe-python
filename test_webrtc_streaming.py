#!/usr/bin/env python3
"""Test WebRTC streaming for outdoor SimpliSafe cameras."""

import asyncio
import logging
from aiohttp import ClientSession

import simplipy
from simplipy.errors import SimplipyError

# Enable debug logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REFRESH_TOKEN = "FVo238-EavENCZsXqJ_NZq2Tq_n7z6c3CTfg_iHl9tH4v"


async def test_webrtc_streaming():
    """Test WebRTC streaming functionality for outdoor cameras."""
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
                logger.info(f"Supports WebRTC streaming: {camera.supports_webrtc_streaming}")

                if camera.status != "online":
                    logger.info("Skipping offline camera")
                    continue

                # Test WebRTC for outdoor cameras
                if camera.supports_webrtc_streaming:
                    try:
                        logger.info("Testing WebRTC stream info retrieval...")
                        stream_info = await camera.async_get_webrtc_stream_info()

                        logger.info(f"SUCCESS: Got WebRTC stream info")
                        logger.info(f"LiveKit URL: {stream_info.liveKitURL}")
                        logger.info(f"Camera Status: {stream_info.cameraStatus}")
                        logger.info(f"Token length: {len(stream_info.userToken)} chars")

                        # Generate WebRTC URI
                        webrtc_uri = camera.get_webrtc_uri(stream_info)
                        logger.info(f"WebRTC URI: {webrtc_uri[:100]}...")

                        # Get connection info
                        connection_info = camera.get_livekit_connection_info(stream_info)
                        logger.info(f"Connection info: {connection_info}")

                        # Test convenience methods
                        convenience_uri = await camera.async_get_webrtc_uri()
                        convenience_info = await camera.async_get_livekit_connection_info()

                        logger.info(f"Convenience URI matches: {webrtc_uri == convenience_uri}")
                        logger.info(f"Convenience info matches: {connection_info == convenience_info}")

                        # Save connection info to file for testing with LiveKit clients
                        filename = f"livekit_info_{camera.name.replace(' ', '_')}.json"
                        import json
                        with open(filename, "w") as f:
                            json.dump(connection_info, f, indent=2)
                        logger.info(f"LiveKit connection info saved to: {filename}")

                        # Also save the WebRTC URI
                        uri_filename = f"webrtc_uri_{camera.name.replace(' ', '_')}.txt"
                        with open(uri_filename, "w") as f:
                            f.write(webrtc_uri)
                        logger.info(f"WebRTC URI saved to: {uri_filename}")

                    except Exception as err:
                        logger.error(f"WebRTC streaming failed: {type(err).__name__}: {err}")

                # Test standard streaming for indoor cameras
                elif camera.supports_standard_streaming:
                    try:
                        logger.info("Testing standard snapshot...")
                        snapshot_data = await camera.async_get_snapshot(width=320, timeout=15)
                        logger.info(f"SUCCESS: Got snapshot: {len(snapshot_data)} bytes")

                    except Exception as err:
                        logger.error(f"Standard snapshot failed: {type(err).__name__}: {err}")

                else:
                    logger.info("Camera doesn't support any streaming methods")

        except SimplipyError as err:
            logger.error(f"SimpliSafe API error: {err}")
        except Exception as err:
            logger.error(f"Unexpected error: {err}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_webrtc_streaming())
