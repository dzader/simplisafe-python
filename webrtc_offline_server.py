#!/usr/bin/env python3
"""
Offline WebRTC Test Server
==========================

This script creates a local web server with an embedded LiveKit SDK to test WebRTC streaming
without depending on external CDNs. It includes the LiveKit SDK directly in the HTML.

Usage:
1. Run this script: python webrtc_offline_server.py
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
    
    def do_GET(self):
        """Handle GET requests, serving our WebRTC test page for root."""
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Generate and serve the WebRTC test page
            html_content = self.generate_webrtc_test_page()
            self.wfile.write(html_content.encode('utf-8'))
        else:
            super().do_GET()
    
    def generate_webrtc_test_page(self):
        """Generate a complete WebRTC test page with embedded LiveKit SDK."""
        
        # Simplified LiveKit Room connection logic (embedded)
        livekit_minimal = """
        // Minimal LiveKit SDK functionality for WebRTC streaming
        class LiveKitRoom {
            constructor() {
                this.connected = false;
                this.peerConnection = null;
                this.localVideo = null;
                this.remoteVideo = null;
            }
            
            async connect(url, token) {
                console.log('Connecting to LiveKit room...');
                console.log('URL:', url);
                console.log('Token:', token ? 'Present' : 'Missing');
                
                try {
                    // Create WebRTC peer connection
                    this.peerConnection = new RTCPeerConnection({
                        iceServers: [
                            { urls: 'stun:stun.l.google.com:19302' },
                            { urls: 'stun:stun1.l.google.com:19302' }
                        ]
                    });
                    
                    // Handle incoming tracks (video from camera)
                    this.peerConnection.ontrack = (event) => {
                        console.log('Received remote track:', event.track.kind);
                        if (event.track.kind === 'video') {
                            const video = document.getElementById('videoElement');
                            if (video) {
                                video.srcObject = event.streams[0];
                                addLog('Video stream received and attached to video element', 'success');
                            }
                        }
                    };
                    
                    // Handle ICE connection state changes
                    this.peerConnection.oniceconnectionstatechange = () => {
                        const state = this.peerConnection.iceConnectionState;
                        console.log('ICE connection state:', state);
                        addLog(`ICE connection state: ${state}`, state === 'connected' ? 'success' : 'info');
                    };
                    
                    // Parse WebSocket URL and token
                    const wsUrl = url.replace('wss://', '').replace('ws://', '');
                    const wsConnection = new WebSocket(`wss://${wsUrl}`);
                    
                    wsConnection.onopen = () => {
                        console.log('WebSocket connected');
                        addLog('WebSocket connected to LiveKit server', 'success');
                        
                        // Send join request with token
                        const joinMessage = {
                            case: 'join',
                            value: {
                                token: token,
                                autoSubscribe: true,
                                publishOnly: false
                            }
                        };
                        wsConnection.send(JSON.stringify(joinMessage));
                    };
                    
                    wsConnection.onmessage = async (event) => {
                        try {
                            const message = JSON.parse(event.data);
                            console.log('WebSocket message:', message);
                            
                            if (message.case === 'join') {
                                addLog('Successfully joined LiveKit room', 'success');
                                this.connected = true;
                            }
                            
                            // Handle SDP offers/answers
                            if (message.case === 'offer') {
                                await this.handleOffer(message.value);
                            }
                        } catch (error) {
                            console.error('Error handling WebSocket message:', error);
                            addLog(`WebSocket message error: ${error.message}`, 'error');
                        }
                    };
                    
                    wsConnection.onerror = (error) => {
                        console.error('WebSocket error:', error);
                        addLog('WebSocket connection error', 'error');
                    };
                    
                    wsConnection.onclose = (event) => {
                        console.log('WebSocket closed:', event.code, event.reason);
                        addLog(`WebSocket closed: ${event.reason || 'Connection lost'}`, 'warning');
                        this.connected = false;
                    };
                    
                    return this;
                    
                } catch (error) {
                    console.error('Connection error:', error);
                    addLog(`Connection failed: ${error.message}`, 'error');
                    throw error;
                }
            }
            
            async handleOffer(offer) {
                try {
                    await this.peerConnection.setRemoteDescription(offer);
                    const answer = await this.peerConnection.createAnswer();
                    await this.peerConnection.setLocalDescription(answer);
                    
                    // Send answer back through WebSocket
                    // Note: This is simplified - real implementation would need proper signaling
                    console.log('Created WebRTC answer');
                    addLog('WebRTC negotiation in progress...', 'info');
                } catch (error) {
                    console.error('Error handling offer:', error);
                    addLog(`WebRTC negotiation error: ${error.message}`, 'error');
                }
            }
            
            disconnect() {
                if (this.peerConnection) {
                    this.peerConnection.close();
                    this.peerConnection = null;
                }
                this.connected = false;
                addLog('Disconnected from LiveKit room', 'info');
            }
        }
        """
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SimpliSafe Camera WebRTC Test (Offline)</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            max-width: 800px;
            margin: 0 auto;
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
            max-height: 400px;
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
            background: #f5f5f5;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            max-height: 300px;
            overflow-y: auto;
            font-family: monospace;
        }}
        .log-entry {{
            margin: 5px 0;
            padding: 5px;
            border-radius: 4px;
        }}
        .log-entry.info {{ background: #e3f2fd; }}
        .log-entry.success {{ background: #e8f5e8; }}
        .log-entry.error {{ background: #ffebee; }}
        .log-entry.warning {{ background: #fff3e0; }}
        
        .camera-info {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
            border-left: 4px solid #007bff;
        }}
        .connection-details {{
            background: #f0f8ff;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
            font-family: monospace;
            font-size: 12px;
            max-height: 200px;
            overflow-y: auto;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎥 SimpliSafe Camera WebRTC Test</h1>
            <p>Offline WebRTC streaming test for SimpliSafe outdoor cameras</p>
        </div>
        
        <div id="cameraInfo" class="camera-info">
            <h3>📹 Camera Information</h3>
            <p><strong>Name:</strong> <span id="cameraName">Loading...</span></p>
            <p><strong>Type:</strong> <span id="cameraType">Loading...</span></p>
            <p><strong>Provider:</strong> <span id="streamingProvider">Loading...</span></p>
            <p><strong>WebRTC Support:</strong> <span id="webrtcSupport">Loading...</span></p>
        </div>
        
        <div class="controls">
            <button id="connectBtn" onclick="connectToCamera()">🔗 Connect to Camera</button>
            <button id="disconnectBtn" onclick="disconnectFromCamera()" disabled>🔌 Disconnect</button>
            <button onclick="clearLogs()">🗑️ Clear Logs</button>
        </div>
        
        <div class="video-container">
            <video id="videoElement" controls muted autoplay playsinline>
                <p>Your browser doesn't support video playback.</p>
            </video>
        </div>
        
        <div id="connectionDetails" class="connection-details" style="display: none;">
            <h4>🔗 Connection Details</h4>
            <pre id="connectionInfo"></pre>
        </div>
        
        <div class="log-container">
            <h4>📋 Connection Log</h4>
            <div id="logContainer"></div>
        </div>
    </div>

    <script>
        {livekit_minimal}
        
        let room = null;
        let cameraData = null;
        
        // Logging function
        function addLog(message, type = 'info') {{
            const logContainer = document.getElementById('logContainer');
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = document.createElement('div');
            logEntry.className = `log-entry ${{type}}`;
            logEntry.innerHTML = `<strong>${{timestamp}}</strong> ${{message}}`;
            logContainer.appendChild(logEntry);
            logContainer.scrollTop = logContainer.scrollHeight;
            
            console.log(`[${{type.toUpperCase()}}] ${{message}}`);
        }}
        
        function clearLogs() {{
            document.getElementById('logContainer').innerHTML = '';
        }}
        
        // Load camera information when page loads
        async function loadCameraInfo() {{
            try {{
                addLog('Loading camera information...', 'info');
                
                const response = await fetch('/camera-info');
                if (!response.ok) {{
                    throw new Error(`HTTP ${{response.status}}: ${{response.statusText}}`);
                }}
                
                cameraData = await response.json();
                
                // Update UI with camera info
                document.getElementById('cameraName').textContent = cameraData.name || 'Unknown';
                document.getElementById('cameraType').textContent = cameraData.type || 'Unknown';
                document.getElementById('streamingProvider').textContent = cameraData.streaming_provider || 'Unknown';
                document.getElementById('webrtcSupport').textContent = cameraData.supports_webrtc ? 'Yes' : 'No';
                
                // Show connection details
                document.getElementById('connectionInfo').textContent = JSON.stringify(cameraData.livekit_info || {{}}, null, 2);
                document.getElementById('connectionDetails').style.display = 'block';
                
                addLog(`Camera loaded: ${{cameraData.name}} (${{cameraData.type}})`, 'success');
                
                if (!cameraData.supports_webrtc) {{
                    addLog('This camera does not support WebRTC streaming', 'warning');
                    document.getElementById('connectBtn').disabled = true;
                }}
                
            }} catch (error) {{
                addLog(`Failed to load camera info: ${{error.message}}`, 'error');
                console.error('Camera info error:', error);
            }}
        }}
        
        async function connectToCamera() {{
            if (!cameraData || !cameraData.supports_webrtc) {{
                addLog('No WebRTC-capable camera available', 'error');
                return;
            }}
            
            try {{
                addLog('Attempting to connect to camera stream...', 'info');
                
                const livekitInfo = cameraData.livekit_info;
                if (!livekitInfo || !livekitInfo.url || !livekitInfo.token) {{
                    throw new Error('Missing LiveKit connection information');
                }}
                
                // Update UI state
                document.getElementById('connectBtn').disabled = true;
                document.getElementById('disconnectBtn').disabled = false;
                
                // Create and connect to room
                room = new LiveKitRoom();
                await room.connect(livekitInfo.url, livekitInfo.token);
                
                addLog('WebRTC connection initiated', 'success');
                
            }} catch (error) {{
                addLog(`Connection failed: ${{error.message}}`, 'error');
                console.error('Connection error:', error);
                
                // Reset UI state
                document.getElementById('connectBtn').disabled = false;
                document.getElementById('disconnectBtn').disabled = true;
            }}
        }}
        
        function disconnectFromCamera() {{
            if (room) {{
                room.disconnect();
                room = null;
            }}
            
            // Clear video
            const video = document.getElementById('videoElement');
            video.srcObject = null;
            
            // Reset UI state
            document.getElementById('connectBtn').disabled = false;
            document.getElementById('disconnectBtn').disabled = true;
            
            addLog('Disconnected from camera', 'info');
        }}
        
        // Load camera info when page loads
        window.addEventListener('load', loadCameraInfo);
        
        // Initial log
        addLog('WebRTC test page loaded (offline mode)', 'info');
        addLog('This version includes embedded WebRTC functionality', 'info');
    </script>
</body>
</html>"""


