# SimpliSafe Camera Streaming - User Guide

## 🎯 What You Can Do Today

### 📷 Indoor & Doorbell Cameras - **FULLY WORKING**

#### 1. **Take Snapshots** (Works immediately)
```python
import asyncio
from simplipy import API

async def take_snapshot():
    api = API()
    await api.async_from_credentials("email", "password")
    systems = await api.async_get_systems()
    system = systems[list(systems.keys())[0]]
    
    for camera in system.cameras.values():
        if camera.supports_standard_streaming:  # Indoor/Doorbell
            snapshot = await camera.async_get_snapshot(width=640)
            with open(f"snapshot_{camera.name}.jpg", "wb") as f:
                f.write(snapshot)
            print(f"✅ Saved snapshot for {camera.name}")

asyncio.run(take_snapshot())
```

#### 2. **Stream Live Video** (Works with VLC, FFmpeg, etc.)
```python
# Generate streaming commands
python vlc_streaming_guide.py

# Example output:
# vlc "https://media.simplisafe.com/v1/ss3/flv/YOUR_CAMERA_ID.flv?x=TOKEN"
# vlc "https://media.simplisafe.com/v1/ss3/mjpeg/YOUR_CAMERA_ID.mjpeg?x=TOKEN"
```

**Open in VLC Media Player:**
1. Copy the generated command
2. Paste into VLC (Media → Open Network Stream)
3. Video starts playing immediately

**Embed in Applications:**
```python
# Get streaming URL for your app
flv_url = await camera.async_get_flv_url()
mjpeg_url = await camera.async_get_mjpeg_url()
```

### 🌐 Outdoor Cameras - **PARTIAL SUPPORT**

#### 1. **Take Snapshots** (Works immediately)
```python
# Same as indoor cameras - snapshots work perfectly
snapshot = await outdoor_camera.async_get_snapshot()
```

#### 2. **Get WebRTC Connection Info** (Authentication tokens only)
```python
# This library provides valid LiveKit connection tokens
livekit_info = await outdoor_camera.async_get_livekit_connection_info()
print(f"Server: {livekit_info['server']}")
print(f"Token: {livekit_info['token']}")
```

#### 3. **⚠️ Actual Video Streaming** (Requires additional setup)
**What this library provides:**
- ✅ Valid LiveKit authentication tokens
- ✅ Correct server endpoints
- ✅ Camera wake-up logic

**What you need to add:**
- 🔧 LiveKit signaling server (go2rtc, official LiveKit, etc.)
- 🔧 WebRTC client implementation
- 🔧 Network infrastructure

## 🛠️ Setting Up WebRTC for Outdoor Cameras

### Option 1: go2rtc (Recommended for Home Assistant)
```yaml
# go2rtc.yaml
streams:
  driveway_camera:
    - "livekit://YOUR_TOKEN@livestream.services.simplisafe.com:7880/YOUR_CAMERA_NAME"

api:
  listen: ":1984"

webrtc:
  listen: ":8555"
```

### Option 2: Official LiveKit Server
1. Deploy LiveKit server: https://docs.livekit.io/home/self-hosting/deployment/
2. Configure with SimpliSafe endpoints
3. Use tokens from this library

### Option 3: Custom Implementation
```python
# Use the provided connection info with LiveKit SDK
from livekit import api

# Get connection info from this library
info = await camera.async_get_livekit_connection_info()

# Connect with official LiveKit client
room = api.connect_to_room(info['server'], info['token'])
```

## 📱 Practical Examples

### 1. **Security Monitoring App** (Indoor/Doorbell)
```python
# Take snapshot every 30 seconds
while True:
    for camera in indoor_cameras:
        snapshot = await camera.async_get_snapshot()
        # Process/analyze snapshot
        await asyncio.sleep(30)
```

### 2. **Live Dashboard** (Indoor/Doorbell)
```html
<!-- Embed MJPEG stream in web page -->
<img src="https://media.simplisafe.com/v1/ss3/mjpeg/CAMERA_ID.mjpeg?x=TOKEN" 
     alt="Live Camera Feed" />
```

### 3. **Home Assistant Integration** (All cameras)
```python
# Snapshots for all camera types
# Streaming for indoor/doorbell via MJPEG
# WebRTC setup needed for outdoor cameras
```

## 🔍 Testing Your Setup

### Quick Test - Indoor/Doorbell Cameras
```bash
# 1. Test snapshots
python test_direct_snapshot.py

# 2. Test streaming
python vlc_streaming_guide.py
# Copy VLC command and run it

# 3. Run comprehensive test
python final_streaming_test.py
```

### Quick Test - Outdoor Cameras  
```bash
# 1. Test snapshots (should work)
python final_streaming_test.py

# 2. Check WebRTC connection info
python test_webrtc_streaming.py

# 3. Set up signaling server for actual streaming
```

## 🚨 Important Limitations

### ✅ What Works Out of the Box
- Indoor camera snapshots and streaming
- Doorbell camera snapshots and streaming  
- Outdoor camera snapshots
- WebRTC authentication tokens

### ❌ What Requires Additional Setup
- Outdoor camera live video streaming
- WebRTC signaling infrastructure
- Browser-based WebRTC without signaling server

### 🔮 Future Improvements
- Monitor SimpliSafe for API changes
- Add more WebRTC client examples
- Improve error handling for edge cases

## 📞 Support & Troubleshooting

**For Indoor/Doorbell Issues:**
- Check network connectivity
- Verify SimpliSafe credentials
- Run `test_direct_snapshot.py` for diagnostics

**For Outdoor Camera Issues:**
- Verify camera is online in SimpliSafe app
- Check if camera supports WebRTC (newer models)
- See `WEBRTC_TROUBLESHOOTING.md` for detailed diagnosis

**For WebRTC Setup:**
- See `livekit_signaling_solution_guide.py`
- Check go2rtc documentation
- Review LiveKit official docs

---

**Bottom Line:** This library gives you everything needed for indoor/doorbell cameras and the authentication pieces for outdoor cameras. For outdoor video streaming, you'll need to set up the WebRTC infrastructure using the tokens this library provides.
