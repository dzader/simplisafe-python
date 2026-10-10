"""Define short-lived camera live-view credentials and response validation.

These objects describe transports; they do not open or relay a media stream.
Fetch a new object for each viewing session and do not persist credentials.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from urllib.parse import urlsplit

from simplipy.errors import LiveViewError


class CameraStreamProvider(Enum):
    """Define camera live-view transports independently of the camera model."""

    LEGACY = "simplisafe"
    KVS = "kvs"
    MIST = "mist"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class LegacyLiveView:
    """An authenticated FLV request, requiring a media player or relay.

    Args:
        url: The FLV media URL.
        headers: The headers required to authenticate the media request.
    """

    url: str = field(repr=False)
    headers: Mapping[str, str] = field(repr=False)
    provider: CameraStreamProvider = field(
        default=CameraStreamProvider.LEGACY, init=False
    )


@dataclass(frozen=True)
class KinesisIceServer:
    """An ICE server returned with a Kinesis signaling session.

    Args:
        urls: STUN or TURN server URLs.
        username: Optional temporary TURN username.
        credential: Optional temporary TURN password.
    """

    urls: tuple[str, ...]
    username: str | None = field(default=None, repr=False)
    credential: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class KinesisLiveView:
    """A Kinesis WebRTC signaling session, requiring a signaling adapter.

    Args:
        signed_channel_endpoint: The temporary signed signaling WebSocket URL.
        client_id: The viewer client identifier.
        ice_servers: The ICE servers for this session.
    """

    signed_channel_endpoint: str = field(repr=False)
    client_id: str
    ice_servers: tuple[KinesisIceServer, ...]
    provider: CameraStreamProvider = field(default=CameraStreamProvider.KVS, init=False)


@dataclass(frozen=True)
class LiveKitLiveView:
    """A LiveKit room session, requiring a LiveKit signaling adapter.

    Args:
        livekit_url: The LiveKit service URL.
        user_token: The temporary participant token.
    """

    livekit_url: str = field(repr=False)
    user_token: str = field(repr=False)
    provider: CameraStreamProvider = field(
        default=CameraStreamProvider.MIST, init=False
    )


CameraLiveView = LegacyLiveView | KinesisLiveView | LiveKitLiveView


def _required_string(data: Mapping[str, Any], key: str) -> str:
    """Read a required string without including the response in errors."""
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise LiveViewError(f"Live-view response is missing a valid {key}")
    if any(character in value for character in ("\r", "\n", "\x00")):
        raise LiveViewError(f"Live-view response contains an invalid {key}")
    return value


def _required_url(data: Mapping[str, Any], key: str, schemes: set[str]) -> str:
    """Read a secure transport URL without logging its signed query."""
    value = _required_string(data, key)
    try:
        parsed = urlsplit(value)
        valid = parsed.scheme in schemes and bool(parsed.hostname)
    except ValueError as err:
        raise LiveViewError(f"Live-view response contains an invalid {key}") from err
    if not valid:
        raise LiveViewError(f"Live-view response contains an invalid {key}")
    return value


def _parse_ice_server(data: Any) -> KinesisIceServer:
    """Validate an ICE server, retaining credentials only in hidden fields."""
    if not isinstance(data, Mapping):
        raise LiveViewError("Live-view response contains an invalid ICE server")
    urls = data.get("urls")
    if isinstance(urls, str):
        urls = [urls]
    if not isinstance(urls, list) or not urls:
        raise LiveViewError("Live-view response contains invalid ICE URLs")
    for url in urls:
        if (
            not isinstance(url, str)
            or not url.partition(":")[2]
            or url.partition(":")[0] not in {"stun", "stuns", "turn", "turns"}
            or any(character in url for character in ("\r", "\n", "\x00"))
        ):
            raise LiveViewError("Live-view response contains invalid ICE URLs")
    username = data.get("username")
    credential = data.get("credential")
    if username is not None and not isinstance(username, str):
        raise LiveViewError("Live-view response contains an invalid ICE username")
    if credential is not None and not isinstance(credential, str):
        raise LiveViewError("Live-view response contains an invalid ICE credential")
    return KinesisIceServer(tuple(urls), username, credential)


def parse_live_view_response(
    provider: CameraStreamProvider, data: Mapping[str, Any]
) -> KinesisLiveView | LiveKitLiveView:
    """Validate a provider-specific live-view response.

    Args:
        provider: The camera's known WebRTC provider.
        data: The response from the app-hub live-view endpoint.

    Returns:
        Fresh credentials for the selected WebRTC transport.

    Raises:
        LiveViewError: If the provider response is incomplete or malformed.
    """
    if not isinstance(data, Mapping):
        raise LiveViewError("Expected a JSON object in the live-view response")
    if provider == CameraStreamProvider.KVS:
        servers = data.get("iceServers")
        if not isinstance(servers, list):
            raise LiveViewError("Live-view response is missing valid iceServers")
        return KinesisLiveView(
            signed_channel_endpoint=_required_url(
                data, "signedChannelEndpoint", {"wss"}
            ),
            client_id=_required_string(data, "clientId"),
            ice_servers=tuple(_parse_ice_server(server) for server in servers),
        )
    if provider == CameraStreamProvider.MIST:
        details = data.get("liveKitDetails")
        if not isinstance(details, Mapping):
            raise LiveViewError("Live-view response is missing liveKitDetails")
        return LiveKitLiveView(
            livekit_url=_required_url(details, "liveKitURL", {"wss", "https"}),
            user_token=_required_string(details, "userToken"),
        )
    raise LiveViewError("Expected a supported WebRTC provider")
