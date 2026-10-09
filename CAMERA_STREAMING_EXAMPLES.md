# SimpliSafe Camera Stream Recorder Scripts

This directory contains example scripts for recording SimpliSafe camera streams to files.

## Available Scripts

### 1. `save_camera_stream.py` - Full-featured interactive script

A comprehensive script with:
- Interactive camera selection
- Multiple authentication methods
- Configurable recording settings
- Progress monitoring
- Error handling

**Usage:**
```bash
# Set your authentication token
export SIMPLISAFE_REFRESH_TOKEN="your_token_here"

# Run the script
python3 save_camera_stream.py

# Or get help
python3 save_camera_stream.py --help
```

### 2. `simple_stream_recorder.py` - Minimal example

A basic script that demonstrates the core functionality:
```python
await camera.async_save_stream_to_file(
    file_path="recording.flv",
    format_type=StreamFormat.FLV,
    duration_seconds=30
)
```

## Using the Streaming API Directly

Here are examples of how to use the camera streaming functionality in your own code:

### Basic Stream Recording

```python
import asyncio
from aiohttp import ClientSession
from simplipy import API
from simplipy.device.camera import StreamFormat

async def record_camera():
    async with ClientSession() as session:
        # Authenticate
        api = await API.async_from_refresh_token("your_token", session=session)

        # Get camera
        systems = await api.async_get_systems()
        system = next(iter(systems.values()))
        camera = next(iter(system.cameras.values()))

        # Record for 30 seconds
        await camera.async_save_stream_to_file(
            file_path="recording.flv",
            format_type=StreamFormat.FLV,
            width=1280,
            audio_encoding="AAC",
            duration_seconds=30
        )

asyncio.run(record_camera())
```

### Manual Stream Processing

```python
import asyncio
from aiohttp import ClientSession
from simplipy import API
from simplipy.device.camera import StreamFormat

async def process_stream():
    async with ClientSession() as session:
        # Authenticate
        api = await API.async_from_refresh_token("your_token", session=session)

        # Get camera
        systems = await api.async_get_systems()
        system = next(iter(systems.values()))
        camera = next(iter(system.cameras.values()))

        # Process stream chunks manually
        with open("manual_recording.flv", "wb") as file:
            chunk_count = 0
            async for chunk in camera.async_stream_data(
                format_type=StreamFormat.FLV,
                width=1280,
                audio_encoding="AAC",
                chunk_size=8192
            ):
                file.write(chunk)
                chunk_count += 1

                # Stop after 1000 chunks (adjust as needed)
                if chunk_count >= 1000:
                    break

                # Print progress every 100 chunks
                if chunk_count % 100 == 0:
                    print(f"Processed {chunk_count} chunks")

asyncio.run(process_stream())
```

### Taking Snapshots

```python
import asyncio
from aiohttp import ClientSession
from simplipy import API

async def take_snapshot():
    async with ClientSession() as session:
        # Authenticate
        api = await API.async_from_refresh_token("your_token", session=session)

        # Get camera
        systems = await api.async_get_systems()
        system = next(iter(systems.values()))
        camera = next(iter(system.cameras.values()))

        # Take snapshot
        snapshot_data = await camera.async_get_snapshot(width=1280)

        # Save to file
        with open(f"snapshot_{camera.name}.jpg", "wb") as file:
            file.write(snapshot_data)

        print(f"Snapshot saved: {len(snapshot_data)} bytes")

asyncio.run(take_snapshot())
```

### Multiple Format Recording

```python
import asyncio
from aiohttp import ClientSession
from simplipy import API
from simplipy.device.camera import StreamFormat

async def record_multiple_formats():
    async with ClientSession() as session:
        # Authenticate
        api = await API.async_from_refresh_token("your_token", session=session)

        # Get camera
        systems = await api.async_get_systems()
        system = next(iter(systems.values()))
        camera = next(iter(system.cameras.values()))

        # Record FLV with audio
        print("Recording FLV with audio...")
        await camera.async_save_stream_to_file(
            file_path="recording_flv_aac.flv",
            format_type=StreamFormat.FLV,
            audio_encoding="AAC",
            duration_seconds=15
        )

        # Record MJPEG without audio
        print("Recording MJPEG...")
        await camera.async_save_stream_to_file(
            file_path="recording_mjpeg.mjpg",
            format_type=StreamFormat.MJPEG,
            width=640,
            duration_seconds=15
        )

        print("Both recordings completed!")

asyncio.run(record_multiple_formats())
```

## Stream Formats

### FLV (Flash Video)
- **Extension**: `.flv`
- **Audio support**: Yes (AAC, OPUS, Speex)
- **Best for**: Complete video recordings with audio
- **Playback**: VLC, ffplay, ffmpeg

### MJPEG (Motion JPEG)
- **Extension**: `.mjpg` or `.avi`
- **Audio support**: No
- **Best for**: Video-only recordings, snapshots
- **Playback**: Most video players, browsers

## Audio Encoding Options

- **`"AAC"`** - Advanced Audio Coding (default, best quality)
- **`"OPUS"`** - Open source codec, good compression
- **`""`** (empty string) - Uses Speex codec

## Configuration Options

```python
await camera.async_save_stream_to_file(
    file_path="custom_recording.flv",
    format_type=StreamFormat.FLV,      # FLV or MJPEG
    width=1280,                        # Video width (320-1920)
    audio_encoding="AAC",              # Audio codec
    duration_seconds=60,               # Recording duration
    chunk_size=8192,                   # Data chunk size
    custom_param="value"               # Additional URL parameters
)
```

## Error Handling

```python
import asyncio
from simplipy.errors import SimplipyError

async def safe_recording():
    try:
        await camera.async_save_stream_to_file(
            file_path="recording.flv",
            duration_seconds=30
        )
        print("Recording completed successfully!")

    except SimplipyError as e:
        print(f"SimpliSafe API error: {e}")

    except FileNotFoundError as e:
        print(f"File system error: {e}")

    except Exception as e:
        print(f"Unexpected error: {e}")
```

## Authentication Setup

Before using any scripts, you need to set up authentication:

### Method 1: Refresh Token (Recommended)
```bash
export SIMPLISAFE_REFRESH_TOKEN="your_refresh_token_here"
```

### Method 2: Authorization Code
```bash
export SIMPLISAFE_AUTHORIZATION_CODE="your_auth_code_here"
export SIMPLISAFE_CODE_VERIFIER="your_code_verifier_here"
```

## Installation Requirements

```bash
# Install the library with dependencies
pip install simplisafe-python

# Or if developing locally
pip install -e .
```

## Troubleshooting

1. **Camera offline**: Check camera status before recording
2. **Authentication errors**: Verify your tokens are valid
3. **No cameras found**: Ensure your system has cameras set up
4. **File permissions**: Check write permissions for output directory
5. **Network issues**: Verify internet connection and SimpliSafe service status
