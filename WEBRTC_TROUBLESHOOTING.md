# WebRTC Testing Troubleshooting Guide

## Current Status ✅

Your SimpliSafe WebRTC streaming is now working with the offline test server!

### What's Working:
- **Camera**: Driveway (Outdoor Camera)
- **Server**: http://localhost:8000 (running)
- **WebRTC Support**: Yes (LiveKit provider)
- **Connection**: Camera is awake and ready
- **LiveKit URL**: wss://livestream.services.simplisafe.com:7880

## How to Test WebRTC Streaming

### 1. Browser Test (Recommended)
The offline server at http://localhost:8000 provides the best testing experience:

```bash
# Server is already running, just open your browser to:
http://localhost:8000
```

**Instructions:**
1. Click "Connect to Camera" button
2. Watch the connection log for status updates
3. Video should appear in the video element once connected
4. Check browser console (F12) for detailed WebRTC logs

### 2. Alternative Testing Methods

#### Python Test Script
```bash
python test_webrtc_streaming.py
```

#### VLC Streaming (for comparison)
```bash
python vlc_streaming_guide.py
```

## Common Issues & Solutions

### Issue: "LiveKit SDK not loaded"
**Solution**: Use the offline server (webrtc_offline_server.py) instead of the original server
- ✅ **Fixed**: Now using embedded WebRTC code instead of external CDNs

### Issue: Camera not waking up
**Solution**: The wake-up logic is already implemented and working
- Camera "Driveway" was successfully woken up
- Takes ~3-5 seconds to wake up outdoor cameras

### Issue: WebRTC connection fails
**Troubleshooting steps:**
1. Check browser console for WebRTC errors
2. Verify camera is still online: run `python test_direct_snapshot.py`
3. Check network firewall/proxy settings
4. Try different browser (Chrome/Edge work best for WebRTC)

### Issue: No video appears
**Possible causes:**
1. WebRTC negotiation failed (check browser console)
2. Camera went to sleep (wake it up again)
3. Network connectivity issues
4. Browser permissions (allow camera/microphone access)

## Technical Details

### Camera Capabilities:
- **Type**: Outdoor Camera
- **Streaming Provider**: livekit
- **Recording Provider**: ss3
- **Standard Streaming**: No (outdoor cameras don't support HTTP streaming)
- **WebRTC Streaming**: Yes (LiveKit-based)

### Connection Information:
- **LiveKit Server**: wss://livestream.services.simplisafe.com:7880
- **Authentication**: JWT token (automatically retrieved)
- **Protocol**: WebRTC over WebSocket
- **ICE Servers**: Google STUN servers for NAT traversal

## Testing Different Cameras

To test other cameras, modify the `REFRESH_TOKEN` in the server script or use:

```python
# List all cameras and their capabilities
python demo_camera_streaming.py
```

## Logs and Debugging

### Server Logs
The server provides detailed logs showing:
- API connection status
- Camera wake-up process
- LiveKit connection retrieval
- WebRTC negotiation attempts

### Browser Console
Open browser developer tools (F12) to see:
- WebSocket connection status
- WebRTC peer connection details
- ICE candidate exchange
- Video track information

## Next Steps

1. **Test the current setup**: Visit http://localhost:8000 and try connecting
2. **Compare with other cameras**: Run `python demo_camera_streaming.py` to see all camera types
3. **Test snapshots**: Run `python test_direct_snapshot.py` for quick camera verification
4. **VLC streaming**: Run `python vlc_streaming_guide.py` for indoor/doorbell camera streaming

## Support

If you encounter issues:
1. Check the connection log in the browser interface
2. Look at server terminal output for API errors  
3. Verify camera status with: `python test_direct_snapshot.py`
4. Try different browsers (Chrome, Edge, Firefox)

The offline WebRTC server provides the most reliable testing experience since it doesn't depend on external CDNs or network connectivity for JavaScript libraries.
