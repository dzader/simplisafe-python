# Cameras

{meth}`Camera <simplipy.camera.Camera>` objects correspond to SimpliSafe™ "SimpliCam"
cameras and doorbells (only available for V3 systems) and allow users to retrieve
information on them, including URLs to view live streams and capture snapshots.

## Camera Streaming Support 🎥

SimpliSafe cameras now support full streaming and snapshot functionality:

- **Live Video Streaming**: FLV and MJPEG format support
- **Snapshot Capture**: High-quality JPEG snapshots
- **Outdoor Camera Wake-up**: Automatic wake-up for battery-powered outdoor cameras
- **Multiple Camera Types**: Indoor, doorbell, and outdoor camera support

### Quick Streaming Example

```python
# Get a snapshot
snapshot_data = await camera.async_get_snapshot(width=640)
with open("snapshot.jpg", "wb") as f:
    f.write(snapshot_data)

# Get streaming URL
stream_url = camera.video_url()
print(f"Stream at: {stream_url}")

# Wake up outdoor camera if needed
if camera.is_outdoor_camera and camera.status == "offline":
    await camera.async_wake_up()
```

See [Camera Streaming Guide](camera_streaming.md) for complete documentation.

## Core Properties

All {meth}`Camera <simplipy.camera.Camera>` objects come with a standard set of properties:

```python
for serial, camera in system.cameras.items():
    # Return the cammera's UUID:
    serial
    # >>> 1234ABCD

    # ...or through the property:
    camera.serial
    # >>> 1234ABCD

    # Return all camera settings data:
    camera.camera_settings
    # >>> {"cameraName": "Camera", "pictureQuality": "720p", ...}

    # Return the type of camera this object represents:
    camera.camera_type
    # >>> doorbell

    # Return the camera name:
    camera.name
    # >>> My Doorbell

    # Return whether the privacy shutter is open when the
    # alarm is armed in away mode:
    camera.shutter_open_when_off
    # >>> False

    # Return whether the privacy shutter is open when the
    # alarm is armed in home mode:
    camera.shutter_open_when_home
    # >>> False

    # Return whether the privacy shutter is open when the
    # alarm is disarmed:
    camera.shutter_open_when_off
    # >>> False

    # Return the camera status:
    camera.status
    # >>> online

    # Return the camera subscription status:
    camera.subscription_enabled
    # >>> True
```

## Getting the Camera Video URL

```python
url = camera.video_url()
# >>> https://media.simplisafe.com/v1/...
```

## Camera Streaming

SimpliSafe cameras support live streaming and snapshot capture. The library provides methods to:

- Take snapshots from cameras
- Stream live video data (FLV or MJPEG formats)
- Record streams to files

### Taking Snapshots

```python
# Take a snapshot
snapshot_data = await camera.async_get_snapshot(width=1280)

# Save to file
with open("snapshot.jpg", "wb") as f:
    f.write(snapshot_data)
```

### Streaming Video

```python
from simplipy.device.camera import StreamFormat

# Stream FLV data with audio
async for chunk in camera.async_stream_data(
    format_type=StreamFormat.FLV,
    width=1280,
    audio_encoding="AAC"
):
    # Process each chunk of stream data
    print(f"Received {len(chunk)} bytes")
```

### Recording Streams

```python
# Record a 30-second stream to file
await camera.async_save_stream_to_file(
    file_path="recording.flv",
    format_type=StreamFormat.FLV,
    duration_seconds=30
)
```

For detailed documentation on camera streaming features, see [Camera Streaming](camera_streaming.md).
