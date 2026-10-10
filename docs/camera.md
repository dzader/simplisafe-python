# Cameras

{meth}`Camera <simplipy.camera.Camera>` objects correspond to SimpliSafe™ "SimpliCam"
cameras and doorbells (only available for V3 systems) and allow users to retrieve
information on them, including URLs to view short-lived streams of the camera.

## Core Properties

All {meth}`Camera <simplipy.camera.Camera>` objects come with a standard set of properties:

```python
for serial, camera in system.cameras.items():
    # Return the camera's UUID:
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

## Discovering the Stream Transport

`camera.uuid` identifies the camera in the media APIs. For compatibility,
`camera.serial` returns that same UUID, which can differ from a hardware serial
in the subscription response. Select the streaming transport using
`camera.stream_provider`, rather than inferring it from a model name:

| Provider | Transport | Required consumer |
| --- | --- | --- |
| `CameraStreamProvider.LEGACY` | Authenticated FLV over HTTPS | Media player or relay supporting HTTP headers |
| `CameraStreamProvider.KVS` | AWS Kinesis WebRTC | Kinesis signaling adapter and WebRTC peer |
| `CameraStreamProvider.MIST` | LiveKit WebRTC | LiveKit signaling adapter and WebRTC peer |
| `CameraStreamProvider.UNKNOWN` | An unrecognized provider | Unsupported until its protocol is implemented |

The raw `camera.webrtc_provider` is the value of
`cameraSettings.admin.webRTCProvider`. An absent value or `simplisafe` selects
legacy FLV; `kvs` selects Kinesis; `mist` selects LiveKit. The older
`supportedFeatures.providers.webrtc` value can be `none` on a working legacy
camera.

## Getting Fresh Live-View Credentials

```python
from simplipy.device.live_view import (
    KinesisLiveView,
    LegacyLiveView,
    LiveKitLiveView,
)

# Call once for each new viewer session. Do not save or log this object.
live_view = await camera.async_get_live_view(width=1280)

if isinstance(live_view, LegacyLiveView):
    # Pass BOTH values to your media relay. A URL alone is unauthenticated.
    source_url = live_view.url
    source_headers = live_view.headers
elif isinstance(live_view, KinesisLiveView):
    # Pass these to a Kinesis signaling adapter, then negotiate WebRTC.
    signaling_url = live_view.signed_channel_endpoint
    client_id = live_view.client_id
    ice_servers = live_view.ice_servers
elif isinstance(live_view, LiveKitLiveView):
    # Join through a LiveKit signaling adapter, then subscribe to the camera.
    service_url = live_view.livekit_url
    participant_token = live_view.user_token
```

Kinesis and LiveKit credentials are fetched from
`https://app-hub.prd.aser.simplisafe.com/v2/cameras/{uuid}/{sid}/live-view` using the
authenticated API's retry and token refresh policy. Legacy FLV uses
`Authorization: Bearer ...` as an HTTP header. It checks authentication before
returning the current bearer token. Tokens are never appended to the FLV URL.
The library does not cache live-view credentials and deliberately omits them
from object representations and API debug payload logs.

These are temporary credentials, not permanent RTSP/HLS URLs. Their exact
lifetime is not exposed by the documented response contracts, so callers must
request a new session whenever they start or reconnect a viewer. The library
validates response structure but does not connect to the media transport,
relay video, or negotiate WebRTC itself. A sleeping or unavailable camera can
return incomplete session details; in that case `LiveViewError` is raised
rather than returning unusable credentials.

The transport contracts are based on public implementations in
[hass-simplirtc](https://github.com/gilliginsisland/hass-simplirtc) and
[homebridge-simplisafe3](https://github.com/homebridge-simplisafe3/homebridge-simplisafe3).
Synthetic tests cover discovery, response validation, auth refresh, and secret
handling. They do not establish playback on a physical camera or account.

## Getting the Legacy Camera Video URL

```python
url = camera.video_url()
# >>> https://media.simplisafe.com/v1/...
```

`video_url()` remains available for existing clients. It only constructs a URL;
use `async_get_live_view()` to obtain the authentication header as well.
