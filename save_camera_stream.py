#!/usr/bin/env python3
"""
Simple script to save SimpliSafe camera stream to a file.

This script connects to a SimpliSafe camera and saves the stream to a file.
You can specify the duration, format, and other parameters.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

from aiohttp import ClientSession

from simplipy import API
from simplipy.device.camera import StreamFormat
from simplipy.errors import SimplipyError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration - set these as environment variables or modify directly
SIMPLISAFE_REFRESH_TOKEN = os.getenv("SIMPLISAFE_REFRESH_TOKEN", "")
SIMPLISAFE_AUTHORIZATION_CODE = os.getenv("SIMPLISAFE_AUTHORIZATION_CODE", "")
SIMPLISAFE_CODE_VERIFIER = os.getenv("SIMPLISAFE_CODE_VERIFIER", "")

# Recording settings
RECORDING_DURATION = 30  # seconds
VIDEO_WIDTH = 1280
STREAM_FORMAT = StreamFormat.FLV  # or StreamFormat.MJPEG
AUDIO_ENCODING = "AAC"  # AAC, OPUS, or "" for Speex


async def save_camera_stream():
    """Save camera stream to a file."""

    # Validate authentication
    if not SIMPLISAFE_REFRESH_TOKEN and not (SIMPLISAFE_AUTHORIZATION_CODE and SIMPLISAFE_CODE_VERIFIER):
        logger.error(
            "No authentication provided. Please set one of:\n"
            "  - SIMPLISAFE_REFRESH_TOKEN environment variable\n"
            "  - Both SIMPLISAFE_AUTHORIZATION_CODE and SIMPLISAFE_CODE_VERIFIER"
        )
        return False

    async with ClientSession() as session:
        try:
            # Authenticate with SimpliSafe
            logger.info("Authenticating with SimpliSafe...")
            if SIMPLISAFE_REFRESH_TOKEN:
                simplisafe = await API.async_from_refresh_token(
                    SIMPLISAFE_REFRESH_TOKEN, session=session
                )
                logger.info("Authenticated using refresh token")
            else:
                simplisafe = await API.async_from_auth(
                    SIMPLISAFE_AUTHORIZATION_CODE,
                    SIMPLISAFE_CODE_VERIFIER,
                    session=session,
                )
                logger.info("Authenticated using authorization code")

            # Get systems and find cameras
            logger.info("Fetching systems...")
            systems = await simplisafe.async_get_systems()

            if not systems:
                logger.error("No systems found")
                return False

            # Find first system with cameras
            system_with_cameras = None
            for system in systems.values():
                if system.cameras:
                    system_with_cameras = system
                    break

            if not system_with_cameras:
                logger.error("No cameras found in any system")
                return False

            logger.info(f"Found system '{system_with_cameras.address}' with {len(system_with_cameras.cameras)} cameras")

            # List available cameras
            print("\nAvailable cameras:")
            for i, camera in enumerate(system_with_cameras.cameras.values(), 1):
                print(f"  {i}. {camera.name} (Serial: {camera.serial}, Status: {camera.status})")

            # Select camera
            if len(system_with_cameras.cameras) == 1:
                camera = next(iter(system_with_cameras.cameras.values()))
                logger.info(f"Using only available camera: {camera.name}")
            else:
                while True:
                    try:
                        choice = int(input(f"\nSelect camera (1-{len(system_with_cameras.cameras)}): "))
                        if 1 <= choice <= len(system_with_cameras.cameras):
                            camera = list(system_with_cameras.cameras.values())[choice - 1]
                            break
                        else:
                            print("Invalid choice, please try again.")
                    except (ValueError, KeyboardInterrupt):
                        print("\nOperation cancelled.")
                        return False

            # Check camera status
            if camera.status != "online":
                logger.warning(f"Camera '{camera.name}' is not online (status: {camera.status})")
                response = input("Continue anyway? (y/N): ").strip().lower()
                if response != 'y':
                    logger.info("Operation cancelled.")
                    return False

            # Generate filename
            safe_name = camera.name.replace(' ', '_').replace('/', '_')
            file_extension = "flv" if STREAM_FORMAT == StreamFormat.FLV else "mjpg"
            filename = f"camera_{camera.serial}_{safe_name}_{RECORDING_DURATION}s.{file_extension}"
            file_path = Path(filename)

            # Confirm recording settings
            print(f"\nRecording settings:")
            print(f"  Camera: {camera.name}")
            print(f"  Format: {STREAM_FORMAT.value.upper()}")
            print(f"  Resolution: {VIDEO_WIDTH}px wide")
            if STREAM_FORMAT == StreamFormat.FLV:
                print(f"  Audio: {AUDIO_ENCODING or 'Speex'}")
            print(f"  Duration: {RECORDING_DURATION} seconds")
            print(f"  Output file: {file_path}")

            response = input("\nStart recording? (Y/n): ").strip().lower()
            if response == 'n':
                logger.info("Recording cancelled.")
                return False

            # Start recording
            logger.info(f"Starting {RECORDING_DURATION}-second recording...")
            logger.info(f"Saving to: {file_path}")

            try:
                await camera.async_save_stream_to_file(
                    file_path=str(file_path),
                    format_type=STREAM_FORMAT,
                    width=VIDEO_WIDTH,
                    audio_encoding=AUDIO_ENCODING,
                    duration_seconds=RECORDING_DURATION,
                    chunk_size=8192  # 8KB chunks for better performance
                )

                # Check if file was created successfully
                if file_path.exists():
                    file_size = file_path.stat().st_size
                    logger.info(f"Recording completed successfully!")
                    logger.info(f"File saved: {file_path} ({file_size:,} bytes)")

                    # Suggest playback command
                    if STREAM_FORMAT == StreamFormat.FLV:
                        print(f"\nTo play the recording, try:")
                        print(f"  vlc {file_path}")
                        print(f"  ffplay {file_path}")
                    else:
                        print(f"\nTo view the MJPEG file, try:")
                        print(f"  vlc {file_path}")
                        print(f"  ffplay {file_path}")

                    return True
                else:
                    logger.error("Recording failed - no output file created")
                    return False

            except KeyboardInterrupt:
                logger.info("Recording interrupted by user")
                if file_path.exists():
                    file_size = file_path.stat().st_size
                    logger.info(f"Partial recording saved: {file_path} ({file_size:,} bytes)")
                return False

        except SimplipyError as err:
            logger.error(f"SimpliSafe API error: {err}")
            return False
        except Exception as err:
            logger.error(f"Unexpected error: {err}")
            return False


async def main():
    """Main entry point."""
    print("SimpliSafe Camera Stream Recorder")
    print("=" * 40)

    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("""
