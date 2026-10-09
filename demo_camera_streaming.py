#!/usr/bin/env python3
"""
SimpliSafe Camera Streaming Demo

This script demonstrates how to use the enhanced camera streaming capabilities
for both indoor (SimpliSafe-hosted) and outdoor (LiveKit WebRTC) cameras.
"""

import asyncio
import logging
from aiohttp import ClientSession

import simplipy
from simplipy.errors import SimplipyError

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Your refresh token
REFRESH_TOKEN = "FVo238-EavENCZsXqJ_NZq2Tq_n7z6c3CTfg_iHl9tH4v"


async def demo_camera_streaming():
    """Demonstrate camera streaming capabilities."""

    async with ClientSession() as session:
        try:
            # Authenticate with SimpliSafe
            logger.info("🔑 Authenticating with SimpliSafe...")
            api = await simplipy.API.async_from_refresh_token(REFRESH_TOKEN, session=session)

            # Get systems
            logger.info("🏠 Getting systems...")
            systems = await api.async_get_systems()

            if not systems:
                logger.error("❌ No systems found")
                return

            system = list(systems.values())[0]
            logger.info(f"✅ Using system: {system.system_id}")

            print("\n" + "="*60)
            print("📹 SIMPLISAFE CAMERA STREAMING CAPABILITIES")
            print("="*60)

            for camera in system.cameras.values():
                print(f"\n📷 Camera: {camera.name}")
                print(f"   Type: {camera.camera_type.name}")
                print(f"   Status: {camera.status}")
                print(f"   Provider: {camera.streaming_provider}/{camera.recording_provider}")
                print(f"   Indoor Streaming: {'✅' if camera.supports_standard_streaming else '❌'}")
                print(f"   Outdoor WebRTC: {'✅' if camera.supports_webrtc_streaming else '❌'}")

                if camera.status != "online":
                    print("   ⚠️  Camera is offline")
                    continue

                # Indoor/Doorbell cameras - Standard streaming and snapshots
                if camera.supports_standard_streaming:
                    print(f"   \n   📸 SNAPSHOT CAPABILITIES:")
                    print(f"   • Snapshot URL: {camera.snapshot_url(width=640)}")
                    print(f"   • Stream URL (FLV): {camera.stream_url()}")
                    print(f"   • Stream URL (MJPEG): {camera.stream_url(format_type=simplipy.device.camera.StreamFormat.MJPEG)}")

                    try:
                        logger.info(f"   📸 Taking snapshot from {camera.name}...")
                        snapshot_data = await camera.async_get_snapshot(width=320, timeout=10)
                        print(f"   ✅ Snapshot successful: {len(snapshot_data)} bytes")

                        # Save snapshot
                        filename = f"demo_snapshot_{camera.name.replace(' ', '_')}.jpg"
                        with open(filename, "wb") as f:
                            f.write(snapshot_data)
                        print(f"   💾 Saved to: {filename}")

                    except Exception as e:
                        print(f"   ❌ Snapshot failed: {e}")

                # Outdoor cameras - WebRTC streaming
                elif camera.supports_webrtc_streaming:
                    print(f"   \n   🌐 WEBRTC STREAMING:")

                    try:
                        logger.info(f"   🔄 Getting WebRTC stream info for {camera.name}...")
                        connection_info = await camera.async_get_livekit_connection_info()

                        print(f"   ✅ WebRTC stream available!")
                        print(f"   • LiveKit URL: {connection_info['url']}")
                        print(f"   • Token expires: ~10 minutes")
                        print(f"   • Camera Status: {connection_info['camera_status']}")

                        # Save connection info for use with LiveKit clients
                        filename = f"demo_livekit_{camera.name.replace(' ', '_')}.json"
                        import json
                        with open(filename, "w") as f:
                            json.dump(connection_info, f, indent=2)
                        print(f"   💾 Connection info saved to: {filename}")

                        # Example usage instructions
                        print(f"   \n   📖 USAGE EXAMPLES:")
                        print(f"   • Python LiveKit: Use url/token with livekit-python")
                        print(f"   • JavaScript: Use url/token with livekit-client-js")
                        print(f"   • WebRTC URL: {await camera.async_get_webrtc_uri()}")

                    except Exception as e:
                        print(f"   ❌ WebRTC failed: {e}")

                else:
                    print("   ❌ No supported streaming methods")

            print("\n" + "="*60)
            print("✅ DEMO COMPLETE")
            print("="*60)
            print(f"📂 Files saved in: {__file__.replace('demo_camera_streaming.py', '')}")
            print("💡 Use the saved connection info with LiveKit clients for outdoor cameras")
            print("🔗 LiveKit docs: https://docs.livekit.io/")

        except SimplipyError as err:
            logger.error(f"❌ SimpliSafe API error: {err}")
        except Exception as err:
            logger.error(f"❌ Unexpected error: {err}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("SimpliSafe Camera Streaming Demo")
    print("================================")
    asyncio.run(demo_camera_streaming())
