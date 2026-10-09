# Camera Streaming

The SimpliSafe Python library now supports streaming data from SimpliSafe cameras (SimpliCams). This includes taking snapshots, streaming live video, and recording streams to files.

## Features

- **Snapshot capture**: Get single frame images from cameras
- **Live streaming**: Stream FLV or MJPEG data from cameras
- **Stream recording**: Save streams directly to files
- **Multiple formats**: Support for FLV (with audio) and MJPEG streams
- **Flexible parameters**: Configurable video width, audio encoding, and custom parameters

## Basic Usage

### Taking Snapshots

```python
import asyncio
from aiohttp import ClientSession
from simplipy import API

async def take_snapshot():
    async with ClientSession() as session:
        # Authenticate with SimpliSafe
        simplisafe = await API.async_from_refresh_token(
            "your_refresh_token", session=session
        )

        # Get systems and cameras
        systems = await simplisafe.async_get_systems()
        system = next(iter(systems.values()))
        camera = next(iter(system.cameras.values()))

        # Take a snapshot
        snapshot_data = await camera.async_get_snapshot(width=1280)

        # Save the snapshot
        with open("snapshot.jpg", "wb") as f:
            f.write(snapshot_data)

asyncio.run(take_snapshot())
```

### Streaming Video

```python
import asyncio
from aiohttp import ClientSession
from simplipy import API
from simplipy.device.camera import StreamFormat

async def stream_video():
    async with ClientSession() as session:
        # Authenticate with SimpliSafe
        simplisafe = await API.async_from_refresh_token(
            "your_refresh_token", session=session
        )

        # Get systems and cameras
        systems = await simplisafe.async_get_systems()
        system = next(iter(systems.values()))
        camera = next(iter(system.cameras.values()))

        # Stream FLV data
        chunk_count = 0
        async for chunk in camera.async_stream_data(
            format_type=StreamFormat.FLV,
            width=1280,
            audio_encoding="AAC"
        ):
            chunk_count += 1
            print(f"Received chunk {chunk_count}: {len(chunk)} bytes")

            # Stop after 100 chunks for this example
            if chunk_count >= 100:
                break

asyncio.run(stream_video())
```

### Recording Streams to Files

```python
import asyncio
from aiohttp import ClientSession
from simplipy import API
from simplipy.device.camera import StreamFormat

async def record_stream():
    async with ClientSession() as session:
        # Authenticate with SimpliSafe
        simplisafe = await API.async_from_refresh_token(
            "your_refresh_token", session=session
        )

        # Get systems and cameras
        systems = await simplisafe.async_get_systems()
        system = next(iter(systems.values()))
        camera = next(iter(system.cameras.values()))

        # Record a 30-second FLV stream
        await camera.async_save_stream_to_file(
            file_path="recording.flv",
            format_type=StreamFormat.FLV,
            width=1280,
            audio_encoding="AAC",
            duration_seconds=30
        )

asyncio.run(record_stream())
```

## API Reference

### Camera Methods

#### `async_get_snapshot(width=1280, **kwargs) -> bytes`

Takes a snapshot from the camera and returns the image data as bytes.

**Parameters:**
- `width` (int): The width of the snapshot image (default: 1280)
- `**kwargs`: Additional URL parameters

**Returns:** `bytes` - The JPEG image data

#### `async_stream_data(format_type=StreamFormat.FLV, width=1280, audio_encoding="AAC", chunk_size=1024, **kwargs) -> AsyncGenerator[bytes, None]`

Streams live data from the camera.

**Parameters:**
- `format_type` (StreamFormat): The stream format (FLV or MJPEG)
- `width` (int): The video width (default: 1280)
- `audio_encoding` (str): Audio encoding for FLV streams (default: "AAC")
- `chunk_size` (int): Size of each data chunk (default: 1024)
- `**kwargs`: Additional URL parameters

**Yields:** `bytes` - Chunks of stream data