Usage: python3 save_camera_stream.py

Environment variables:
  SIMPLISAFE_REFRESH_TOKEN        - Your SimpliSafe refresh token
  SIMPLISAFE_AUTHORIZATION_CODE   - Authorization code (alternative to refresh token)
  SIMPLISAFE_CODE_VERIFIER        - Code verifier (required with auth code)

Configuration (edit script to change):
  RECORDING_DURATION = 30         - Recording duration in seconds
  VIDEO_WIDTH = 1280              - Video width in pixels
  STREAM_FORMAT = StreamFormat.FLV - Stream format (FLV or MJPEG)
  AUDIO_ENCODING = "AAC"          - Audio encoding (AAC, OPUS, or "" for Speex)

Examples:
  # Using refresh token
  export SIMPLISAFE_REFRESH_TOKEN="your_token_here"
  python3 save_camera_stream.py

  # Using authorization code
  export SIMPLISAFE_AUTHORIZATION_CODE="your_code_here"
  export SIMPLISAFE_CODE_VERIFIER="your_verifier_here"
  python3 save_camera_stream.py
""")
        return

    try:
        success = await save_camera_stream()
        if success:
            print("\n✅ Stream recording completed successfully!")
        else:
            print("\n❌ Stream recording failed.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Recording interrupted by user.")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
