#!/usr/bin/env python3
"""
Minimal script to save SimpliSafe camera stream to a file.

This is a simple, straightforward example of using the camera streaming functionality.
"""

import asyncio
import os
from aiohttp import ClientSession
from simplipy import API
from simplipy.device.camera import StreamFormat

# Configuration
REFRESH_TOKEN = "your_refresh_token_here"  # Replace with your actual token
DURATION_SECONDS = 30  # How long to record
OUTPUT_FILE = "camera_stream.flv"


async def save_stream():
    """Save camera stream to file."""

    async with ClientSession() as session:
        # Authenticate
        api = await API.async_from_refresh_token(REFRESH_TOKEN, session=session)

        # Get first system and first camera
        systems = await api.async_get_systems()
        system = next(iter(systems.values()))
        camera = next(iter(system.cameras.values()))

        print(f"Recording from camera: {camera.name}")
        print(f"Duration: {DURATION_SECONDS} seconds")
        print(f"Output file: {OUTPUT_FILE}")

        # Save stream to file
        await camera.async_save_stream_to_file(
            file_path=OUTPUT_FILE,
            format_type=StreamFormat.FLV,
            width=1280,
            audio_encoding="AAC",
            duration_seconds=DURATION_SECONDS
        )

        print("Recording completed!")


if __name__ == "__main__":
    # Check if token is set
    if REFRESH_TOKEN == "your_refresh_token_here":
        print("Please set your REFRESH_TOKEN in the script")
        exit(1)

    asyncio.run(save_stream())
