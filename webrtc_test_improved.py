#!/usr/bin/env python3
"""
WebRTC Streaming Test for SimpliSafe Outdoor Cameras
===================================================

This script creates a comprehensive WebRTC test for your outdoor cameras,
generating HTML test pages and connection examples.
"""

import asyncio
import logging
import json
import webbrowser
import os
from aiohttp import ClientSession
from simplipy import API

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

REFRESH_TOKEN = "FVo238-EavENCZsXqJ_NZq2Tq_n7z6c3CTfg_iHl9tH4v"


def create_webrtc_test_html(camera_name, connection_info):
    """Create a comprehensive WebRTC test HTML page."""
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SimpliSafe {camera_name} - WebRTC Test</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e1e5e9;
        }}
        .video-container {{
            position: relative;
            background: #000;
            border-radius: 8px;
            overflow: hidden;
            margin: 20px 0;
        }}
        #videoElement {{
            width: 100%;
            height: 400px;
            object-fit: cover;
        }}
        .controls {{
            display: flex;
            gap: 10px;
            justify-content: center;
            margin: 20px 0;
        }}
        button {{
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s;
        }}
        .connect-btn {{
            background: #28a745;
            color: white;
        }}
        .connect-btn:hover {{
            background: #218838;
        }}
        .disconnect-btn {{
            background: #dc3545;
            color: white;
        }}
        .disconnect-btn:hover {{
            background: #c82333;
        }}
        .connect-btn:disabled, .disconnect-btn:disabled {{
            opacity: 0.6;
            cursor: not-allowed;
        }}
        .status {{
            text-align: center;
            padding: 10px;
            border-radius: 6px;
            margin: 10px 0;
            font-weight: 600;
        }}
        .status.connecting {{
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }}
        .status.connected {{
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }}
        .status.disconnected {{
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }}
        .info {{
            background: #e7f3ff;
            border: 1px solid #b8daff;
            padding: 15px;
            border-radius: 6px;
            margin: 20px 0;
        }}
        .error {{
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
            padding: 15px;
            border-radius: 6px;
            margin: 10px 0;
        }}
        .debug {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            padding: 15px;
            border-radius: 6px;
            margin: 20px 0;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 12px;
            white-space: pre-wrap;
            max-height: 200px;
            overflow-y: auto;
        }}
        .loading {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #3498db;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎥 SimpliSafe Camera: {camera_name}</h1>
            <p>WebRTC Live Stream Test</p>
        </div>

        <div class="video-container">
            <video id="videoElement" autoplay muted playsinline>
                <p>Video not supported by your browser.</p>
            </video>
        </div>

        <div class="controls">
            <button id="connectBtn" class="connect-btn">
                <span id="connectText">Connect to Camera</span>
                <span id="connectLoading" class="loading" style="display: none;"></span>
            </button>
            <button id="disconnectBtn" class="disconnect-btn" disabled>Disconnect</button>
        </div>

        <div id="status" class="status disconnected">Ready to connect</div>

        <div class="info">
            <h3>📋 Instructions:</h3>
            <ol>
                <li><strong>Click "Connect to Camera"</strong> to start the WebRTC connection</li>
                <li><strong>Wait 10-30 seconds</strong> for the outdoor camera to wake up</li>
                <li><strong>Video should appear</strong> once connected successfully</li>
                <li><strong>Check the debug log</strong> below if there are any issues</li>
            </ol>
            
            <h3>🔧 Requirements:</h3>
            <ul>
                <li>Modern browser (Chrome, Edge, Safari, Firefox)</li>
                <li>Secure connection (HTTPS or localhost)</li>
                <li>Camera must be online and charged</li>
            </ul>
        </div>

        <div id="errorContainer" style="display: none;"></div>

        <details>
            <summary><strong>🐛 Debug Information</strong></summary>
            <div id="debugLog" class="debug">Debug log will appear here...\n</div>
        </details>
    </div>

    <!-- LiveKit SDK from CDN -->
    <script src="https://unpkg.com/livekit-client@2.5.7/dist/livekit-client.umd.js"></script>
    
    <script>
        // Connection configuration
        const config = {connection_info};
        
        // UI elements
        const videoElement = document.getElementById('videoElement');
        const connectBtn = document.getElementById('connectBtn');
        const disconnectBtn = document.getElementById('disconnectBtn');
        const statusDiv = document.getElementById('status');
        const errorContainer = document.getElementById('errorContainer');
        const debugLog = document.getElementById('debugLog');
        const connectText = document.getElementById('connectText');
        const connectLoading = document.getElementById('connectLoading');
        
        // LiveKit room and connection
        let room = null;
        let isConnecting = false;
        
        // Debug logging
        function log(message) {{
            const timestamp = new Date().toISOString().split('T')[1].split('.')[0];
            debugLog.textContent += `[${{timestamp}}] ${{message}}\n`;
            debugLog.scrollTop = debugLog.scrollHeight;
            console.log(message);
        }}
        
        // Show error message
        function showError(message) {{
            errorContainer.innerHTML = `<div class="error"><strong>❌ Error:</strong> ${{message}}</div>`;
            errorContainer.style.display = 'block';
            log(`ERROR: ${{message}}`);
        }}
        
        // Update connection status
        function updateStatus(message, className) {{
            statusDiv.textContent = message;
            statusDiv.className = `status ${{className}}`;
            log(`STATUS: ${{message}}`);
        }}
        
        // Update button states
        function updateButtons(connecting) {{
            isConnecting = connecting;
            connectBtn.disabled = connecting || (room && room.state === 'connected');
            disconnectBtn.disabled = !room || room.state === 'disconnected';
            
            if (connecting) {{
                connectText.style.display = 'none';
                connectLoading.style.display = 'inline-block';
            }} else {{
                connectText.style.display = 'inline-block';
                connectLoading.style.display = 'none';
            }}
        }}
        
        // Connect to camera
        async function connectToCamera() {{
            try {{
                // Hide previous errors
                errorContainer.style.display = 'none';
                
                // Check if LiveKit is available
                if (typeof LiveKit === 'undefined') {{
                    throw new Error('LiveKit SDK not loaded. Please check your internet connection.');
                }}
                
                log('Starting connection to SimpliSafe camera...');
                updateStatus('Connecting to camera...', 'connecting');
                updateButtons(true);
                
                // Create room
                room = new LiveKit.Room({{
                    adaptiveStream: true,
                    dynacast: true,
                    videoCaptureDefaults: {{
                        resolution: LiveKit.VideoPresets.h720.resolution,
                    }},
                }});
                
                // Set up event handlers
                room.on(LiveKit.RoomEvent.Connected, () => {{
                    log('Successfully connected to LiveKit room');
                    updateStatus('Connected! Waiting for video...', 'connecting');
                }});
                
                room.on(LiveKit.RoomEvent.TrackSubscribed, (track, publication, participant) => {{
                    log(`Track subscribed: ${{track.kind}} from ${{participant.identity}}`);
                    
                    if (track.kind === LiveKit.Track.Kind.Video) {{
                        log('Video track received, attaching to video element');
                        track.attach(videoElement);
                        updateStatus('✅ Video streaming successfully!', 'connected');
                        updateButtons(false);
                    }}
                }});
                
                room.on(LiveKit.RoomEvent.TrackUnsubscribed, (track) => {{
                    log('Track unsubscribed');
                    track.detach();
                }});
                
                room.on(LiveKit.RoomEvent.Disconnected, (reason) => {{
                    log(`Disconnected from room: ${{reason}}`);
                    updateStatus('Disconnected', 'disconnected');
                    updateButtons(false);
                    videoElement.srcObject = null;
                }});
                
                room.on(LiveKit.RoomEvent.ConnectionQualityChanged, (quality, participant) => {{
                    log(`Connection quality: ${{quality}} for ${{participant?.identity || 'local'}}`);
                }});
                
                room.on(LiveKit.RoomEvent.ParticipantConnected, (participant) => {{
                    log(`Participant joined: ${{participant.identity}}`);
                }});
                
                // Connect with timeout
                log(`Connecting to: ${{config.url}}`);
                log('Token length: ' + config.token.length + ' characters');
                
                const connectPromise = room.connect(config.url, config.token);
                const timeoutPromise = new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('Connection timeout after 30 seconds')), 30000)
                );
                
                await Promise.race([connectPromise, timeoutPromise]);
                
                log('Connection established, waiting for video tracks...');
                
                // Wait a bit more for tracks to be available
                setTimeout(() => {{
                    if (room.remoteParticipants.size === 0) {{
                        log('No remote participants found. Camera may be sleeping or offline.');
                        updateStatus('Camera connected but no video available. Camera may be sleeping.', 'connecting');
                    }}
                }}, 5000);
                
            }} catch (error) {{
                log(`Connection failed: ${{error.message}}`);
                showError(`Connection failed: ${{error.message}}`);
                updateStatus('Connection failed', 'disconnected');
                updateButtons(false);
                
                if (room) {{
                    room.disconnect();
                    room = null;
                }}
            }}
        }}
        
        // Disconnect from camera
        function disconnectFromCamera() {{
            if (room) {{
                log('Disconnecting from camera...');
                room.disconnect();
                room = null;
            }}
            videoElement.srcObject = null;
            updateStatus('Disconnected', 'disconnected');
            updateButtons(false);
        }}
        
        // Button event listeners
        connectBtn.addEventListener('click', connectToCamera);
        disconnectBtn.addEventListener('click', disconnectFromCamera);
        
        // Initialize
        log('WebRTC test page loaded');
        log('LiveKit SDK available: ' + (typeof LiveKit !== 'undefined'));
        log('Camera: {camera_name}');
        log('Ready to connect...');
        
        // Auto-expand debug on errors
        window.addEventListener('error', () => {{
            document.querySelector('details').open = true;
        }});
        
    </script>
