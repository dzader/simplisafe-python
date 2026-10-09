#!/usr/bin/env python3
"""
SimpliSafe WebRTC Server Example
================================

This script demonstrates how to use the WebRTC signaling server for SimpliSafe outdoor cameras.
It sets up a complete streaming solution with web interface.

Usage:
    python webrtc_server_example.py --refresh-token YOUR_TOKEN

Features:
- Automatic go2rtc installation
- Dynamic stream configuration
- Web interface for viewing streams
- Home Assistant integration examples
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add current directory to path to import our modules
sys.path.insert(0, str(Path(__file__).parent))

from webrtc_signaling_server import SimpliSafeWebRTCServer

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

REFRESH_TOKEN = "FVo238-EavENCZsXqJ_NZq2Tq_n7z6c3CTfg_iHl9tH4v"


async def demo_webrtc_server():
    """Demonstrate the WebRTC signaling server."""
    logger.info("🚀 SimpliSafe WebRTC Server Demo")
    logger.info("=" * 50)
    
    # Create server instance
    server = SimpliSafeWebRTCServer(
        refresh_token=REFRESH_TOKEN,
        port=1984,           # go2rtc API port
        webrtc_port=8555     # WebRTC streaming port
    )
    
    logger.info("📋 This demo will:")
    logger.info("   1. Install go2rtc automatically")
    logger.info("   2. Discover your SimpliSafe cameras")
    logger.info("   3. Generate configuration for WebRTC streaming")
    logger.info("   4. Start streaming server with web interface")
    logger.info("   5. Provide URLs for viewing streams")
    
    # Test camera discovery first
    logger.info("\n🔍 Discovering cameras...")
    cameras = await server.discover_cameras()
    
    if not cameras:
        logger.error("❌ No cameras found. Check your refresh token.")
        return
    
    logger.info(f"✅ Found {len(cameras)} cameras:")
    for camera in cameras:
        status_icon = "🟢" if camera['status'] == 'online' else "🔴"
        stream_type = "WebRTC" if camera['supports_webrtc'] else "HTTP"
        logger.info(f"   {status_icon} {camera['name']}: {camera['type']} ({stream_type})")
    
    # Check for WebRTC cameras
    webrtc_cameras = [c for c in cameras if c['supports_webrtc']]
    online_webrtc = [c for c in webrtc_cameras if c['status'] == 'online']
    
    if not webrtc_cameras:
        logger.warning("⚠️ No WebRTC cameras found. This demo is for outdoor cameras.")
        logger.info("💡 You can still run the server to see the setup process.")
    elif not online_webrtc:
        logger.warning("⚠️ No online WebRTC cameras. Make sure outdoor cameras are powered on.")
    else:
        logger.info(f"✅ Found {len(online_webrtc)} online WebRTC cameras")
    
    # Run the server
    logger.info("\n🚀 Starting WebRTC signaling server...")
    logger.info("   This will take a moment to set up...")
    
    try:
        await server.run_server()
    except KeyboardInterrupt:
        logger.info("\n🛑 Server stopped by user")
    except Exception as err:
        logger.error(f"❌ Server error: {err}")


async def test_webrtc_integration():
    """Test WebRTC integration without starting full server."""
    logger.info("🧪 Testing WebRTC Integration")
    logger.info("=" * 40)
    
    server = SimpliSafeWebRTCServer(REFRESH_TOKEN)
    
    # Test camera discovery
    cameras = await server.discover_cameras()
    
    webrtc_cameras = [c for c in cameras if c['supports_webrtc'] and c['status'] == 'online']
    
    if not webrtc_cameras:
        logger.info("ℹ️ No online WebRTC cameras for testing")
        return
    
    # Test getting WebRTC URL for first camera
    camera = webrtc_cameras[0]
    logger.info(f"🎥 Testing WebRTC URL generation for: {camera['name']}")
    
    try:
        webrtc_url = await server.get_webrtc_stream_url(camera['name'])
        if webrtc_url:
            logger.info(f"✅ WebRTC URL generated successfully")
            logger.info(f"   📍 Camera: {camera['name']}")
            logger.info(f"   🔗 URL length: {len(webrtc_url)} characters")
            logger.info(f"   🏷️ URL prefix: {webrtc_url[:50]}...")
        else:
            logger.error("❌ Failed to generate WebRTC URL")
    except Exception as err:
        logger.error(f"❌ Error testing WebRTC: {err}")


def show_usage_examples():
    """Show usage examples for different scenarios."""
    print("\n" + "=" * 60)
    print("  SimpliSafe WebRTC Server - Usage Examples")
    print("=" * 60)
    
    print("\n📱 Basic Usage:")
    print("   python webrtc_server_example.py")
    print("   # Uses default refresh token")
    
    print("\n🔧 Custom Configuration:")
    print("   python webrtc_signaling_server.py \\")
    print("       --refresh-token YOUR_TOKEN \\")
    print("       --port 1984 \\")
    print("       --webrtc-port 8555")
    
    print("\n🏠 Home Assistant Integration:")
    print("   # Add to configuration.yaml:")
    print("   camera:")
    print("     - platform: generic")
    print("       name: SimpliSafe Driveway")
    print("       stream_source: http://localhost:1984/api/stream.m3u8?src=driveway")
    print("       still_image_url: http://localhost:1984/api/frame.jpeg?src=driveway")
    
    print("\n🌐 Web Interface:")
    print("   SimpliSafe Interface: http://localhost:2984")
    print("   go2rtc Interface:     http://localhost:1984")
    
    print("\n📺 VLC Streaming:")
    print("   vlc http://localhost:1984/api/stream.flv?src=CAMERA_NAME")
    
    print("\n🐳 Docker Usage:")
    print("   docker run -p 1984:1984 -p 8555:8555/udp \\")
    print("       -v $(pwd)/go2rtc.yaml:/config/go2rtc.yaml \\")
    print("       alexxit/go2rtc")
    
    print("\n🔍 Troubleshooting:")
    print("   - Check camera status in SimpliSafe app")
    print("   - Ensure cameras are online and powered")
    print("   - Verify network connectivity")
    print("   - Check go2rtc logs for errors")


async def main():
    """Main function with options."""
    import argparse
    
    parser = argparse.ArgumentParser(description='SimpliSafe WebRTC Server Demo')
    parser.add_argument('--test-only', action='store_true', help='Test integration without starting server')
    parser.add_argument('--examples', action='store_true', help='Show usage examples')
    
    args = parser.parse_args()
    
    if args.examples:
        show_usage_examples()
        return
    
    if args.test_only:
        await test_webrtc_integration()
    else:
        await demo_webrtc_server()


if __name__ == "__main__":
    asyncio.run(main())