#### `async_save_stream_to_file(file_path, format_type=StreamFormat.FLV, width=1280, audio_encoding="AAC", duration_seconds=None, chunk_size=1024, **kwargs) -> None`

Saves a camera stream directly to a file.

**Parameters:**
- `file_path` (str): Path where to save the stream
- `format_type` (StreamFormat): The stream format (FLV or MJPEG)
- `width` (int): The video width (default: 1280)
- `audio_encoding` (str): Audio encoding for FLV streams (default: "AAC")
- `duration_seconds` (float | None): How long to record (None for indefinite)
- `chunk_size` (int): Size of each data chunk (default: 1024)
- `**kwargs`: Additional URL parameters

#### URL Generation Methods

#### `snapshot_url(width=1280, **kwargs) -> str`

Generates the URL for taking snapshots.

#### `stream_url(format_type=StreamFormat.FLV, width=1280, audio_encoding="AAC", **kwargs) -> str`

Generates the URL for streaming data.

#### `video_url(width=1280, audio_encoding="AAC", **kwargs) -> str`

Generates the URL for FLV video streams (legacy method).

## Stream Formats

### FLV (Flash Video)
- Supports both video and audio
- Audio encoding options: "AAC", "OPUS", or no audio encoding for Speex
- Best for recording complete video streams
- File extension: `.flv`

### MJPEG (Motion JPEG)
- Video only (no audio)
- Sequence of JPEG images
- Good for snapshots and simple video streaming
- More compatible with basic video players

## Audio Encoding Options

For FLV streams, you can specify different audio encodings:

- `"AAC"` - Advanced Audio Coding (default, best quality)
- `"OPUS"` - Open source audio codec
- `None` or empty string - Uses Speex audio codec

Example:
```python
# AAC audio
async for chunk in camera.async_stream_data(audio_encoding="AAC"):
    pass

# OPUS audio
async for chunk in camera.async_stream_data(audio_encoding="OPUS"):
    pass

# Speex audio (no audioEncoding parameter)
async for chunk in camera.async_stream_data(audio_encoding=""):
    pass
```

## Video Resolution Options

You can specify different video widths. The height is automatically calculated to maintain aspect ratio:

- `320` - Low resolution
- `640` - Medium resolution
- `720` - HD ready
- `1280` - HD (default)
- `1920` - Full HD (if supported by camera)

## Error Handling

The streaming methods can raise various exceptions:

```python
from simplipy.errors import SimplipyError, RequestError

try:
    snapshot = await camera.async_get_snapshot()
except RequestError as e:
    print(f"Network error: {e}")
except SimplipyError as e:
    print(f"SimpliSafe API error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Privacy Considerations

Be aware that:

1. Camera streams respect privacy shutter settings
2. Streaming requires an active SimpliSafe subscription
3. The camera must be online and accessible
4. Authentication tokens are required for all streaming operations

## Integration with Home Assistant

The streaming functionality can be integrated with Home Assistant camera platforms:

```python
# Example for Home Assistant custom component
async def async_camera_image(self, width: int | None = None, height: int | None = None) -> bytes | None:
    """Return a still image response from the camera."""
    try:
        return await self._camera.async_get_snapshot(width=width or 640)
    except Exception:
        return None

async def async_stream_source(self) -> str | None:
    """Return the stream source."""
    return self._camera.stream_url(
        format_type=StreamFormat.MJPEG,
        width=640
    )
```

## Performance Tips

1. **Choose appropriate resolution**: Lower resolutions use less bandwidth
2. **Use reasonable chunk sizes**: 1024-8192 bytes work well for most use cases
3. **Handle interruptions gracefully**: Use proper signal handling for long-running streams
4. **Monitor data usage**: Streaming can consume significant bandwidth
5. **Cache snapshots**: Don't take snapshots too frequently to avoid rate limiting

## Examples

See `examples/test_camera_streaming.py` for a complete example script that demonstrates:

- Taking snapshots
- Recording timed streams to files
- Continuous streaming with manual control
- MJPEG streaming
- Error handling and graceful shutdown
