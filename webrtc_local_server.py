#!/usr/bin/env python3
"""
Local WebRTC Test Server
========================

This script creates a local web server to properly serve the WebRTC test page,
which resolves JavaScript loading issues that occur when opening HTML files directly.

Usage:
1. Run this script: python webrtc_local_server.py
2. Open the provided URL in your browser
3. Test WebRTC streaming for your outdoor cameras
"""

import asyncio
import json
import logging
import os
import socket
import webbrowser
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse

import simplipy
from aiohttp import ClientSession
from simplipy.errors import SimplipyError

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

REFRESH_TOKEN = "FVo238-EavENCZsXqJ_NZq2Tq_n7z6c3CTfg_iHl9tH4v"


class CORSHTTPRequestHandler(SimpleHTTPRequestHandler):
    """HTTP request handler with CORS headers for local development."""
    
    def end_headers(self):
        """Add CORS headers to all responses."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Handle preflight OPTIONS requests."""
        self.send_response(200)
        self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default logging to reduce noise."""
        pass


def find_free_port():
    """Find a free port for the web server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


def start_web_server(port=None):
    """Start a local web server."""
    if port is None:
        port = find_free_port()
    
    server = HTTPServer(('localhost', port), CORSHTTPRequestHandler)
    
    def run_server():
        logger.info(f"Starting web server on http://localhost:{port}")
        server.serve_forever()
    
    thread = Thread(target=run_server, daemon=True)
    thread.start()
    
    return server, port


