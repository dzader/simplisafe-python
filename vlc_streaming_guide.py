#!/usr/bin/env python3
"""
Generate VLC-compatible streaming URLs for SimpliSafe cameras.
"""

import asyncio
import logging
from aiohttp import ClientSession
from simplipy import API
from simplipy.device.camera import StreamFormat

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

REFRESH_TOKEN = "FVo238-EavENCZsXqJ_NZq2Tq_n7z6c3CTfg_iHl9tH4v"


async def generate_vlc_commands():
    """Generate VLC commands for viewing SimpliSafe camera streams."""

    async with ClientSession() as session:
        try:
            # Authenticate with SimpliSafe
            logger.info("🔑 Authenticating with SimpliSafe...")
            api = await API.async_from_refresh_token(REFRESH_TOKEN, session=session)
            
            # Get systems
            systems = await api.async_get_systems()
            system = list(systems.values())[0]
            
            print("\n" + "="*60)
            print("📺 VLC STREAMING COMMANDS FOR SIMPLISAFE CAMERAS")
            print("="*60)
            
            # Process each camera
            for camera in system.cameras.values():
                if camera.status != "online":
                    continue
                    
                print(f"\n📷 {camera.name} ({camera.camera_type.name})")
                print("-" * 40)
                
                if camera.supports_standard_streaming:
                    # Generate streaming URLs with authentication
                    base_headers = f'--http-user-agent="SimpliSafe-Python" --http-password="" --http-user="" --extraintf=http --intf=dummy'
                    auth_header = f'--http-referrer="" --http-forward-cookies'
                    
                    # Get URLs
                    flv_url = camera.stream_url(format_type=StreamFormat.FLV, width=1280)
                    mjpeg_url = camera.stream_url(format_type=StreamFormat.MJPEG, width=1280)
                    snapshot_url = camera.snapshot_url(width=640)
                    
                    # Add authentication token to URLs
                    auth_token = camera._system._api.access_token
                    auth_param = f"access_token={auth_token}"
                    
                    # Add auth to URLs
                    if "?" in flv_url:
                        flv_url_auth = f"{flv_url}&{auth_param}"
                        mjpeg_url_auth = f"{mjpeg_url}&{auth_param}"
                        snapshot_url_auth = f"{snapshot_url}&{auth_param}"
                    else:
                        flv_url_auth = f"{flv_url}?{auth_param}"
                        mjpeg_url_auth = f"{mjpeg_url}?{auth_param}"
                        snapshot_url_auth = f"{snapshot_url}?{auth_param}"
                    
                    print("🎬 LIVE STREAMING:")
                    print(f"   FLV Stream (with audio):")
                    print(f'     vlc "{flv_url_auth}"')
                    print()
                    print(f"   MJPEG Stream (video only):")
                    print(f'     vlc "{mjpeg_url_auth}"')
                    print()
                    
                    print("📸 SNAPSHOT:")
                    print(f'   vlc "{snapshot_url_auth}"')
                    print()
                    
                    print("🔄 ALTERNATIVE COMMANDS:")
                    print(f"   # With custom user agent")
                    print(f'   vlc --http-user-agent="VLC/SimpliSafe" "{flv_url_auth}"')
                    print()
                    print(f"   # Loop the stream")
                    print(f'   vlc --loop "{mjpeg_url_auth}"')
                    print()
                    print(f"   # Save to file while viewing")
                    print(f'   vlc "{flv_url_auth}" --sout="#duplicate{{dst=display,dst=std{{access=file,mux=mp4,dst=camera_{camera.name.replace(" ", "_")}.mp4}}}}"')
                    
                elif camera.supports_webrtc_streaming:
                    print("🌐 WEBRTC STREAMING:")
                    print("   WebRTC streams require a WebRTC-compatible client.")
                    print("   VLC does not support WebRTC directly.")
                    print()
                    print("   ALTERNATIVES:")
                    print("   • Use a web browser with WebRTC support")
                    print("   • Use go2rtc to convert WebRTC to RTMP/HLS for VLC")
                    print("   • Use FFmpeg with WebRTC support")
                    
                    # Get WebRTC info for reference
                    try:
                        connection_info = await camera.async_get_livekit_connection_info()
                        print(f"   • LiveKit URL: {connection_info['url']}")
                        print(f"   • Token available (expires in ~10 minutes)")
                    except Exception as e:
                        print(f"   • Could not get WebRTC info: {e}")
                
                print()
                
            print("="*60)
            print("📋 QUICK START GUIDE:")
            print("="*60)
            print()
            print("1. COPY any command above")
            print("2. PASTE into terminal/command prompt")
            print("3. PRESS Enter to start streaming")
            print()
            print("💡 TIPS:")
            print("   • FLV streams include audio")
            print("   • MJPEG streams are video-only but more compatible")
            print("   • Tokens expire, re-run this script for fresh URLs")
            print("   • Use Ctrl+C to stop VLC")
            print()
            print("🔧 TROUBLESHOOTING:")
            print("   • If stream fails: Check camera is online")
            print("   • If authentication fails: Re-run script for new token")
            print("   • If VLC won't open: Try the alternative commands")
            
        except Exception as e:
            logger.error(f"❌ Failed to generate VLC commands: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("SimpliSafe Camera Streaming with VLC")
    print("=" * 37)
    asyncio.run(generate_vlc_commands())
