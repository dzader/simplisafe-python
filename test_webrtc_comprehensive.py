#!/usr/bin/env python3
"""
WebRTC Streaming Test Guide for SimpliSafe Outdoor Cameras
==========================================================

This script demonstrates how to test WebRTC streaming for outdoor SimpliSafe cameras
and provides multiple methods for viewing the streams.
"""

import asyncio
import logging
import json
import webbrowser
import os
from datetime import datetime
from aiohttp import ClientSession

import simplipy
from simplipy.errors import SimplipyError

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

REFRESH_TOKEN = "FVo238-EavENCZsXqJ_NZq2Tq_n7z6c3CTfg_iHl9tH4v"


def create_web_test_page(camera_name, livekit_url, token):
    """Create an HTML page to test WebRTC streaming in browser."""
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SimpliSafe {camera_name} - WebRTC Test</title>
    <script src="https://unpkg.com/livekit-client@2/dist/livekit-client.umd.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            text-align: center;
        }}
        .status {{
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
            font-weight: bold;
        }}
        .status.connecting {{ background: #fff3cd; color: #856404; }}
        .status.connected {{ background: #d4edda; color: #155724; }}
        .status.error {{ background: #f8d7da; color: #721c24; }}
        .video-container {{
            text-align: center;
            margin: 20px 0;
        }}
        video {{
            max-width: 100%;
            max-height: 600px;
            border: 2px solid #ddd;
            border-radius: 8px;
            background: #000;
        }}
        .controls {{
            text-align: center;
            margin: 20px 0;
        }}
        button {{
            background: #007bff;
            color: white;
            border: none;
            padding: 12px 24px;
            margin: 5px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }}
        button:hover {{ background: #0056b3; }}
        button:disabled {{ background: #6c757d; cursor: not-allowed; }}
        .info {{
            background: #e9ecef;
            padding: 15px;
            border-radius: 4px;
            margin: 10px 0;
        }}
        .info h3 {{ margin-top: 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎥 SimpliSafe {camera_name} WebRTC Stream</h1>
        
        <div id="status" class="status connecting">Initializing...</div>
        
        <div class="controls">
            <button id="connectBtn" onclick="connectToRoom()">Connect to Camera</button>
            <button id="disconnectBtn" onclick="disconnectFromRoom()" disabled>Disconnect</button>
        </div>
        
        <div class="video-container">
            <video id="videoElement" autoplay muted playsinline controls>
                Your browser doesn't support video playback.
            </video>
        </div>
        
        <div class="info">
            <h3>📋 Connection Info:</h3>
            <p><strong>Camera:</strong> {camera_name}</p>
            <p><strong>LiveKit URL:</strong> {livekit_url}</p>
            <p><strong>Token Expires:</strong> ~10 minutes from generation</p>
            <p><strong>Status:</strong> <span id="detailedStatus">Ready to connect</span></p>
        </div>
        
        <div class="info">
            <h3>📖 Instructions:</h3>
            <ol>
                <li>Click <strong>"Connect to Camera"</strong> to start streaming</li>
                <li>Your camera will wake up (may take 10-30 seconds)</li>
                <li>Video should appear once connected</li>
                <li>Use browser's video controls for volume, fullscreen, etc.</li>
                <li>Click <strong>"Disconnect"</strong> when done</li>
            </ol>
        </div>
        
        <div class="info">
            <h3>🔧 Troubleshooting:</h3>
            <ul>
                <li><strong>No video:</strong> Check that camera is online in SimpliSafe app</li>
                <li><strong>Connection fails:</strong> Token may have expired, regenerate</li>
                <li><strong>Audio issues:</strong> Click video to unmute (browser policy)</li>
                <li><strong>Performance:</strong> Try Chrome or Edge for best WebRTC support</li>
            </ul>
        </div>
    </div>

    <script>
        const LiveKit = window.LiveKit;
        let room = null;
        let connected = false;
        
        const wsUrl = '{livekit_url}';
        const token = '{token}';
        
        const statusDiv = document.getElementById('status');
        const detailedStatus = document.getElementById('detailedStatus');
        const connectBtn = document.getElementById('connectBtn');
        const disconnectBtn = document.getElementById('disconnectBtn');
        const videoElement = document.getElementById('videoElement');
        
        function updateStatus(message, type = 'connecting') {{
            statusDiv.className = `status ${{type}}`;
            statusDiv.textContent = message;
            detailedStatus.textContent = message;
        }}
        
        async function connectToRoom() {{
            try {{
                updateStatus('Connecting to SimpliSafe camera...', 'connecting');
                connectBtn.disabled = true;
                
                // Create room instance
                room = new LiveKit.Room({{
                    adaptiveStream: true,
                    dynacast: true,
                }});
                
                // Set up event handlers
                room.on(LiveKit.RoomEvent.Connected, () => {{
                    updateStatus('Connected! Waiting for video...', 'connected');
                    console.log('Connected to room');
                }});
                
                room.on(LiveKit.RoomEvent.TrackSubscribed, (track, publication, participant) => {{
                    console.log('Track subscribed:', track.kind);
                    if (track.kind === 'video') {{
                        updateStatus('Video stream active!', 'connected');
                        track.attach(videoElement);
                    }}
                }});
                
                room.on(LiveKit.RoomEvent.TrackUnsubscribed, (track) => {{
                    track.detach();
                }});
                
                room.on(LiveKit.RoomEvent.Disconnected, () => {{
                    updateStatus('Disconnected from camera', 'connecting');
                    connectBtn.disabled = false;
                    disconnectBtn.disabled = true;
                    connected = false;
                }});
                
                room.on(LiveKit.RoomEvent.ConnectionQualityChanged, (quality, participant) => {{
                    console.log('Connection quality:', quality);
                }});
                
                // Connect to the room
                await room.connect(wsUrl, token);
                connected = true;
                disconnectBtn.disabled = false;
                
            }} catch (error) {{
                console.error('Connection failed:', error);
                updateStatus(`Connection failed: ${{error.message}}`, 'error');
                connectBtn.disabled = false;
            }}
        }}
        
        async function disconnectFromRoom() {{
            if (room && connected) {{
                await room.disconnect();
                room = null;
                connected = false;
                updateStatus('Disconnected from camera', 'connecting');
                connectBtn.disabled = false;
                disconnectBtn.disabled = true;
                
                // Clear video
                videoElement.srcObject = null;
            }}
        }}
        
        // Auto-connect on page load (optional)
        // setTimeout(connectToRoom, 1000);
    </script>
</body>
</html>
"""
    
    filename = f"webrtc_test_{camera_name.replace(' ', '_')}.html"
    with open(filename, "w") as f:
        f.write(html_content)
    
    return filename


async def test_webrtc_streaming():
    """Test WebRTC streaming for outdoor cameras."""
    
    print("🌐 SimpliSafe WebRTC Streaming Test")
    print("=" * 40)
    
    async with ClientSession() as session:
        try:
            # Authenticate
            logger.info("🔑 Authenticating with SimpliSafe...")
            api = await simplipy.API.async_from_refresh_token(REFRESH_TOKEN, session=session)
            
            # Get systems
            systems = await api.async_get_systems()
            system = list(systems.values())[0]
            
            # Find outdoor cameras
            outdoor_cameras = [c for c in system.cameras.values() 
                             if c.supports_webrtc_streaming and c.status == "online"]
            
            if not outdoor_cameras:
                print("❌ No online outdoor cameras found")
                return
            
            print(f"📊 Found {len(outdoor_cameras)} outdoor camera(s)")
            
            for camera in outdoor_cameras:
                print(f"\n🎥 Testing: {camera.name}")
                print("-" * 30)
                
                try:
                    # Get WebRTC connection info
                    logger.info(f"Getting WebRTC info for {camera.name}...")
                    connection_info = await camera.async_get_livekit_connection_info()
                    
                    print(f"✅ WebRTC connection ready!")
                    print(f"   • Camera: {camera.name}")
                    print(f"   • Provider: {camera.streaming_provider}")
                    print(f"   • Status: {connection_info['camera_status']}")
                    print(f"   • LiveKit URL: {connection_info['url']}")
                    print(f"   • Token length: {len(connection_info['token'])} chars")
                    
                    # Save connection info
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    json_filename = f"webrtc_connection_{camera.name.replace(' ', '_')}_{timestamp}.json"
                    with open(json_filename, "w") as f:
                        json.dump(connection_info, f, indent=2)
                    print(f"   💾 Connection info saved: {json_filename}")
                    
                    # Create web test page
                    html_filename = create_web_test_page(
                        camera.name, 
                        connection_info['url'], 
                        connection_info['token']
                    )
                    print(f"   🌐 Web test page created: {html_filename}")
                    
                    # Generate other integration examples
                    print(f"\n📋 Integration Examples:")
                    
                    # Python LiveKit example
                    python_example = f"""
# Python LiveKit Client Example
import asyncio
from livekit import Room, RoomOptions

async def stream_camera():
    room = Room()
    await room.connect(
        "{connection_info['url']}", 
        "{connection_info['token']}"
    )
    
    @room.on("track_subscribed")
    def on_track_subscribed(track, publication, participant):
        print(f"Subscribed to {{track.kind}} track")
        if track.kind == "video":
            # Handle video track
            pass
    
    # Keep connection alive
    await asyncio.sleep(60)
    await room.disconnect()

asyncio.run(stream_camera())
"""
                    
                    python_filename = f"python_example_{camera.name.replace(' ', '_')}.py"
                    with open(python_filename, "w") as f:
                        f.write(python_example.strip())
                    print(f"   🐍 Python example: {python_filename}")
                    
                    # FFmpeg example
                    print(f"\n🎬 FFmpeg Integration:")
                    print(f"   # Convert WebRTC to RTMP (requires FFmpeg with WebRTC support)")
                    print(f"   ffmpeg -protocol_whitelist file,http,https,tcp,tls,ws,wss \\")
                    print(f"          -i '{connection_info['url']}?token={connection_info['token'][:50]}...' \\")
                    print(f"          -c copy -f flv rtmp://localhost/live/{camera.name.replace(' ', '_')}")
                    
                    # go2rtc example
                    print(f"\n🔄 go2rtc Configuration:")
                    go2rtc_config = f"""
# Add to go2rtc.yaml
streams:
  {camera.name.replace(' ', '_').lower()}:
    - "livekit://{connection_info['url'].replace('wss://', '')}?token={connection_info['token']}"
"""
                    print(go2rtc_config)
                    
                    go2rtc_filename = f"go2rtc_config_{camera.name.replace(' ', '_')}.yaml"
                    with open(go2rtc_filename, "w") as f:
                        f.write(go2rtc_config.strip())
                    print(f"   ⚙️  go2rtc config saved: {go2rtc_filename}")
                    
                except Exception as err:
                    print(f"❌ Failed to test {camera.name}: {err}")
            
            print(f"\n🚀 How to Test WebRTC Streaming:")
            print("=" * 40)
            print("1. 🌐 BROWSER TEST (Easiest):")
            print("   • Open the generated .html file in Chrome/Edge")
            print("   • Click 'Connect to Camera'")
            print("   • Wait for video to appear (10-30 seconds)")
            
            print("\n2. 🐍 PYTHON LIVEKIT:")
            print("   • Install: pip install livekit")
            print("   • Run the generated Python example")
            
            print("\n3. 🔄 GO2RTC (For Home Assistant/VLC):")
            print("   • Install go2rtc")
            print("   • Use the generated config")
            print("   • Stream to VLC: http://localhost:1984/api/stream.flv?src=camera_name")
            
            print("\n4. 🎬 FFMPEG (Advanced):")
            print("   • Requires FFmpeg with WebRTC support")
            print("   • Can convert to RTMP/HLS for other players")
            
            print(f"\n⚠️  Important Notes:")
            print("   • Tokens expire in ~10 minutes")
            print("   • Camera must be online and awake")
            print("   • Chrome/Edge have best WebRTC support")
            print("   • May take 10-30 seconds for video to start")
            
            # Offer to open browser test
            if outdoor_cameras:
                camera = outdoor_cameras[0]
                html_file = f"webrtc_test_{camera.name.replace(' ', '_')}.html"
                
                print(f"\n🌐 Open browser test? (y/n): ", end="")
                import sys
                if sys.stdin.isatty():
                    try:
                        choice = input().lower().strip()
                        if choice in ['y', 'yes']:
                            file_path = os.path.abspath(html_file)
                            webbrowser.open(f"file://{file_path}")
                            print(f"   ✅ Opened {html_file} in default browser")
                    except:
                        pass
                
        except Exception as err:
            logger.error(f"❌ Test failed: {err}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_webrtc_streaming())
