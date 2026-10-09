"""Example script demonstrating SimpliSafe camera streaming functionality."""

import asyncio
import logging
import os
import signal
import sys
from pathlib import Path

from aiohttp import ClientSession

from simplipy import API
from simplipy.device.camera import StreamFormat
from simplipy.errors import SimplipyError

_LOGGER = logging.getLogger(__name__)

# Set these environment variables or replace with your values
SIMPLISAFE_AUTHORIZATION_CODE = os.getenv("SIMPLISAFE_AUTHORIZATION_CODE", "")
SIMPLISAFE_CODE_VERIFIER = os.getenv("SIMPLISAFE_CODE_VERIFIER", "")
SIMPLISAFE_REFRESH_TOKEN = os.getenv("SIMPLISAFE_REFRESH_TOKEN", "")

# Global variable to control streaming
streaming_active = True


def signal_handler(signum, frame):
    """Handle interrupt signals to gracefully stop streaming."""
    global streaming_active
    _LOGGER.info("Received signal %s, stopping stream...", signum)
    streaming_active = False


async def take_snapshot_example(camera) -> None:
    """Demonstrate taking a snapshot from a camera."""
    _LOGGER.info("Taking snapshot from camera: %s", camera.name)

    try:
        # Take a snapshot at different resolutions
        snapshot_data = await camera.async_get_snapshot(width=1280)

        # Save the snapshot
        snapshot_path = Path(f"snapshot_{camera.serial}_{camera.name.replace(' ', '_')}.jpg")
        with open(snapshot_path, "wb") as f:
            f.write(snapshot_data)

        _LOGGER.info("Snapshot saved to: %s (%d bytes)", snapshot_path, len(snapshot_data))

    except Exception as err:
        _LOGGER.error("Failed to take snapshot: %s", err)


async def stream_to_file_example(camera) -> None:
    """Demonstrate streaming camera data to a file."""
    _LOGGER.info("Starting stream from camera: %s", camera.name)

    try:
        # Stream FLV format to file for 30 seconds
        stream_path = f"stream_{camera.serial}_{camera.name.replace(' ', '_')}.flv"

        _LOGGER.info("Recording 30-second FLV stream to: %s", stream_path)
        await camera.async_save_stream_to_file(
            file_path=stream_path,
            format_type=StreamFormat.FLV,
            width=1280,
            audio_encoding="AAC",
            duration_seconds=30
        )

        _LOGGER.info("Stream recording completed: %s", stream_path)

    except Exception as err:
        _LOGGER.error("Failed to record stream: %s", err)


async def continuous_stream_example(camera) -> None:
    """Demonstrate continuous streaming with manual control."""
    _LOGGER.info("Starting continuous stream from camera: %s", camera.name)

    try:
        chunk_count = 0
        total_bytes = 0

        async for chunk in camera.async_stream_data(
            format_type=StreamFormat.FLV,
            width=720,  # Lower resolution for example
            audio_encoding="AAC",
            chunk_size=8192
        ):
            if not streaming_active:
                break

            chunk_count += 1
            total_bytes += len(chunk)

            # Log progress every 100 chunks
            if chunk_count % 100 == 0:
                _LOGGER.info("Received %d chunks, %d total bytes", chunk_count, total_bytes)

            # You could process the chunk here, save it, or forward it elsewhere
            # For this example, we'll just count the data

        _LOGGER.info("Stream ended. Total: %d chunks, %d bytes", chunk_count, total_bytes)

    except Exception as err:
        _LOGGER.error("Failed during continuous streaming: %s", err)


async def mjpeg_stream_example(camera) -> None:
    """Demonstrate MJPEG streaming for snapshots."""
    _LOGGER.info("Starting MJPEG stream from camera: %s", camera.name)

    try:
        frame_count = 0

        async for chunk in camera.async_stream_data(
            format_type=StreamFormat.MJPEG,
            width=640,
            chunk_size=4096
        ):
            if not streaming_active or frame_count >= 10:  # Limit to 10 frames for example
                break

            frame_count += 1
            _LOGGER.info("Received MJPEG frame %d (%d bytes)", frame_count, len(chunk))

        _LOGGER.info("MJPEG stream ended after %d frames", frame_count)

    except Exception as err:
        _LOGGER.error("Failed during MJPEG streaming: %s", err)


async def main() -> None:
    """Run the camera streaming examples."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Validate authentication info
    if not ((SIMPLISAFE_AUTHORIZATION_CODE and SIMPLISAFE_CODE_VERIFIER) or SIMPLISAFE_REFRESH_TOKEN):
        _LOGGER.error(
            "Missing authentication info. Please set either:\n"
            "  SIMPLISAFE_AUTHORIZATION_CODE and SIMPLISAFE_CODE_VERIFIER, or\n"
            "  SIMPLISAFE_REFRESH_TOKEN"
        )
        return 1

    async with ClientSession() as session:
        try:
            # Authenticate with SimpliSafe
            if SIMPLISAFE_REFRESH_TOKEN:
                _LOGGER.info("Authenticating with refresh token...")
                simplisafe = await API.async_from_refresh_token(
                    SIMPLISAFE_REFRESH_TOKEN, session=session
                )
            else:
                _LOGGER.info("Authenticating with authorization code...")
                simplisafe = await API.async_from_auth(
                    SIMPLISAFE_AUTHORIZATION_CODE,
                    SIMPLISAFE_CODE_VERIFIER,
                    session=session,
                )

            # Get systems and find cameras
            systems = await simplisafe.async_get_systems()
            if not systems:
                _LOGGER.error("No systems found")
                return 1

            # Find the first system with cameras
            system_with_cameras = None
            for system in systems.values():
                if system.cameras:
                    system_with_cameras = system
                    break

            if not system_with_cameras:
                _LOGGER.error("No cameras found in any system")
                return 1

            _LOGGER.info("Found system '%s' with %d cameras",
                        system_with_cameras.address, len(system_with_cameras.cameras))

            # List all cameras
            for camera in system_with_cameras.cameras.values():
                _LOGGER.info("Camera: %s (Serial: %s, Status: %s, Type: %s)",
                           camera.name, camera.serial, camera.status, camera.camera_type.name)

            # Use the first available camera
            camera = next(iter(system_with_cameras.cameras.values()))
            _LOGGER.info("Using camera: %s", camera.name)

            # Check if camera is online
            if camera.status != "online":
                _LOGGER.warning("Camera %s is not online (status: %s)", camera.name, camera.status)

            print("\nAvailable examples:")
            print("1. Take snapshot")
            print("2. Record 30-second stream to file")
            print("3. Continuous streaming (Ctrl+C to stop)")
            print("4. MJPEG stream example (10 frames)")
            print("5. Run all examples")

            choice = input("\nSelect an example (1-5): ").strip()

            if choice == "1":
                await take_snapshot_example(camera)
            elif choice == "2":
                await stream_to_file_example(camera)
            elif choice == "3":
                await continuous_stream_example(camera)
            elif choice == "4":
                await mjpeg_stream_example(camera)
            elif choice == "5":
                _LOGGER.info("Running all examples...")
                await take_snapshot_example(camera)
                await asyncio.sleep(2)
                await stream_to_file_example(camera)
                await asyncio.sleep(2)
                await mjpeg_stream_example(camera)
                _LOGGER.info("All examples completed!")
            else:
                _LOGGER.error("Invalid choice")
                return 1

        except SimplipyError as err:
            _LOGGER.error("SimpliSafe API error: %s", err)
            return 1
        except Exception as err:
            _LOGGER.error("Unexpected error: %s", err)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
