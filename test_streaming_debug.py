#!/usr/bin/env python3
"""
Debug streaming and snapshot issues for SimpliSafe cameras.
This script helps diagnose problems with camera snapshot retrieval.
"""

import asyncio
import logging
import os
from aiohttp import ClientSession

import simplipy
from simplipy.errors import SimplipyError

# Enable debug logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

REFRESH_TOKEN = "FVo238-EavENCZsXqJ_NZq2Tq_n7z6c3CTfg_iHl9tH4v"


async def debug_camera_response(camera):
    """Debug camera response to understand what we're getting."""
    if not camera.supports_standard_streaming:
        logger.info(f"Camera {camera.name} doesn't support standard streaming, skipping debug")
        return

    logger.info(f"=== Debugging camera: {camera.name} ===")
    
    # Get the snapshot URL
    snapshot_url = camera.snapshot_url(width=320)
    logger.info(f"Snapshot URL: {snapshot_url}")
    
    try:
        # Make a direct request to see what we get
        async with camera._system._api.session.get(
            snapshot_url,
            headers={
                "Authorization": f"Bearer {camera._system._api.access_token}",
                "User-Agent": "simplipy",
            },
            timeout=30
        ) as resp:
            logger.info(f"Response status: {resp.status}")
            logger.info(f"Response headers: {dict(resp.headers)}")
            
            # Read first 100 bytes to check the start
            first_chunk = await resp.content.read(100)
            logger.info(f"First 100 bytes: {first_chunk}")
            logger.info(f"First 4 bytes hex: {first_chunk[:4].hex()}")
            
            # Check if it starts with JPEG marker
            JPEG_START = b'\xff\xd8'
            if first_chunk.startswith(JPEG_START):
                logger.info("✅ Response starts with JPEG marker")
            else:
                logger.warning("❌ Response does NOT start with JPEG marker")
                # Check if it might be HTML error or something else
                try:
                    text_preview = first_chunk.decode('utf-8', errors='ignore')
                    logger.info(f"Text preview: {text_preview}")
                except:
                    logger.info("Could not decode as text")
                    
    except Exception as err:
        logger.error(f"Error during debug request: {err}")


async def test_streaming_with_debug():
    """Test streaming functionality with detailed debugging."""
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
                if camera.status != "online":
                    logger.info(f"Skipping offline camera: {camera.name}")
                    continue
                    
                logger.info(f"\n{'='*60}")
                logger.info(f"Camera: {camera.name}")
                logger.info(f"Type: {camera.camera_type}")
                logger.info(f"Status: {camera.status}")
                logger.info(f"Provider: {camera.streaming_provider}/{camera.recording_provider}")
                logger.info(f"Supports standard streaming: {camera.supports_standard_streaming}")
                logger.info(f"Supports WebRTC streaming: {camera.supports_webrtc_streaming}")

                # Debug response first
                await debug_camera_response(camera)
                
                # Test standard streaming for supported cameras
                if camera.supports_standard_streaming:
                    logger.info("Testing actual snapshot method...")
                    try:
                        snapshot_data = await camera.async_get_snapshot(width=320, timeout=15)
                        logger.info(f"✅ Snapshot successful: {len(snapshot_data)} bytes")
                        
                        # Save snapshot for verification
                        filename = f"debug_snapshot_{camera.name.replace(' ', '_')}.jpg"
                        with open(filename, "wb") as f:
                            f.write(snapshot_data)
                        logger.info(f"💾 Snapshot saved to: {filename}")
                        
                    except Exception as err:
                        logger.error(f"❌ Snapshot failed: {err}")

                # Test WebRTC for outdoor cameras
                elif camera.supports_webrtc_streaming:
                    logger.info("Testing WebRTC stream info...")
                    try:
                        stream_info = await camera.async_get_webrtc_stream_info()
                        logger.info(f"✅ WebRTC info: {stream_info.liveKitURL}")
                        
                        # Generate WebRTC URI
                        webrtc_uri = camera.get_webrtc_uri(stream_info)
                        logger.info(f"WebRTC URI length: {len(webrtc_uri)} chars")
                        
                        # Save connection info
                        connection_info = camera.get_livekit_connection_info(stream_info)
                        filename = f"debug_livekit_{camera.name.replace(' ', '_')}.json"
                        import json
                        with open(filename, "w") as f:
                            json.dump(connection_info, f, indent=2)
                        logger.info(f"💾 LiveKit info saved to: {filename}")
                        
                    except Exception as err:
                        logger.error(f"❌ WebRTC failed: {err}")

        except SimplipyError as err:
            logger.error(f"SimpliSafe API error: {err}")
        except Exception as err:
            logger.error(f"Unexpected error: {err}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_streaming_with_debug())