def create_improved_webrtc_test_page(camera_name, connection_info):
    """Create an improved WebRTC test page with better error handling and logging."""
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SimpliSafe WebRTC Test - {camera_name}</title>
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
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }}
        .status {{
            padding: 15px;
            margin: 15px 0;
            border-radius: 8px;
            font-weight: 500;
        }}
        .status.info {{ background: #e3f2fd; color: #1565c0; border-left: 4px solid #2196f3; }}
        .status.success {{ background: #e8f5e8; color: #2e7d32; border-left: 4px solid #4caf50; }}
        .status.error {{ background: #ffebee; color: #c62828; border-left: 4px solid #f44336; }}
        .status.warning {{ background: #fff3e0; color: #ef6c00; border-left: 4px solid #ff9800; }}
        
        .video-container {{
            text-align: center;
            margin: 30px 0;
        }}
        video {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            background: #000;
        }}
        .controls {{
            text-align: center;
            margin: 20px 0;
        }}
        button {{
            background: #2196f3;
            color: white;
            border: none;
            padding: 12px 24px;
            margin: 5px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            transition: background 0.3s;
        }}
        button:hover {{ background: #1976d2; }}
        button:disabled {{ background: #ccc; cursor: not-allowed; }}
        
        .log-container {{
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            max-height: 300px;
            overflow-y: auto;
        }}
        .log-entry {{
            margin: 5px 0;
            padding: 8px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
        }}
        .log-info {{ background: #e3f2fd; }}
        .log-success {{ background: #e8f5e8; }}
        .log-error {{ background: #ffebee; }}
        .log-warning {{ background: #fff3e0; }}
        
        .connection-info {{
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border: 1px solid #dee2e6;
        }}
        .connection-info pre {{
            margin: 0;
            font-size: 12px;
            overflow-x: auto;
        }}
        
        .instructions {{
            margin: 20px 0;
            padding: 20px;
            background: #e8f4fd;
            border-radius: 8px;
            border-left: 4px solid #2196f3;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎥 SimpliSafe WebRTC Streaming Test</h1>
            <h2>{camera_name}</h2>
            <p>Testing LiveKit WebRTC streaming for outdoor SimpliSafe cameras</p>
        </div>

        <div class="instructions">
            <h3>📋 Instructions</h3>
            <ol>
                <li><strong>Check SDK Status:</strong> Verify that the LiveKit SDK loads successfully</li>
                <li><strong>Connect to Stream:</strong> Click "Connect to Stream" to start WebRTC streaming</li>
                <li><strong>Monitor Logs:</strong> Watch the debug log below for detailed connection information</li>
                <li><strong>Troubleshoot:</strong> If connection fails, check your network and camera status</li>
            </ol>
        </div>

        <div class="status info" id="sdkStatus">
            🔄 Checking LiveKit SDK availability...
        </div>

        <div class="controls">
            <button id="connectBtn" onclick="connectToStream()" disabled>
                🔗 Connect to Stream
            </button>
            <button id="disconnectBtn" onclick="disconnectStream()" disabled>
                ❌ Disconnect
            </button>
            <button onclick="clearLogs()">
                🗑️ Clear Logs
            </button>
        </div>

        <div class="video-container">
            <video id="videoElement" controls muted autoplay playsinline>
                Your browser does not support the video element.
            </video>
        </div>

        <div class="connection-info">
            <h3>🔗 Connection Information</h3>
            <pre id="connectionInfo">{json.dumps(connection_info, indent=2)}</pre>
        </div>

        <div class="log-container">
            <h3>📝 Debug Log</h3>
            <div id="logOutput"></div>
        </div>
    </div>

    <!-- Load LiveKit SDK from multiple CDN sources for reliability -->
    <script crossorigin="anonymous" src="https://unpkg.com/livekit-client@2.5.6/dist/livekit-client.umd.min.js"
            onerror="tryAlternateCDN()"></script>
    
    <script>
        // Configuration
        const CONNECTION_INFO = {json.dumps(connection_info)};
        
        // Global variables
        let room = null;
        let connected = false;
        let sdkLoaded = false;
        let loadAttempts = 0;
        
        // Logging function
        function addLog(message, type = 'info') {{
            const logOutput = document.getElementById('logOutput');
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = document.createElement('div');
            logEntry.className = `log-entry log-${{type}}`;
            logEntry.textContent = `[${{timestamp}}] ${{message}}`;
            logOutput.appendChild(logEntry);
            logOutput.scrollTop = logOutput.scrollHeight;
            console.log(`WebRTC Test [${{type.toUpperCase()}}]: ${{message}}`);
        }}
        
        function clearLogs() {{
            document.getElementById('logOutput').innerHTML = '';
            addLog('Logs cleared', 'info');
        }}
        
        function updateStatus(message, type = 'info') {{
            const statusEl = document.getElementById('sdkStatus');
            statusEl.textContent = message;
            statusEl.className = `status ${{type}}`;
        }}
        
        function updateButtons() {{
            const connectBtn = document.getElementById('connectBtn');
            const disconnectBtn = document.getElementById('disconnectBtn');
            
            connectBtn.disabled = !sdkLoaded || connected;
            disconnectBtn.disabled = !connected;
        }}
        
        // Try alternate CDN if primary fails
        function tryAlternateCDN() {{
            loadAttempts++;
            addLog(`Primary CDN failed, trying alternate source... (attempt ${{loadAttempts}})`, 'warning');
            
            if (loadAttempts === 1) {{
                const script = document.createElement('script');
                script.src = 'https://cdn.jsdelivr.net/npm/livekit-client@2.5.6/dist/livekit-client.umd.min.js';
                script.crossOrigin = 'anonymous';
                script.onerror = () => {{
                    loadAttempts++;
                    addLog('Alternate CDN also failed, trying final source...', 'error');
                    tryFinalCDN();
                }};
                script.onload = checkSDK;
                document.head.appendChild(script);
            }} else {{
                tryFinalCDN();
            }}
        }}
        
        function tryFinalCDN() {{
            if (loadAttempts >= 3) {{
                updateStatus('❌ Failed to load LiveKit SDK from all sources', 'error');
                addLog('All CDN sources failed. Please check your internet connection.', 'error');
                addLog('You can try: 1) Refresh the page, 2) Check firewall settings, 3) Try a different browser', 'error');
                return;
            }}
            
            const script = document.createElement('script');
            script.src = 'https://cdn.skypack.dev/livekit-client@2.5.6';
            script.crossOrigin = 'anonymous';
            script.onerror = () => {{
                updateStatus('❌ Failed to load LiveKit SDK from all sources', 'error');
                addLog('All CDN sources failed. Please check your internet connection.', 'error');
            }};
            script.onload = checkSDK;
            document.head.appendChild(script);
        }}
        
        // Check if LiveKit SDK is available
        function checkSDK() {{
            addLog('Checking LiveKit SDK availability...', 'info');
            
            if (typeof LiveKit !== 'undefined') {{
                sdkLoaded = true;
                updateStatus('✅ LiveKit SDK loaded successfully', 'success');
                addLog('LiveKit SDK version: ' + (LiveKit.version || 'Unknown'), 'success');
                addLog('Available classes: ' + Object.keys(LiveKit).slice(0, 5).join(', ') + '...', 'info');
            }} else {{
                sdkLoaded = false;
                updateStatus('❌ LiveKit SDK not available', 'error');
                addLog('LiveKit SDK failed to load. This may be due to:', 'error');
                addLog('1. Network connectivity issues', 'error');
                addLog('2. Browser security restrictions', 'error');
                addLog('3. Firewall or proxy blocking CDN access', 'error');
            }}
            
            updateButtons();
        }}
        
        // Connect to WebRTC stream
        async function connectToStream() {{
            if (!sdkLoaded) {{
                addLog('Cannot connect: LiveKit SDK not loaded', 'error');
                return;
            }}
            
            try {{
                addLog('Initializing LiveKit room...', 'info');
                updateStatus('🔄 Connecting to stream...', 'info');
                
                // Create room instance
                room = new LiveKit.Room({{
                    adaptiveStream: true,
                    dynacast: true,
                    publishDefaults: {{
                        simulcast: false,
                    }},
                }});
                
                // Set up event listeners
                room.on('connected', () => {{
                    connected = true;
                    updateStatus('✅ Connected to LiveKit room', 'success');
                    addLog('Successfully connected to LiveKit room', 'success');
                    addLog(`Room: ${{room.name}}, SID: ${{room.sid}}`, 'info');
                    updateButtons();
                }});
                
                room.on('disconnected', (reason) => {{
                    connected = false;
                    updateStatus('❌ Disconnected from stream', 'warning');
                    addLog(`Disconnected: ${{reason}}`, 'warning');
                    updateButtons();
                }});
                
                room.on('trackSubscribed', (track, publication, participant) => {{
                    addLog(`Track subscribed: ${{track.kind}} from ${{participant.identity}}`, 'success');
                    
                    if (track.kind === 'video') {{
                        const videoElement = document.getElementById('videoElement');
                        track.attach(videoElement);
                        addLog('Video track attached to video element', 'success');
                    }}
                }});
                
                room.on('trackUnsubscribed', (track, publication, participant) => {{
                    addLog(`Track unsubscribed: ${{track.kind}} from ${{participant.identity}}`, 'info');
                    track.detach();
                }});
                
                room.on('participantConnected', (participant) => {{
                    addLog(`Participant connected: ${{participant.identity}}`, 'info');
                }});
                
                room.on('participantDisconnected', (participant) => {{
                    addLog(`Participant disconnected: ${{participant.identity}}`, 'info');
                }});
                
                // Connect to room
                addLog(`Connecting to: ${{CONNECTION_INFO.url}}`, 'info');
                addLog(`Room: ${{CONNECTION_INFO.room}}`, 'info');
                addLog(`Identity: ${{CONNECTION_INFO.identity}}`, 'info');
                
                await room.connect(CONNECTION_INFO.url, CONNECTION_INFO.token);
                
            }} catch (error) {{
                connected = false;
                updateStatus('❌ Connection failed: ' + error.message, 'error');
                addLog(`Connection error: ${{error.message}}`, 'error');
                addLog(`Error details: ${{error.stack}}`, 'error');
                updateButtons();
            }}
        }}
        
        // Disconnect from stream
        async function disconnectStream() {{
            if (room) {{
                addLog('Disconnecting from stream...', 'info');
                await room.disconnect();
                room = null;
                connected = false;
                updateStatus('⏹️ Disconnected', 'info');
                updateButtons();
                
                // Clear video element
                const videoElement = document.getElementById('videoElement');
                videoElement.srcObject = null;
            }}
        }}
        
        // Initialize when page loads
        window.addEventListener('load', () => {{
            addLog('Page loaded, initializing WebRTC test...', 'info');
            addLog('Camera: {camera_name}', 'info');
            addLog('Connection URL: ' + CONNECTION_INFO.url, 'info');
            
            // Check SDK after a brief delay to ensure script loading
            setTimeout(checkSDK, 500);
        }});
        
        // Handle page unload
        window.addEventListener('beforeunload', () => {{
            if (room) {{
                room.disconnect();
            }}
        }});
    </script>
</body>
</html>"""
    
    return html_content


async def generate_webrtc_test_for_outdoor_cameras():
    """Generate WebRTC test pages for all outdoor cameras."""
    async with ClientSession() as session:
        try:
            # Authenticate
            logger.info("🔑 Authenticating with SimpliSafe...")
            api = await simplipy.API.async_from_refresh_token(REFRESH_TOKEN, session=session)
            
            # Get systems
            systems = await api.async_get_systems()
            if not systems:
                logger.error("No systems found")
                return []
            
            system = list(systems.values())[0]
            
            # Find outdoor cameras
            outdoor_cameras = [
                camera for camera in system.cameras.values() 
                if camera.supports_webrtc_streaming and camera.status == "online"
            ]
            
            if not outdoor_cameras:
                logger.error("No online outdoor cameras found")
                return []
            
            generated_files = []
            
            for camera in outdoor_cameras:
                logger.info(f"Generating WebRTC test for {camera.name}...")
                
                try:
                    # Get WebRTC stream info
                    stream_info = await camera.async_get_webrtc_stream_info()
                    connection_info = camera.get_livekit_connection_info(stream_info)
                    
                    # Create HTML test page
                    html_content = create_improved_webrtc_test_page(camera.name, connection_info)
                    
                    # Save HTML file
                    safe_name = camera.name.replace(' ', '_').replace('/', '_')
                    html_filename = f"webrtc_test_{safe_name}.html"
                    
                    with open(html_filename, 'w') as f:
                        f.write(html_content)
                    
                    generated_files.append({
                        'camera': camera.name,
                        'html_file': html_filename,
                        'connection_info': connection_info
                    })
                    
                    logger.info(f"✅ Generated: {html_filename}")
                    
                except Exception as e:
                    logger.error(f"Failed to generate test for {camera.name}: {e}")
            
            return generated_files
            
        except Exception as e:
            logger.error(f"Error generating WebRTC tests: {e}")
            return []


async def main():
    """Main function to start the WebRTC test server."""
    print("🌐 SimpliSafe WebRTC Local Test Server")
    print("=" * 50)
    print("This tool creates a local web server to properly test WebRTC streaming")
    print("and resolves JavaScript loading issues with the LiveKit SDK.")
    print()
    
    # Generate WebRTC test pages
    print("📝 Generating WebRTC test pages...")
    generated_files = await generate_webrtc_test_for_outdoor_cameras()
    
    if not generated_files:
        print("❌ No outdoor cameras available for testing")
        return
    
    # Start web server
    print("🚀 Starting local web server...")
    server, port = start_web_server()
    base_url = f"http://localhost:{port}"
    
    print(f"✅ Server running at: {base_url}")
    print()
    print("📋 Available WebRTC Tests:")
    
    for file_info in generated_files:
        camera_name = file_info['camera']
        html_file = file_info['html_file']
        test_url = f"{base_url}/{html_file}"
        
        print(f"   • {camera_name}: {test_url}")
    
    print()
    print("🔧 Instructions:")
    print("1. Click on any URL above (or copy-paste into your browser)")
    print("2. Wait for the LiveKit SDK to load")
    print("3. Click 'Connect to Stream' to test WebRTC streaming")
    print("4. Monitor the debug log for connection details")
    print("5. Press Ctrl+C to stop the server when done")
    print()
    
    # Open first test in browser
    if generated_files:
        first_test = f"{base_url}/{generated_files[0]['html_file']}"
        print(f"🌐 Opening first test in browser: {first_test}")
        try:
            webbrowser.open(first_test)
        except:
            print("   (Could not auto-open browser - please copy the URL manually)")
    
    try:
        print("⏳ Server is running... Press Ctrl+C to stop")
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping server...")
        server.shutdown()
        print("✅ Server stopped")


if __name__ == "__main__":
    asyncio.run(main())
