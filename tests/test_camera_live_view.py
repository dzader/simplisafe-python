"""Test provider discovery, fresh credentials and live-view response contracts.

The example.test fixtures are synthetic contracts derived from public clients,
not captures of a working session or evidence of physical-camera playback.
"""

from __future__ import annotations

import json
import logging
from copy import deepcopy
from datetime import timedelta
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest
from aresponses import ResponsesMockServer

from simplipy import API
from simplipy.device import DeviceTypes
from simplipy.device.camera import WEBRTC_URL_BASE, Camera
from simplipy.device.live_view import (
    CameraStreamProvider,
    KinesisLiveView,
    LegacyLiveView,
    LiveKitLiveView,
    parse_live_view_response,
)
from simplipy.errors import (
    InvalidCredentialsError,
    LiveViewError,
    RequestError,
    UnsupportedStreamProviderError,
)
from simplipy.system.v3 import SystemV3
from simplipy.util.dt import utcnow

from .common import TEST_ACCESS_TOKEN, TEST_CAMERA_ID, TEST_SYSTEM_ID, load_fixture

HUB_HOST = "app-hub.prd.aser.simplisafe.com"
HUB_PATH = f"/v2/cameras/{TEST_CAMERA_ID}/{TEST_SYSTEM_ID}/live-view"


def make_camera(api: API, provider: Any = None) -> Camera:
    """Create a camera without cloud calls, keeping UUID and serial distinct."""
    data = json.loads(load_fixture("subscriptions_response.json"))["subscriptions"][0][
        "location"
    ]["system"]["cameras"][0]
    data["serial"] = "hardware-serial"
    data["cameraSettings"]["admin"]["webRTCProvider"] = provider
    system = cast(
        SystemV3,
        SimpleNamespace(
            _api=api, system_id=TEST_SYSTEM_ID, camera_data={TEST_CAMERA_ID: data}
        ),
    )
    return Camera(system, DeviceTypes.CAMERA, TEST_CAMERA_ID)


@pytest.mark.parametrize(
    ("provider", "expected"),
    [
        (None, CameraStreamProvider.LEGACY),
        ("", CameraStreamProvider.LEGACY),
        ("simplisafe", CameraStreamProvider.LEGACY),
        ("kvs", CameraStreamProvider.KVS),
        ("mist", CameraStreamProvider.MIST),
        ("future-provider", CameraStreamProvider.UNKNOWN),
        (7, CameraStreamProvider.UNKNOWN),
    ],
)
@pytest.mark.asyncio
async def test_provider_discovery(
    provider: Any, expected: CameraStreamProvider
) -> None:
    """Discover a transport using provider settings, independently of model."""
    async with aiohttp.ClientSession() as session:
        camera = make_camera(API(session=session), provider)
        assert camera.uuid == camera.serial == TEST_CAMERA_ID
        assert camera.uuid != "hardware-serial"
        assert camera.stream_provider == expected
        assert camera.webrtc_provider == (
            provider or None if isinstance(provider, str) else None
        )
        camera._system.camera_data[TEST_CAMERA_ID]["model"] = "unknown-model"
        assert camera.stream_provider == expected
        camera.camera_settings["admin"] = None
        assert camera.webrtc_provider is None
        assert camera.stream_provider == CameraStreamProvider.LEGACY


