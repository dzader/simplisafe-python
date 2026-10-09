"""Define tests for the Camera objects."""

from __future__ import annotations

from typing import cast
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest
from aresponses import ResponsesMockServer

from simplipy import API
from simplipy.device.camera import CameraTypes, StreamFormat
from simplipy.system.v3 import SystemV3

from .common import (
    TEST_AUTHORIZATION_CODE,
    TEST_CAMERA_ID,
    TEST_CAMERA_ID_2,
    TEST_CODE_VERIFIER,
    TEST_SYSTEM_ID,
)


@pytest.mark.asyncio
async def test_properties(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
) -> None:
    """Test that camera properties are created properly.

    Args:
        aresponses: An aresponses server.
        authenticated_simplisafe_server_v3: A authenticated API connection.
    """
    async with authenticated_simplisafe_server_v3, aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )

        systems = await simplisafe.async_get_systems()
        system: SystemV3 = cast(SystemV3, systems[TEST_SYSTEM_ID])
        camera = system.cameras[TEST_CAMERA_ID]
        assert camera.name == "Camera"
        assert camera.serial == TEST_CAMERA_ID
        assert camera.camera_settings["cameraName"] == "Camera"
        assert camera.status == "online"
        assert camera.subscription_enabled
        assert not camera.shutter_open_when_off
        assert not camera.shutter_open_when_home
        assert camera.shutter_open_when_away
        assert camera.camera_type == CameraTypes.CAMERA

        error_camera = system.cameras[TEST_CAMERA_ID_2]
        assert error_camera.camera_type == CameraTypes.UNKNOWN

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_video_urls(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
) -> None:
    """Test that camera video URL is configured properly.

    Args:
        aresponses: An aresponses server.
        authenticated_simplisafe_server_v3: A authenticated API connection.
    """
    async with authenticated_simplisafe_server_v3, aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )

        systems = await simplisafe.async_get_systems()
        system: SystemV3 = cast(SystemV3, systems[TEST_SYSTEM_ID])
        camera = system.cameras[TEST_CAMERA_ID]
        assert camera.video_url() == (
            f"https://media.simplisafe.com/v1/{TEST_CAMERA_ID}/flv?x=1280&"
            "audioEncoding=AAC"
        )
        assert camera.video_url(width=720) == (
            f"https://media.simplisafe.com/v1/{TEST_CAMERA_ID}/flv?x=720"
            "&audioEncoding=AAC"
        )
        assert camera.video_url(width=720, audio_encoding="OPUS") == (
            f"https://media.simplisafe.com/v1/{TEST_CAMERA_ID}/flv?x=720&"
            "audioEncoding=OPUS"
        )
        assert camera.video_url(audio_encoding="OPUS") == (
            f"https://media.simplisafe.com/v1/{TEST_CAMERA_ID}/flv?x=1280&"
            "audioEncoding=OPUS"
        )
        assert camera.video_url(additional_param="1") == (
            f"https://media.simplisafe.com/v1/{TEST_CAMERA_ID}/flv?x=1280&"
            "audioEncoding=AAC&additional_param=1"
        )

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_snapshot_url(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
) -> None:
    """Test that camera snapshot URL is configured properly.

    Args:
        aresponses: An aresponses server.
        authenticated_simplisafe_server_v3: A authenticated API connection.
    """
    async with authenticated_simplisafe_server_v3, aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )

        systems = await simplisafe.async_get_systems()
        system: SystemV3 = cast(SystemV3, systems[TEST_SYSTEM_ID])
        camera = system.cameras[TEST_CAMERA_ID]

        assert camera.snapshot_url() == (
            f"https://media.simplisafe.com/v1/{TEST_CAMERA_ID}/mjpg?x=1280&fr=1"
        )
        assert camera.snapshot_url(width=640) == (
            f"https://media.simplisafe.com/v1/{TEST_CAMERA_ID}/mjpg?x=640&fr=1"
        )
        assert camera.snapshot_url(additional_param="test") == (
            f"https://media.simplisafe.com/v1/{TEST_CAMERA_ID}/mjpg?x=1280&fr=1&additional_param=test"
        )

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_stream_url(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
) -> None:
    """Test that camera stream URLs are configured properly.

    Args:
        aresponses: An aresponses server.
        authenticated_simplisafe_server_v3: A authenticated API connection.
    """
    async with authenticated_simplisafe_server_v3, aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )

        systems = await simplisafe.async_get_systems()
        system: SystemV3 = cast(SystemV3, systems[TEST_SYSTEM_ID])
        camera = system.cameras[TEST_CAMERA_ID]

        # Test FLV stream URL
        assert camera.stream_url(StreamFormat.FLV) == (
            f"https://media.simplisafe.com/v1/{TEST_CAMERA_ID}/flv?x=1280&audioEncoding=AAC"
        )
        assert camera.stream_url(StreamFormat.FLV, width=720, audio_encoding="OPUS") == (
            f"https://media.simplisafe.com/v1/{TEST_CAMERA_ID}/flv?x=720&audioEncoding=OPUS"
        )

        # Test MJPEG stream URL
        assert camera.stream_url(StreamFormat.MJPEG) == (
            f"https://media.simplisafe.com/v1/{TEST_CAMERA_ID}/mjpg?x=1280"
        )
        assert camera.stream_url(StreamFormat.MJPEG, width=640) == (
            f"https://media.simplisafe.com/v1/{TEST_CAMERA_ID}/mjpg?x=640"
        )

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_snapshot(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
) -> None:
    """Test taking a camera snapshot.

    Args:
        aresponses: An aresponses server.
        authenticated_simplisafe_server_v3: A authenticated API connection.
    """
    async with authenticated_simplisafe_server_v3, aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )

        systems = await simplisafe.async_get_systems()
        system: SystemV3 = cast(SystemV3, systems[TEST_SYSTEM_ID])
        camera = system.cameras[TEST_CAMERA_ID]

        # Mock the media request
        mock_snapshot_data = b"fake_jpeg_data"
        with patch.object(
            system.api, "_async_media_data", new_callable=AsyncMock
        ) as mock_media:
            mock_media.return_value = {"bytes": mock_snapshot_data}

            snapshot = await camera.async_get_snapshot(width=640)
            assert snapshot == mock_snapshot_data

            # Verify the correct URL was called
            expected_url = f"https://media.simplisafe.com/v1/{TEST_CAMERA_ID}/mjpg?x=640&fr=1"
            mock_media.assert_called_once_with(expected_url)

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_stream_data(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
) -> None:
    """Test streaming camera data.

    Args:
        aresponses: An aresponses server.
        authenticated_simplisafe_server_v3: A authenticated API connection.
    """
    async with authenticated_simplisafe_server_v3, aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )

        systems = await simplisafe.async_get_systems()
        system: SystemV3 = cast(SystemV3, systems[TEST_SYSTEM_ID])
        camera = system.cameras[TEST_CAMERA_ID]

        # Mock the streaming response
        mock_chunks = [b"chunk1", b"chunk2", b"chunk3"]

        class MockResponse:
            def __init__(self):
                self.content = MockContent()

            def raise_for_status(self):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        class MockContent:
            def __init__(self):
                self.chunks = iter(mock_chunks)

            async def iter_chunked(self, chunk_size):
                for chunk in self.chunks:
                    yield chunk

        with patch.object(session, "get", return_value=MockResponse()) as mock_get:
            chunks = []
            async for chunk in camera.async_stream_data(
                format_type=StreamFormat.FLV,
                width=720,
                chunk_size=1024
            ):
                chunks.append(chunk)

            assert chunks == mock_chunks

            # Verify the correct URL and headers were used
            expected_url = f"https://media.simplisafe.com/v1/{TEST_CAMERA_ID}/flv?x=720&audioEncoding=AAC"
            mock_get.assert_called_once_with(
                expected_url,
                headers={"Authorization": f"Bearer {system.api.access_token}"}
            )

    aresponses.assert_plan_strictly_followed()
