#!/usr/bin/env python3
"""
Direct WebSocket Test for SimpliSafe LiveKit
===========================================

This script tests the WebSocket connection directly using the websockets library
to diagnose the error 1006 issue.
"""

import asyncio
import json
import logging
from aiohttp import ClientSession
import simplipy
import websockets

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

REFRESH_TOKEN = "FVo238-EavENCZsXqJ_NZq2Tq_n7z6c3CTfg_iHl9tH4v"


async def test_direct_websocket():
    """Test direct WebSocket connection to LiveKit server."""
    
    async with ClientSession() as session:
        try:
            # Get camera and connection info
            logger.info("Getting LiveKit connection info...")
            api = await simplipy.API.async_from_refresh_token(REFRESH_TOKEN, session=session)
            systems = await api.async_get_systems()
            system = list(systems.values())[0]
            
            # Find outdoor camera
            camera = None
            for cam in system.cameras.values():
                if hasattr(cam, 'supports_webrtc_streaming') and cam.supports_webrtc_streaming:
                    camera = cam
                    break
            
            if not camera:
                print("❌ No WebRTC camera found")
                return
            
            # Get connection info
            connection_info = await camera.async_get_livekit_connection_info()
            url = connection_info['url']
            token = connection_info['token']
            
            print(f"🎥 Camera: {camera.name}")
            print(f"🔗 URL: {url}")
            print(f"🎫 Token: {token[:50]}...")
            
            print(f"\n🧪 Testing direct WebSocket connection...")
            
            # Test different connection approaches
            approaches = [
                {"name": "Basic Connection", "headers": {}},
                {"name": "With Authorization", "headers": {"Authorization": f"Bearer {token}"}},
                {"name": "With User-Agent", "headers": {"User-Agent": "SimpliSafe-Client/1.0"}},
                {"name": "With Origin", "headers": {"Origin": "https://simplisafe.com"}},
                {"name": "Full Headers", "headers": {
                    "Authorization": f"Bearer {token}",
                    "User-Agent": "SimpliSafe-Client/1.0",
                    "Origin": "https://simplisafe.com"
                }}
            ]
            
            for approach in approaches:
                print(f"\n📡 Trying: {approach['name']}")
                try:
                    # Set timeout and ping settings
                    timeout_config = {
                        'timeout': 10,
                        'ping_interval': 20,
                        'ping_timeout': 10,
                        'close_timeout': 5
                    }
                    
                    async with websockets.connect(
                        url,
                        extra_headers=approach['headers'],
                        **timeout_config
                    ) as websocket:
                        print(f"   ✅ Connection established!")
                        
                        # Send join message
                        join_message = {
                            "case": "join",
                            "value": {
                                "token": token,
                                "autoSubscribe": True,
                                "publishOnly": False
                            }
                        }
                        
                        print(f"   📤 Sending join message...")
                        await websocket.send(json.dumps(join_message))
                        
                        # Wait for response
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=5)
                            print(f"   ✅ Response received: {response[:100]}...")
                            
                            # Try to parse response
                            try:
                                resp_data = json.loads(response)
                                print(f"   📋 Response type: {resp_data.get('case', 'unknown')}")
                            except:
                                print(f"   📋 Response (raw): {response[:50]}...")
                            
                            # Keep connection alive for a moment
                            print(f"   ⏱️  Keeping connection alive for 10 seconds...")
                            await asyncio.sleep(10)
                            
                            print(f"   ✅ Connection stable - SUCCESS!")
                            return True
                            
                        except asyncio.TimeoutError:
                            print(f"   ⚠️  No response within timeout")
                        except Exception as recv_error:
                            print(f"   ❌ Error receiving data: {recv_error}")
                        
                except websockets.exceptions.ConnectionClosedError as e:
                    print(f"   ❌ Connection closed: {e.code} - {e.reason}")
                except websockets.exceptions.InvalidStatusCode as e:
                    print(f"   ❌ Invalid status code: {e.status_code}")
                except Exception as e:
                    print(f"   ❌ Connection failed: {e}")
                
                # Wait between attempts
                await asyncio.sleep(2)
            
            print(f"\n❌ All connection approaches failed")
            return False
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            return False


async def analyze_error_1006():
    """Analyze the WebSocket error 1006 and provide solutions."""
    
    print(f"\n{'='*60}")
    print(f"  WebSocket Error 1006 Analysis")
    print(f"{'='*60}")
    
    print(f"""
🔍 What is Error 1006?
Error 1006 is a WebSocket close code that means "Abnormal Closure".
This happens when the connection is closed without a proper close frame.

🎯 Common Causes:
1. Network connectivity issues
2. Firewall blocking WebSocket connections
3. Proxy server interference
4. Server temporarily unavailable
5. Authentication/authorization failure
6. Browser security restrictions

💡 Solutions to Try:

1. Network Troubleshooting:
   • Check internet connection stability
   • Try from different network (mobile hotspot)
   • Disable VPN/proxy temporarily
   • Check firewall settings

2. Browser-Specific:
   • Use Chrome or Edge (best WebRTC support)
   • Clear browser cache and cookies
   • Disable browser extensions
   • Try incognito/private mode

3. Alternative Testing:
   • Use Python websockets library (this script)
   • Test from different computer/device
   • Try at different time (server load)

4. SimpliSafe Specific:
   • Ensure camera is online and awake
   • Refresh authentication token
   • Check SimpliSafe service status

5. Development Workarounds:
   • Use snapshot functionality instead
   • Use standard streaming for indoor cameras
   • Implement retry logic with backoff
   • Add connection health monitoring
""")


async def main():
    """Main function."""
    print(f"🔌 Direct WebSocket Test for SimpliSafe LiveKit")
    print(f"=" * 50)
    
    success = await test_direct_websocket()
    
    if not success:
        await analyze_error_1006()
        
        print(f"\n🔄 Recommended Next Steps:")
        print(f"1. Try the direct snapshot test: python test_direct_snapshot.py")
        print(f"2. Check VLC streaming: python vlc_streaming_guide.py") 
        print(f"3. Run full diagnostic: python webrtc_diagnostics.py")
        print(f"4. Try from different network/device")
        print(f"5. Contact SimpliSafe support if issue persists")
    else:
        print(f"\n✅ WebSocket connection working!")
        print(f"   The error 1006 may be browser-specific.")
        print(f"   Try refreshing the browser test page.")


if __name__ == "__main__":
    asyncio.run(main())