</body>
</html>"""
    
    return html_content


async def test_webrtc_streaming():
    """Test WebRTC streaming and generate test files."""
    
    async with ClientSession() as session:
        try:
            print("🌐 SimpliSafe WebRTC Streaming Test")
            print("=" * 40)
            
            # Authenticate
            logger.info("🔑 Authenticating with SimpliSafe...")
            api = await API.async_from_refresh_token(REFRESH_TOKEN, session=session)
            
            # Get systems
            logger.info("🏠 Getting systems...")
            systems = await api.async_get_systems()
            
            if not systems:
                print("❌ No systems found")
                return
            
            system = list(systems.values())[0]
            logger.info(f"✅ Using system: {system.system_id}")
            
            # Find outdoor cameras
            outdoor_cameras = [c for c in system.cameras.values() 
                             if c.supports_webrtc_streaming and c.status == "online"]
            
            if not outdoor_cameras:
                print("❌ No online outdoor cameras found")
                print("Available cameras:")
                for camera in system.cameras.values():
                    print(f"   • {camera.name}: {camera.status} ({camera.streaming_provider})")
                return
            
            print(f"📹 Found {len(outdoor_cameras)} outdoor camera(s)")
            
            # Test each outdoor camera
            for camera in outdoor_cameras:
                print(f"\n🎥 Testing: {camera.name}")
                print("-" * 30)
                
                try:
                    # Get WebRTC connection info
                    logger.info(f"Getting WebRTC info for {camera.name}...")
                    connection_info = await camera.async_get_livekit_connection_info()
                    
                    print(f"✅ WebRTC connection info retrieved")
                    print(f"   • URL: {connection_info['url']}")
                    print(f"   • Status: {connection_info['camera_status']}")
                    print(f"   • Token: {len(connection_info['token'])} chars")
                    
                    # Generate HTML test file
                    camera_clean = camera.name.replace(' ', '_')
                    html_filename = f"webrtc_test_{camera_clean}.html"
                    
                    html_content = create_webrtc_test_html(camera.name, json.dumps(connection_info))
                    
                    with open(html_filename, 'w') as f:
                        f.write(html_content)
                    
                    print(f"   💾 Test page created: {html_filename}")
                    
                    # Save connection info as JSON
                    json_filename = f"webrtc_connection_{camera_clean}.json"
                    with open(json_filename, 'w') as f:
                        json.dump(connection_info, f, indent=2)
                    
                    print(f"   💾 Connection info saved: {json_filename}")
                    
                    # Try to open in browser
                    try:
                        file_path = os.path.abspath(html_filename)
                        file_url = f"file://{file_path}"
                        webbrowser.open(file_url)
                        print(f"   🌐 Opening in browser: {file_url}")
                    except Exception as e:
                        print(f"   ⚠️  Could not open browser: {e}")
                        print(f"   📋 Manual open: file://{os.path.abspath(html_filename)}")
                    
                except Exception as e:
                    print(f"   ❌ Failed to get WebRTC info: {e}")
                    continue
            
            print(f"\n🎯 WebRTC Test Summary:")
            print("=" * 40)
            print("📁 Files created:")
            print("   • webrtc_test_*.html - Browser test pages")
            print("   • webrtc_connection_*.json - Connection info")
            print()
            print("🔗 Next steps:")
            print("   1. Open the HTML file in your browser")
            print("   2. Click 'Connect to Camera'")
            print("   3. Wait 10-30 seconds for video to appear")
            print("   4. Check debug log if there are issues")
            print()
            print("💡 Tips:")
            print("   • Use Chrome/Edge for best compatibility")
            print("   • Camera needs to be online and charged")
            print("   • Connection may take time for camera wake-up")
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_webrtc_streaming())