@pytest.mark.parametrize(
    ("provider", "fixture", "expected_type"),
    [
        ("kvs", "kvs_live_view_response.json", KinesisLiveView),
        ("mist", "mist_live_view_response.json", LiveKitLiveView),
    ],
)
@pytest.mark.asyncio
async def test_fresh_live_view_and_private_logging(
    aresponses: ResponsesMockServer,
    caplog: pytest.LogCaptureFixture,
    provider: str,
    fixture: str,
    expected_type: type,
) -> None:
    """Fetch each session, preserving app-hub Host/auth and hiding secrets."""
    payload = json.loads(load_fixture(fixture))
    second_payload = deepcopy(payload)
    if provider == "mist":
        second_payload["liveKitDetails"]["userToken"] = "replacement-livekit-token"
    else:
        second_payload["signedChannelEndpoint"] += "&session=second"

    async def response(request: aiohttp.web.Request) -> aiohttp.web.Response:
        assert request.headers["Host"] == HUB_HOST
        assert request.headers["Authorization"] == f"Bearer {TEST_ACCESS_TOKEN}"
        assert "access_token" not in request.query
        return aiohttp.web.json_response(payload)

    aresponses.add(HUB_HOST, HUB_PATH, "get", response=response)
    aresponses.add(
        HUB_HOST, HUB_PATH, "get", response=aiohttp.web.json_response(second_payload)
    )
    caplog.set_level(logging.DEBUG, logger="simplipy")
    async with aiohttp.ClientSession() as session:
        api = API(session=session)
        api.access_token = TEST_ACCESS_TOKEN
        camera = make_camera(api, provider)
        first = await camera.async_get_live_view()
        second = await camera.async_get_live_view()
        assert isinstance(first, expected_type)
        assert first != second
        if isinstance(first, KinesisLiveView):
            assert first.ice_servers[1].credential == "temporary-turn-password"
            assert first.ice_servers[0].username is None
        else:
            assert isinstance(first, LiveKitLiveView)
            assert first.user_token == "temporary-livekit-token"
        assert "temporary-signature" not in repr(first)
        assert "temporary-turn-password" not in repr(first)
        assert "temporary-livekit-token" not in repr(first)
        assert "replacement-livekit-token" not in repr(second)
        assert "temporary-livekit-token" not in json.dumps(camera.as_dict())
        assert "temporary-signature" not in caplog.text
        assert "temporary-turn-password" not in caplog.text
        assert "temporary-livekit-token" not in caplog.text
        assert "replacement-livekit-token" not in caplog.text
    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_unflagged_live_view_is_private(
    aresponses: ResponsesMockServer, caplog: pytest.LogCaptureFixture
) -> None:
    """Protect credentials even when a caller omits the sensitive flag."""
    payload = json.loads(load_fixture("mist_live_view_response.json"))
    aresponses.add(
        HUB_HOST, HUB_PATH, "get", response=aiohttp.web.json_response(payload)
    )
    caplog.set_level(logging.DEBUG, logger="simplipy")
    async with aiohttp.ClientSession() as session:
        api = API(session=session)
        result = await api.async_request(
            "get", HUB_PATH.removeprefix("/v2/"), url_base=WEBRTC_URL_BASE
        )
        assert result == payload
    assert "temporary-livekit-token" not in caplog.text
    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_legacy_authentication_and_current_token(
    aresponses: ResponsesMockServer,
) -> None:
    """Return FLV bearer headers with the current token for every viewer."""
    aresponses.add(
        "api.simplisafe.com",
        "/v1/api/authCheck",
        "get",
        response=aiohttp.web.json_response({"userId": 12345}),
        repeat=2,
    )
    async with aiohttp.ClientSession() as session:
        api = API(session=session)
        api.access_token = "first-access-token"
        camera = make_camera(api)
        first = await camera.async_get_live_view(width=720, audio_encoding="OPUS")
        api.access_token = "refreshed-access-token"
        second = await camera.async_get_live_view()
        assert isinstance(first, LegacyLiveView)
        assert first.url == camera.video_url(width=720, audio_encoding="OPUS")
        assert first.headers["Authorization"] == "Bearer first-access-token"
        assert isinstance(second, LegacyLiveView)
        assert second.headers["Authorization"] == "Bearer refreshed-access-token"
        assert "access_token" not in second.url
        assert "refreshed-access-token" not in repr(second)
        with pytest.raises(TypeError):
            second.headers["Authorization"] = "mutable"  # type: ignore[index]
    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_unsupported_and_missing_token() -> None:
    """Reject unknown providers before requesting a session, and absent auth."""
    async with aiohttp.ClientSession() as session:
        api = API(session=session)
        api.async_request = AsyncMock(return_value={})
        with pytest.raises(UnsupportedStreamProviderError):
            await make_camera(api, "future-provider").async_get_live_view()
        api.async_request.assert_not_called()
        with pytest.raises(InvalidCredentialsError):
            await make_camera(api).async_get_live_view()


@pytest.mark.parametrize("provider", [None, "mist"])
@pytest.mark.asyncio
async def test_expired_access_token_refresh(
    aresponses: ResponsesMockServer,
    api_token_response: dict[str, Any],
    caplog: pytest.LogCaptureFixture,
    provider: str | None,
) -> None:
    """An expired account token refreshes and retries the same live-view request."""
    host = HUB_HOST if provider else "api.simplisafe.com"
    path = HUB_PATH if provider else "/v1/api/authCheck"
    aresponses.add(
        host, path, "get", response=aresponses.Response(status=401, text="Unauthorized")
    )
    new_tokens = {
        **api_token_response,
        "access_token": "new-access-token",
        "refresh_token": "new-refresh-token",
    }
    aresponses.add(
        "auth.simplisafe.com",
        "/oauth/token",
        "post",
        response=aiohttp.web.json_response(new_tokens),
    )

    async def success(request: aiohttp.web.Request) -> aiohttp.web.Response:
        assert request.headers["Authorization"] == "Bearer new-access-token"
        payload = (
            json.loads(load_fixture("mist_live_view_response.json"))
            if provider
            else {"userId": 12345}
        )
        return aiohttp.web.json_response(payload)

    aresponses.add(host, path, "get", response=success)
    caplog.set_level(logging.DEBUG, logger="simplipy")
    async with aiohttp.ClientSession() as session:
        api = API(session=session, request_retries=2)
        api.access_token = "old-access-token"
        api.refresh_token = "old-refresh-token"
        api._token_last_refreshed = utcnow() - timedelta(seconds=30)
        with patch("asyncio.sleep", new_callable=AsyncMock):
            view = await make_camera(api, provider).async_get_live_view()
        assert api.access_token == "new-access-token"
        assert api.refresh_token == "new-refresh-token"
        if isinstance(view, LegacyLiveView):
            assert view.headers["Authorization"] == "Bearer new-access-token"
        assert "new-access-token" not in caplog.text
        assert "new-refresh-token" not in caplog.text
    aresponses.assert_plan_strictly_followed()