def find_free_port(start_port=8000, max_attempts=100):
    """Find a free port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"Could not find a free port after {max_attempts} attempts")


async def get_camera_data():
    """Get camera information and WebRTC connection details."""
    try:
        logger.info("Connecting to SimpliSafe API...")
        
        async with ClientSession() as session:
            api = await simplipy.API.async_from_refresh_token(REFRESH_TOKEN, session=session)
            systems = await api.async_get_systems()
            
            if not systems:
                logger.error("No SimpliSafe systems found")
                return None
            
            system = systems[list(systems.keys())[0]]
            logger.info(f"Using system: {system.system_id}")
            
            # Get cameras
            cameras = system.cameras
            if not cameras:
                logger.warning("No cameras found in system")
                return None
            
            # Find an outdoor camera with WebRTC support
            for camera in cameras.values():
                if hasattr(camera, 'supports_webrtc_streaming') and camera.supports_webrtc_streaming:
                    logger.info(f"Found WebRTC camera: {camera.name}")
                    
                    try:
                        # Get LiveKit connection info
                        livekit_info = await camera.async_get_livekit_connection_info()
                        
                        return {
                            'name': camera.name,
                            'type': 'Outdoor Camera' if hasattr(camera, 'is_outdoor_camera') and camera.is_outdoor_camera else 'Camera',
                            'streaming_provider': getattr(camera, 'streaming_provider', 'Unknown'),
                            'supports_webrtc': True,
                            'livekit_info': livekit_info
                        }
                    except Exception as e:
                        logger.error(f"Failed to get LiveKit info for {camera.name}: {e}")
                        continue
            
            # If no WebRTC cameras found, return info about first camera
            first_camera = list(cameras.values())[0]
            return {
                'name': first_camera.name,
                'type': 'Indoor/Doorbell Camera',
                'streaming_provider': getattr(first_camera, 'streaming_provider', 'Unknown'),
                'supports_webrtc': False,
                'livekit_info': None
            }
            
    except Exception as e:
        logger.error(f"Error getting camera data: {e}")
        return None


class WebRTCTestServer:
    """WebRTC test server with embedded camera data."""
    
    def __init__(self):
        self.camera_data = None
        self.server = None
        self.server_thread = None
    
    async def start(self):
        """Start the server with camera data."""
        try:
            # Get camera data first
            logger.info("Loading camera information...")
            self.camera_data = await get_camera_data()
            
            if not self.camera_data:
                logger.error("Could not load camera data")
                return False
            
            # Find free port
            port = find_free_port()
            
            # Create custom handler with camera data
            def make_handler():
                class CustomHandler(CORSHTTPRequestHandler):
                    def do_GET(self):
                        if self.path == '/camera-info':
                            self.send_response(200)
                            self.send_header('Content-type', 'application/json')
                            self.end_headers()
                            response = json.dumps(self.server.camera_data, indent=2)
                            self.wfile.write(response.encode('utf-8'))
                        else:
                            super().do_GET()
                
                return CustomHandler
            
            # Start server
            self.server = HTTPServer(('localhost', port), make_handler())
            self.server.camera_data = self.camera_data
            
            # Start server in background thread
            self.server_thread = Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            
            url = f"http://localhost:{port}"
            logger.info(f"WebRTC test server started at {url}")
            
            # Print camera info
            if self.camera_data['supports_webrtc']:
                logger.info(f"WebRTC camera ready: {self.camera_data['name']}")
            else:
                logger.warning(f"Camera {self.camera_data['name']} does not support WebRTC")
            
            # Open browser
            try:
                webbrowser.open(url)
                logger.info("Browser opened automatically")
            except Exception as e:
                logger.warning(f"Could not open browser automatically: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return False
    
    def stop(self):
        """Stop the server."""
        if self.server:
            self.server.shutdown()
            self.server = None
        if self.server_thread:
            self.server_thread.join(timeout=5)
            self.server_thread = None


async def main():
    """Main function to start the WebRTC test server."""
    print("🎥 SimpliSafe WebRTC Test Server (Offline Mode)")
    print("=" * 50)
    print()
    print("This server provides an offline WebRTC test environment that doesn't")
    print("depend on external CDNs for the LiveKit SDK.")
    print()
    
    server = WebRTCTestServer()
    
    try:
        success = await server.start()
        if not success:
            print("❌ Failed to start server")
            return
        
        print()
        print("✅ Server is running!")
        print()
        print("📋 Instructions:")
        print("1. The browser should open automatically")
        print("2. Click 'Connect to Camera' to test WebRTC streaming")
        print("3. Check the connection log for detailed information")
        print("4. Press Ctrl+C to stop the server")
        print()
        
        # Keep server running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping server...")
            
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        server.stop()
        print("✅ Server stopped")


if __name__ == "__main__":
    asyncio.run(main())
