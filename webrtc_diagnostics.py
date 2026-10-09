#!/usr/bin/env python3
"""
SimpliSafe WebRTC Connection Diagnostics
========================================

This script provides comprehensive diagnostics for SimpliSafe WebRTC connections,
including alternative testing methods and detailed error analysis.

Usage:
1. Run this script: python webrtc_diagnostics.py
2. Review the comprehensive connection analysis
3. Try different connection methods and troubleshooting steps
"""

import asyncio
import json
import logging
import socket
import ssl
import sys
import time
from datetime import datetime
from urllib.parse import urlparse

import simplipy
from aiohttp import ClientSession
from simplipy.errors import SimplipyError

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

REFRESH_TOKEN = "FVo238-EavENCZsXqJ_NZq2Tq_n7z6c3CTfg_iHl9tH4v"


def print_header(title):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_section(title):
    """Print a section header."""
    print(f"\n{title}")
    print("-" * len(title))


async def test_basic_connectivity():
    """Test basic internet connectivity and DNS resolution."""
    print_section("🌐 Basic Connectivity Tests")
    
    # Test DNS resolution
    try:
        host = "livestream.services.simplisafe.com"
        ip = socket.gethostbyname(host)
        print(f"✅ DNS Resolution: {host} -> {ip}")
    except Exception as e:
        print(f"❌ DNS Resolution Failed: {e}")
        return False
    
    # Test HTTPS connectivity
    try:
        import urllib.request
        response = urllib.request.urlopen("https://www.google.com", timeout=5)
        print(f"✅ HTTPS Connectivity: Working (status: {response.status})")
    except Exception as e:
        print(f"❌ HTTPS Connectivity Failed: {e}")
        return False
    
    # Test specific SimpliSafe host
    try:
        response = urllib.request.urlopen("https://api.simplisafe.com", timeout=10)
        print(f"✅ SimpliSafe API Reachable: Working (status: {response.status})")
    except Exception as e:
        print(f"⚠️  SimpliSafe API Check: {e}")
    
    return True


async def test_websocket_server_reachability(url):
    """Test if the WebSocket server is reachable via TCP."""
    print_section("🔌 WebSocket Server Reachability")
    
    try:
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == 'wss' else 80)
        
        print(f"Testing connection to {host}:{port}")
        
        # Test TCP connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        
        start_time = time.time()
        result = sock.connect_ex((host, port))
        duration = time.time() - start_time
        
        if result == 0:
            print(f"✅ TCP Connection: Success ({duration:.2f}s)")
            sock.close()
            
            # Test SSL if it's a secure connection
            if parsed.scheme == 'wss':
                try:
                    context = ssl.create_default_context()
                    with socket.create_connection((host, port), timeout=10) as sock:
                        with context.wrap_socket(sock, server_hostname=host) as ssock:
                            print(f"✅ SSL/TLS Connection: Success")
                            print(f"   Certificate: {ssock.getpeercert()['subject']}")
                except Exception as ssl_error:
                    print(f"❌ SSL/TLS Connection Failed: {ssl_error}")
                    return False
            
            return True
        else:
            print(f"❌ TCP Connection Failed: Error {result}")
            return False
            
    except Exception as e:
        print(f"❌ Connection Test Failed: {e}")
        return False
    finally:
        try:
            sock.close()
        except:
            pass


async def test_websocket_headers(url, token):
    """Test WebSocket connection with proper headers."""
    print_section("📋 WebSocket Headers Test")
    
    try:
        import websockets
        
        # Custom headers for LiveKit
        extra_headers = {
            'Authorization': f'Bearer {token}',
            'User-Agent': 'SimpliSafe-Python-Client/1.0',
            'Origin': 'https://simplisafe.com'
        }
        
        print(f"Attempting WebSocket connection to: {url}")
        print(f"Headers: {extra_headers}")
        
        async with websockets.connect(
            url,
            extra_headers=extra_headers,
            timeout=10,
            ping_interval=None
        ) as websocket:
            print(f"✅ WebSocket Connected Successfully")
            
            # Send a join message
            join_message = {
                "case": "join",
                "value": {
                    "token": token,
                    "autoSubscribe": True,
                    "publishOnly": False
                }
            }
            
            await websocket.send(json.dumps(join_message))
            print(f"✅ Join message sent")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                print(f"✅ Response received: {response[:100]}...")
                return True
            except asyncio.TimeoutError:
                print(f"⚠️  No response received within timeout")
                return False
                
    except ImportError:
        print("⚠️  websockets library not available, installing...")
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
            print("✅ websockets library installed, please run the script again")
            return False
        except Exception as install_error:
            print(f"❌ Failed to install websockets: {install_error}")
            return False
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False