@pytest.mark.parametrize("status", [401, 403, 429, 503])
@pytest.mark.asyncio
async def test_live_view_http_error(
    aresponses: ResponsesMockServer, status: int
) -> None:
    """Use the existing request error policy for authentication and service errors."""
    aresponses.add(
        HUB_HOST,
        HUB_PATH,
        "get",
        response=aiohttp.web.json_response(
            {"message": "temporary-livekit-token"}, status=status
        ),
    )
    async with aiohttp.ClientSession() as session:
        api = API(session=session, request_retries=1)
        api.access_token = TEST_ACCESS_TOKEN
        with pytest.raises(RequestError) as error:
            await make_camera(api, "mist").async_get_live_view()
        assert "temporary-livekit-token" not in str(error.value)
    aresponses.assert_plan_strictly_followed()


@pytest.mark.parametrize(
    "payload",
    [[], None, 42, {"liveKitDetails": {"userToken": "temporary-livekit-token"}}],
)
@pytest.mark.asyncio
async def test_invalid_api_response(
    aresponses: ResponsesMockServer, payload: Any
) -> None:
    """Reject malformed API responses without returning partial credentials."""
    aresponses.add(
        HUB_HOST, HUB_PATH, "get", response=aiohttp.web.json_response(payload)
    )
    async with aiohttp.ClientSession() as session:
        api = API(session=session)
        with pytest.raises(RequestError):
            await make_camera(api, "mist").async_get_live_view()
    aresponses.assert_plan_strictly_followed()


@pytest.mark.parametrize(
    ("provider", "data"),
    [
        (CameraStreamProvider.MIST, {}),
        (CameraStreamProvider.MIST, {"liveKitDetails": "secret"}),
        (
            CameraStreamProvider.MIST,
            {
                "liveKitDetails": {
                    "liveKitURL": "http://plain.test",
                    "userToken": "secret",
                }
            },
        ),
        (
            CameraStreamProvider.MIST,
            {"liveKitDetails": {"liveKitURL": "wss://[invalid", "userToken": "secret"}},
        ),
        (
            CameraStreamProvider.MIST,
            {"liveKitDetails": {"liveKitURL": "wss://live.test", "userToken": ""}},
        ),
        (
            CameraStreamProvider.MIST,
            {
                "liveKitDetails": {
                    "liveKitURL": "wss://live.test",
                    "userToken": "secret\r\n",
                }
            },
        ),
        (CameraStreamProvider.KVS, {"iceServers": []}),
        (
            CameraStreamProvider.KVS,
            {"signedChannelEndpoint": "wss://signal.test", "clientId": "id"},
        ),
        (
            CameraStreamProvider.KVS,
            {
                "signedChannelEndpoint": "wss://signal.test",
                "clientId": "id",
                "iceServers": [None],
            },
        ),
        (
            CameraStreamProvider.KVS,
            {
                "signedChannelEndpoint": "wss://signal.test",
                "clientId": "id",
                "iceServers": [{"urls": []}],
            },
        ),
        (
            CameraStreamProvider.KVS,
            {
                "signedChannelEndpoint": "wss://signal.test",
                "clientId": "id",
                "iceServers": [{"urls": ["https://invalid.test"]}],
            },
        ),
        (
            CameraStreamProvider.KVS,
            {
                "signedChannelEndpoint": "wss://signal.test",
                "clientId": "id",
                "iceServers": [{"urls": [1]}],
            },
        ),
        (
            CameraStreamProvider.KVS,
            {
                "signedChannelEndpoint": "wss://signal.test",
                "clientId": "id",
                "iceServers": [{"urls": ["turn:host"], "username": 1}],
            },
        ),
        (
            CameraStreamProvider.KVS,
            {
                "signedChannelEndpoint": "wss://signal.test",
                "clientId": "id",
                "iceServers": [{"urls": ["turn:host"], "credential": 1}],
            },
        ),
        (CameraStreamProvider.LEGACY, {}),
        (CameraStreamProvider.MIST, None),
    ],
)
def test_malformed_provider_contract(provider: CameraStreamProvider, data: Any) -> None:
    """Report malformed fields without reproducing credentials in errors."""
    with pytest.raises(LiveViewError) as error:
        parse_live_view_response(provider, data)
    assert "secret" not in str(error.value)


def test_ice_server_string_urls() -> None:
    """Accept the WebRTC single-string ICE URLs representation as well as lists."""
    view = parse_live_view_response(
        CameraStreamProvider.KVS,
        {
            "signedChannelEndpoint": "wss://signal.test",
            "clientId": "id",
            "iceServers": [{"urls": "stun:host"}],
        },
    )
    assert isinstance(view, KinesisLiveView)
    assert view.ice_servers[0].urls == ("stun:host",)