async def analyze_livekit_connection_info(connection_info):
    """Analyze LiveKit connection information for potential issues."""
    print_section("🔍 LiveKit Connection Analysis")
    
    print(f"Connection Details:")
    print(f"• URL: {connection_info.get('url', 'Missing')}")
    print(f"• Token Length: {len(connection_info.get('token', ''))} characters")
    print(f"• Room: {connection_info.get('room', 'Unknown')}")
    print(f"• Participant: {connection_info.get('participant', 'Unknown')}")
    
    # Analyze URL
    url = connection_info.get('url', '')
    if url:
        parsed = urlparse(url)
        print(f"\nURL Analysis:")
        print(f"• Protocol: {parsed.scheme}")
        print(f"• Host: {parsed.hostname}")
        print(f"• Port: {parsed.port or 'default'}")
        print(f"• Path: {parsed.path or '/'}")
        
        if parsed.scheme not in ['ws', 'wss']:
            print(f"⚠️  Unusual protocol: {parsed.scheme}")
        
        if not parsed.hostname:
            print(f"❌ Missing hostname in URL")
            return False
    else:
        print(f"❌ Missing URL in connection info")
        return False
    
    # Analyze token
    token = connection_info.get('token', '')
    if token:
        try:
            # Basic JWT structure check (header.payload.signature)
            parts = token.split('.')
            if len(parts) == 3:
                print(f"✅ Token structure looks correct (JWT format)")
                
                # Try to decode header (it's usually not encrypted)
                import base64
                try:
                    header_padded = parts[0] + '=' * (4 - len(parts[0]) % 4)
                    header = json.loads(base64.b64decode(header_padded))
                    print(f"• Token Type: {header.get('typ', 'Unknown')}")
                    print(f"• Algorithm: {header.get('alg', 'Unknown')}")
                except:
                    print(f"• Token header not decodable (normal for some tokens)")
            else:
                print(f"⚠️  Token doesn't appear to be JWT format")
        except Exception as e:
            print(f"⚠️  Token analysis failed: {e}")
    else:
        print(f"❌ Missing token in connection info")
        return False
    
    return True


async def test_alternative_connection_methods(camera):
    """Test alternative methods for camera connection."""
    print_section("🔄 Alternative Connection Methods")
    
    # Test 1: Direct snapshot (should work for all cameras)
    try:
        print("Testing direct snapshot access...")
        start_time = time.time()
        snapshot_data = await camera.async_get_snapshot(width=320, timeout=10)
        duration = time.time() - start_time
        print(f"✅ Snapshot: {len(snapshot_data):,} bytes in {duration:.2f}s")
    except Exception as e:
        print(f"❌ Snapshot failed: {e}")
    
    # Test 2: Camera status refresh
    try:
        print("Testing camera status refresh...")
        # Force a refresh of camera data
        await camera._api.async_get_systems()
        print(f"✅ Camera status: {camera.status}")
    except Exception as e:
        print(f"❌ Status refresh failed: {e}")
    
    # Test 3: Check for standard streaming (fallback)
    if hasattr(camera, 'supports_standard_streaming') and camera.supports_standard_streaming:
        try:
            from simplipy.device.camera import StreamFormat
            flv_url = camera.stream_url(format_type=StreamFormat.FLV, width=640)
            print(f"✅ Standard streaming available: {flv_url[:50]}...")
        except Exception as e:
            print(f"❌ Standard streaming failed: {e}")
    else:
        print("ℹ️  Standard streaming not supported for this camera type")


async def generate_troubleshooting_report(camera, connection_info):
    """Generate a comprehensive troubleshooting report."""
    print_header("📊 Troubleshooting Report")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"webrtc_diagnostics_{camera.name.replace(' ', '_')}_{timestamp}.json"
    
    report = {
        "timestamp": timestamp,
        "camera": {
            "name": camera.name,
            "type": getattr(camera, 'camera_type', 'Unknown'),
            "status": camera.status,
            "serial": camera.serial,
            "is_outdoor": getattr(camera, 'is_outdoor_camera', False),
            "streaming_provider": getattr(camera, 'streaming_provider', 'Unknown'),
            "supports_webrtc": getattr(camera, 'supports_webrtc_streaming', False)
        },
        "connection_info": connection_info,
        "tests_performed": [],
        "recommendations": []
    }
    
    # Basic connectivity test
    if await test_basic_connectivity():
        report["tests_performed"].append("Basic connectivity: PASSED")
    else:
        report["tests_performed"].append("Basic connectivity: FAILED")
        report["recommendations"].append("Check internet connection and DNS settings")
    
    # WebSocket server reachability
    if connection_info and connection_info.get('url'):
        if await test_websocket_server_reachability(connection_info['url']):
            report["tests_performed"].append("WebSocket server reachability: PASSED")
        else:
            report["tests_performed"].append("WebSocket server reachability: FAILED")
            report["recommendations"].append("Check firewall and proxy settings")
    
    # LiveKit connection analysis
    if connection_info:
        if await analyze_livekit_connection_info(connection_info):
            report["tests_performed"].append("LiveKit connection analysis: PASSED")
        else:
            report["tests_performed"].append("LiveKit connection analysis: FAILED")
            report["recommendations"].append("Check LiveKit connection parameters")
    
    # Alternative methods
    await test_alternative_connection_methods(camera)
    report["tests_performed"].append("Alternative connection methods: TESTED")
    
    # Common issues and solutions
    report["common_issues"] = {
        "websocket_error_1006": {
            "description": "WebSocket closed abnormally (error 1006)",
            "possible_causes": [
                "Network connectivity issues",
                "Firewall blocking WebSocket connections",
                "Proxy server interference",
                "SimpliSafe server temporarily unavailable",
                "Authentication token expired or invalid"
            ],
            "solutions": [
                "Check internet connection stability",
                "Try from different network (mobile hotspot)",
                "Disable VPN/proxy temporarily",
                "Wait and retry (server may be temporarily down)",
                "Refresh authentication token"
            ]
        },
        "livekit_connection_failed": {
            "description": "LiveKit WebRTC connection failed",
            "possible_causes": [
                "WebRTC not supported by browser",
                "Network NAT/firewall blocking WebRTC",
                "STUN/TURN servers not reachable",
                "Camera not properly awakened"
            ],
            "solutions": [
                "Use Chrome/Edge browser for best WebRTC support",
                "Check firewall settings for WebRTC traffic",
                "Try from different network environment",
                "Ensure camera is online and awakened"
            ]
        }
    }
    
    # Working alternatives
    report["working_alternatives"] = {
        "snapshots": "Use async_get_snapshot() for still images",
        "standard_streaming": "Use stream_url() for indoor/doorbell cameras",
        "vlc_streaming": "Use VLC with generated stream URLs",
        "python_webrtc": "Use aiortc library for WebRTC in Python"
    }
    
    # Save report
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"📋 Diagnostic report saved: {report_file}")
    
    # Print summary
    print(f"\n🎯 Summary:")
    print(f"• Camera: {camera.name} ({camera.status})")
    print(f"• WebRTC Support: {getattr(camera, 'supports_webrtc_streaming', False)}")
    print(f"• Connection URL: {connection_info.get('url', 'N/A') if connection_info else 'N/A'}")
    
    print(f"\n💡 Immediate Recommendations:")
    for rec in report["recommendations"]:
        print(f"   • {rec}")
    
    if not report["recommendations"]:
        print(f"   • Connection parameters look correct")
        print(f"   • Issue likely temporary - try again later")
        print(f"   • Consider using snapshot functionality as alternative")
    
    return report


async def main():
    """Main diagnostic function."""
    print_header("SimpliSafe WebRTC Connection Diagnostics")
    print("This tool provides comprehensive diagnostics for WebRTC connection issues.")
    print("Error 1006 typically indicates network connectivity or server availability problems.")
    
    async with ClientSession() as session:
        try:
            # Authenticate
            logger.info("🔑 Authenticating with SimpliSafe...")
            api = await simplipy.API.async_from_refresh_token(REFRESH_TOKEN, session=session)
            
            # Get systems
            logger.info("🏠 Getting systems...")
            systems = await api.async_get_systems()
            
            if not systems:
                print("❌ No systems found")
                return
            
            system = list(systems.values())[0]
            logger.info(f"✅ Using system: {system.system_id}")
            
            # Find WebRTC camera
            webrtc_camera = None
            for camera in system.cameras.values():
                if hasattr(camera, 'supports_webrtc_streaming') and camera.supports_webrtc_streaming:
                    webrtc_camera = camera
                    break
            
            if not webrtc_camera:
                print("❌ No WebRTC-capable cameras found")
                return
            
            print(f"\n🎥 Testing camera: {webrtc_camera.name}")
            print(f"   Status: {webrtc_camera.status}")
            print(f"   Provider: {getattr(webrtc_camera, 'streaming_provider', 'Unknown')}")
            
            # Get connection info
            connection_info = None
            try:
                logger.info("📡 Getting LiveKit connection info...")
                connection_info = await webrtc_camera.async_get_livekit_connection_info()
                print(f"✅ LiveKit connection info retrieved")
            except Exception as e:
                print(f"❌ Failed to get LiveKit connection info: {e}")
            
            # Run comprehensive diagnostics
            await generate_troubleshooting_report(webrtc_camera, connection_info)
            
            # Test WebSocket connection if we have connection info
            if connection_info and connection_info.get('url') and connection_info.get('token'):
                print_section("🧪 Direct WebSocket Test")
                await test_websocket_headers(connection_info['url'], connection_info['token'])
            
            print_header("🔗 Next Steps")
            print("1. Review the diagnostic report for specific issues")
            print("2. Try the recommended solutions")
            print("3. Use alternative methods if WebRTC continues to fail:")
            print("   • Snapshots: python test_direct_snapshot.py")
            print("   • Standard streaming: python vlc_streaming_guide.py")
            print("4. Contact SimpliSafe support if issues persist")
            
        except SimplipyError as err:
            logger.error(f"SimpliSafe API error: {err}")
        except Exception as err:
            logger.error(f"Unexpected error: {err}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
