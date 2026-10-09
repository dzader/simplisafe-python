"""Define SimpliSafe cameras (SimpliCams)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, AsyncGenerator, cast
from urllib.parse import urlencode
import json

from aiohttp import ClientTimeout

from simplipy.const import LOGGER
from simplipy.device import DeviceV3

if TYPE_CHECKING:
    from simplipy.system.v3 import SystemV3

DEFAULT_AUDIO_ENCODING = "AAC"
DEFAULT_MEDIA_URL_BASE = "https://media.simplisafe.com/v1"
DEFAULT_VIDEO_WIDTH = 1280
DEFAULT_SNAPSHOT_WIDTH = 1280
DEFAULT_STREAM_CHUNK_SIZE = 1024
DEFAULT_WAKEUP_TIMEOUT = 30  # seconds to wait for outdoor camera to wake up
DEFAULT_WAKEUP_RETRY_DELAY = 2  # seconds between wake-up retry attempts
DEFAULT_CAMERA_TIMEOUT = 30  # seconds timeout for camera operations (snapshot/stream)
DEFAULT_WEBRTC_URL_BASE = "https://app-hub.prd.aser.simplisafe.com/v2"


class CameraTypes(Enum):
    """Define camera types based on internal SimpliSafe ID number."""

    CAMERA = 0
    DOORBELL = 1
    OUTDOOR_CAMERA = 2
    UNKNOWN = 99


class StreamFormat(Enum):
    """Define supported stream formats."""

    FLV = "flv"
    MJPEG = "mjpg"


MODEL_TO_TYPE = {
    "SS001": CameraTypes.CAMERA,
    "SS002": CameraTypes.DOORBELL,
    "SS003": CameraTypes.CAMERA,
    "SSOBCM4": CameraTypes.OUTDOOR_CAMERA,
}


@dataclass
class LiveViewResponse:
    """Response from SimpliSafe live view API for outdoor cameras."""

    liveKitURL: str
    userToken: str
    cameraStatus: str


@dataclass
class KinesisLiveViewResponse:
    """Legacy response format for Kinesis-based streaming (kept for compatibility)."""

    signedChannelEndpoint: str
    clientId: str
    iceServers: list[dict]


class Camera(DeviceV3):
    """Define a SimpliCam."""

    _system: SystemV3

    @property
    def camera_settings(self) -> dict[str, Any]:
        """Return the camera settings.

        Returns:
            A dictionary of camera settings.
        """
        return cast(
            dict[str, Any], self._system.camera_data[self._serial]["cameraSettings"]
        )

    @property
    def camera_type(self) -> CameraTypes:
        """Return the type of camera.

        Returns:
            The camera type.
        """
        try:
            return MODEL_TO_TYPE[self._system.camera_data[self._serial]["model"]]
        except KeyError:
            LOGGER.error(
                "Unknown camera type: %s",
                self._system.camera_data[self._serial]["model"],
            )
            return CameraTypes.UNKNOWN

    @property
    def is_outdoor_camera(self) -> bool:
        """Return whether this is an outdoor camera that requires wake-up.

        Returns:
            True if this is an outdoor camera.
        """
        return self.camera_type == CameraTypes.OUTDOOR_CAMERA

    @property
    def name(self) -> str:
        """Return the camera name.

        Returns:
            The camera name.
        """
        return cast(
            str, self._system.camera_data[self._serial]["cameraSettings"]["cameraName"]
        )

    @property
    def serial(self) -> str:
        """Return the camera's serial number.

        Returns:
            The camera serial number.
        """
        return self._serial

    @property
    def shutter_open_when_away(self) -> bool:
        """Return whether the privacy shutter is open in away mode.

        Returns:
            The camera's "shutter open when away" status.
        """
        val = self._system.camera_data[self._serial]["cameraSettings"]["shutterAway"]
        return cast(bool, val == "open")

    @property
    def shutter_open_when_home(self) -> bool:
        """Return whether the privacy shutter is open in home mode.

        Returns:
            The camera's "shutter open when home" status.
        """
        val = self._system.camera_data[self._serial]["cameraSettings"]["shutterHome"]
        return cast(bool, val == "open")

    @property
    def shutter_open_when_off(self) -> bool:
        """Return whether the privacy shutter is open when the alarm is disarmed.

        Returns:
            The camera's "shutter open when off" status.
        """
        val = self._system.camera_data[self._serial]["cameraSettings"]["shutterOff"]
        return cast(bool, val == "open")

    @property
    def status(self) -> str:
        """Return the camera status.

        Returns:
            The camera status.
        """
        return cast(str, self._system.camera_data[self._serial]["status"])

    @property
    def subscription_enabled(self) -> bool:
        """Return the camera subscription status.

        Returns:
            The camera subscription status.
        """
        return cast(
            bool, self._system.camera_data[self._serial]["subscription"]["enabled"]
        )

    @property
    def streaming_provider(self) -> str:
        """Return the streaming provider for this camera.

        Returns:
            The streaming provider ('simplisafe', 'kvs', 'mist', or 'unknown').
        """
        try:
            # Get the provider information from camera settings
            admin_settings = self._system.camera_data[self._serial]["cameraSettings"]["admin"]
            return admin_settings.get("webRTCProvider", "simplisafe").lower()
        except (KeyError, TypeError):
            # Fallback to checking supported features
            try:
                features = self._system.camera_data[self._serial]["supportedFeatures"]
                providers = features.get("providers", {})
                webrtc_provider = providers.get("webrtc", "simplisafe")
                return webrtc_provider.lower() if webrtc_provider != "none" else "simplisafe"
            except (KeyError, TypeError):
                return "simplisafe"

    @property
    def recording_provider(self) -> str:
        """Return the recording provider for this camera.

        Returns:
            The recording provider ('simplisafe', 'kvs', 'mist', or 'unknown').
        """
        try:
            # Get the provider information from camera settings
            admin_settings = self._system.camera_data[self._serial]["cameraSettings"]["admin"]
            return admin_settings.get("recordingProvider", "simplisafe").lower()
        except (KeyError, TypeError):
            # Fallback to checking supported features
            try:
                features = self._system.camera_data[self._serial]["supportedFeatures"]
                providers = features.get("providers", {})
                recording_provider = providers.get("recording", "simplisafe")
                return recording_provider.lower() if recording_provider != "none" else "simplisafe"
            except (KeyError, TypeError):
                return "simplisafe"

    @property
    def supports_standard_streaming(self) -> bool:
        """Return whether this camera supports standard SimpliSafe streaming.

        Returns:
            True if the camera uses SimpliSafe's media endpoints.
        """
        return self.streaming_provider == "simplisafe" and self.recording_provider == "simplisafe"

    @property
    def supports_webrtc_streaming(self) -> bool:
        """Return whether this camera supports WebRTC streaming.

        Returns:
            True if this camera supports WebRTC (outdoor cameras with KVS/Mist providers).
        """
        return self.is_outdoor_camera and self.streaming_provider in ("kvs", "mist")

    async def async_wake_up(self, timeout: int = DEFAULT_WAKEUP_TIMEOUT) -> bool:
        """Wake up an outdoor camera if needed.

        Args:
            timeout: Maximum time to wait for camera to wake up (seconds).

        Returns:
            True if camera is awake and ready, False if wake-up failed.
        """
        # Use the enhanced wake-up method for better reliability
        return await self.async_wake_up_enhanced(timeout)

    async def async_ensure_awake(self, timeout: int = DEFAULT_WAKEUP_TIMEOUT) -> bool:
        """Ensure camera is awake and ready for operations.
        
        This is a convenience method that automatically wakes up outdoor cameras
        when needed, similar to how the SimpliSafe app behaves.
        
        Args:
            timeout: Maximum time to wait for camera to wake up (seconds).
            
        Returns:
            True if camera is awake and ready, False if wake-up failed.
        """
        if not self.is_outdoor_camera:
            # Indoor cameras are always ready
            return True
            
        if self.status == "online":
            # Camera appears to be online, but outdoor cameras might still need wake-up
            LOGGER.debug("Camera %s appears online, attempting wake-up to ensure readiness", self.name)
        else:
            LOGGER.info("Camera %s is %s, attempting to wake up", self.name, self.status)
            
        return await self.async_wake_up(timeout)

    async def async_wake_up_enhanced(self, timeout: int = DEFAULT_WAKEUP_TIMEOUT) -> bool:
        """Enhanced wake-up with multiple strategies, like SimpliSafe app.

        Args:
            timeout: Maximum time to wait for camera to wake up (seconds).

        Returns:
            True if camera is awake and ready, False if wake-up failed.
        """
        if not self.is_outdoor_camera:
            return True

        LOGGER.info("Waking up outdoor camera %s (enhanced method)", self.name)

        try:
            # Strategy 1: Standard wake-up endpoints
            wake_up_endpoints = [
                f"cameras/{self._serial}/wakeup",
                f"cameras/{self._serial}/wake", 
                f"cameras/{self._serial}/activate",
                f"v1/ss3/subscriptions/{self._system.system_id}/cameras/{self._serial}/wakeup",
                f"subscriptions/{self._system.system_id}/cameras/{self._serial}/wake",
            ]

            wake_up_successful = False
            for endpoint in wake_up_endpoints:
                try:
                    # Try different payload formats
                    payloads = [
                        {"action": "wake"},
                        {"command": "wakeup"},
                        {"state": "active"},
                        {}  # Empty payload
                    ]
                    
                    for payload in payloads:
                        try:
                            await self._system._api._async_api_request(
                                "post", endpoint, json=payload
                            )
                            wake_up_successful = True
                            LOGGER.debug("Wake-up successful via endpoint: %s with payload: %s", endpoint, payload)
                            break
                        except Exception as payload_err:
                            LOGGER.debug("Payload %s failed for endpoint %s: %s", payload, endpoint, payload_err)
                            continue
                    
                    if wake_up_successful:
                        break
                        
                except Exception as endpoint_err:
                    LOGGER.debug("Wake-up endpoint %s failed: %s", endpoint, endpoint_err)
                    continue

            # Strategy 2: Alternative wake-up methods (like the app might use)
            if not wake_up_successful:
                LOGGER.info("Standard wake-up failed, trying alternative methods for camera %s", self.name)
                
                # Try requesting camera info/status which might trigger wake-up
                alternative_endpoints = [
                    f"cameras/{self._serial}/status",
                    f"cameras/{self._serial}/info", 
                    f"cameras/{self._serial}",
                    f"v1/ss3/subscriptions/{self._system.system_id}/cameras/{self._serial}",
                ]
                
                for endpoint in alternative_endpoints:
                    try:
                        await self._system._api._async_api_request("get", endpoint)
                        LOGGER.debug("Alternative wake-up method successful: %s", endpoint)
                        wake_up_successful = True
                        break
                    except Exception:
                        continue

            # Strategy 3: If all else fails, try live-view request which definitely wakes cameras
            if not wake_up_successful:
                LOGGER.info("Trying live-view request as final wake-up attempt for camera %s", self.name)
                try:
                    await self._system._api._async_api_request(
                        "get", 
                        f"cameras/{self.serial}/{self._system.system_id}/live-view",
                        url_base=DEFAULT_WEBRTC_URL_BASE
                    )
                    wake_up_successful = True
                    LOGGER.debug("Live-view wake-up successful")
                except Exception as live_view_err:
                    LOGGER.debug("Live-view wake-up failed: %s", live_view_err)

            # Wait for camera to become responsive with progressive backoff
            if wake_up_successful or True:  # Always try to verify, even if wake-up commands failed
                start_time = asyncio.get_event_loop().time()
                check_interval = 1  # Start with 1 second
                max_interval = 5   # Max 5 seconds between checks
                
                while (asyncio.get_event_loop().time() - start_time) < timeout:
                    try:
                        # Test camera responsiveness
                        await self._system._api._async_api_request(
                            "get", f"cameras/{self._serial}/status", timeout=10
                        )
                        LOGGER.info("Outdoor camera %s is now awake and ready", self.name)
                        return True
                    except Exception as check_err:
                        LOGGER.debug("Camera %s not ready yet: %s", self.name, check_err)
                        
                        # Progressive backoff - increase delay between checks
                        await asyncio.sleep(check_interval)
                        check_interval = min(check_interval * 1.5, max_interval)

            LOGGER.warning(
                "Timeout waiting for outdoor camera %s to wake up after %d seconds",
                self.name,
                timeout,
            )
            return False

        except Exception as err:
            LOGGER.error("Failed to wake up outdoor camera %s: %s", self.name, err)
            return False

    def as_dict(self) -> dict[str, Any]:
        """Return dictionary version of this device.

        Returns:
            A dict representation of this device.
        """
        return {
            "camera_settings": self.camera_settings,
            "camera_type": self.camera_type.value,
            "name": self.name,
            "serial": self.serial,
            "shutter_open_when_away": self.shutter_open_when_away,
            "shutter_open_when_home": self.shutter_open_when_home,
            "shutter_open_when_off": self.shutter_open_when_off,
            "status": self.status,
            "subscription_enabled": self.subscription_enabled,
            "is_outdoor_camera": self.is_outdoor_camera,
            "streaming_provider": self.streaming_provider,
            "recording_provider": self.recording_provider,
            "supports_standard_streaming": self.supports_standard_streaming,
            "supports_webrtc_streaming": self.supports_webrtc_streaming,
        }

    def video_url(
        self,
        width: int = DEFAULT_VIDEO_WIDTH,
        audio_encoding: str = DEFAULT_AUDIO_ENCODING,
        **kwargs: Any,
    ) -> str:
        """Return the camera video URL.

        Args:
            width: The video width.
            audio_encoding: The audio encoding.
            kwargs: Additional parameters.

        Returns:
            The camera video URL.
        """
        url_params = {"x": width, "audioEncoding": audio_encoding, **kwargs}
        return f"{DEFAULT_MEDIA_URL_BASE}/{self.serial}/flv?{urlencode(url_params)}"

    def snapshot_url(
        self,
        width: int = DEFAULT_SNAPSHOT_WIDTH,
        **kwargs: Any,
    ) -> str:
        """Return the camera snapshot URL.

        Args:
            width: The snapshot width.
            kwargs: Additional parameters.

        Returns:
            The camera snapshot URL.
        """
        url_params = {"x": width, "fr": 1, **kwargs}
        return f"{DEFAULT_MEDIA_URL_BASE}/{self.serial}/mjpg?{urlencode(url_params)}"

    def stream_url(
        self,
        format_type: StreamFormat = StreamFormat.FLV,
        width: int = DEFAULT_VIDEO_WIDTH,
        audio_encoding: str = DEFAULT_AUDIO_ENCODING,
        **kwargs: Any,
    ) -> str:
        """Return the camera stream URL for different formats.

        Args:
            format_type: The stream format (FLV or MJPEG).
            width: The video width.
            audio_encoding: The audio encoding (for FLV streams).
            kwargs: Additional parameters.

        Returns:
            The camera stream URL.
        """
        if format_type == StreamFormat.FLV:
            url_params = {"x": width, "audioEncoding": audio_encoding, **kwargs}
        elif format_type == StreamFormat.MJPEG:
            url_params = {"x": width, **kwargs}
        else:
            raise ValueError(f"Unsupported stream format: {format_type}")

        return f"{DEFAULT_MEDIA_URL_BASE}/{self.serial}/{format_type.value}?{urlencode(url_params)}"

    async def async_get_snapshot(
        self,
        width: int = DEFAULT_SNAPSHOT_WIDTH,
        timeout: int = DEFAULT_CAMERA_TIMEOUT,
        **kwargs: Any,
    ) -> bytes:
        """Get a camera snapshot.

        Args:
            width: The snapshot width.
            timeout: Timeout in seconds for the operation.
            kwargs: Additional parameters.

        Returns:
            The snapshot image data as bytes.
        """
        # Wake up outdoor camera if needed
        if self.is_outdoor_camera:
            wake_up_success = await self.async_wake_up()
            if not wake_up_success:
                raise RuntimeError(
                    f"Failed to wake up outdoor camera {self.name} for snapshot"
                )

        # Check if this camera supports standard streaming
        if not self.supports_standard_streaming:
            raise RuntimeError(
                f"Camera {self.name} uses {self.streaming_provider}/{self.recording_provider} "
                f"providers which are not yet supported for snapshots. "
                f"Only SimpliSafe-hosted cameras support snapshots currently."
            )

        url = self.snapshot_url(width=width, **kwargs)

        try:
            # Use direct HTTP request with timeout to avoid retry complications
            timeout_config = ClientTimeout(total=timeout)
            async with self._system._api.session.request(
                "GET",
                url,
                headers={
                    "User-Agent": "simplisafe-python",
                    "Authorization": f"Bearer {self._system._api.access_token}",
                },
                timeout=timeout_config,
            ) as resp:
                resp.raise_for_status()

                # Read data in chunks and detect complete JPEG
                data = await self._read_complete_jpeg(resp)
                return data
        except Exception as err:
            LOGGER.error("Failed to get snapshot for camera %s: %s", self.name, str(err))
            raise

    async def async_get_snapshot_direct(
        self,
        width: int = DEFAULT_SNAPSHOT_WIDTH,
        timeout: int = DEFAULT_CAMERA_TIMEOUT,
        **kwargs: Any,
    ) -> bytes:
        """Get a camera snapshot using direct HTTP request (bypasses retries).

        Args:
            width: The snapshot width.
            timeout: Timeout in seconds for the operation.
            kwargs: Additional parameters.

        Returns:
            The snapshot image data as bytes.
        """
        # Wake up outdoor camera if needed
        if self.is_outdoor_camera:
            wake_up_success = await self.async_wake_up()
            if not wake_up_success:
                raise RuntimeError(
                    f"Failed to wake up outdoor camera {self.name} for snapshot"
                )

        # Check if this camera supports standard streaming
        if not self.supports_standard_streaming:
            raise RuntimeError(
                f"Camera {self.name} uses {self.streaming_provider}/{self.recording_provider} "
                f"providers which are not yet supported for snapshots. "
                f"Only SimpliSafe-hosted cameras support snapshots currently."
            )

        url = self.snapshot_url(width=width, **kwargs)

        try:
            # Import aiohttp timeout for better control
            from aiohttp import ClientTimeout

            # Create timeout object with proper timeouts for each operation
            timeout_obj = ClientTimeout(total=timeout, sock_read=timeout)

            # Make a direct HTTP request with proper timeout
            async with self._system._api.session.get(
                url,
                headers={
                    "Authorization": f"Bearer {self._system._api.access_token}",
                    "User-Agent": "simplipy",
                },
                timeout=timeout_obj,
            ) as resp:
                resp.raise_for_status()

                # Get response info for debugging
                content_length = resp.headers.get('content-length', 'unknown')
                LOGGER.info(
                    "Camera %s snapshot response: status=%d, content-length=%s",
                    self.name, resp.status, content_length
                )

                # Read data in chunks and detect complete JPEG
                data = await self._read_complete_jpeg(resp)

                if len(data) == 0:
                    raise RuntimeError(
                        f"Camera {self.name} returned empty snapshot data"
                    )

                LOGGER.info(
                    "Camera %s snapshot read successfully: %d bytes",
                    self.name, len(data)
                )

                return data
        except asyncio.TimeoutError:
            raise RuntimeError(
                f"Timeout ({timeout}s) while getting snapshot from camera {self.name}"
            )
        except Exception as err:
            LOGGER.error("Failed to get direct snapshot for camera %s: %s", self.name, err)
            raise

    async def async_stream_data(
        self,
        format_type: StreamFormat = StreamFormat.FLV,
        width: int = DEFAULT_VIDEO_WIDTH,
        audio_encoding: str = DEFAULT_AUDIO_ENCODING,
        chunk_size: int = DEFAULT_STREAM_CHUNK_SIZE,
        **kwargs: Any,
    ) -> AsyncGenerator[bytes, None]:
        """Stream camera data.

        Args:
            format_type: The stream format (FLV or MJPEG).
            width: The video width.
            audio_encoding: The audio encoding (for FLV streams).
            chunk_size: The size of each data chunk.
            kwargs: Additional parameters.

        Yields:
            Chunks of stream data as bytes.
        """
        # Wake up outdoor camera if needed
        if self.is_outdoor_camera:
            wake_up_success = await self.async_wake_up()
            if not wake_up_success:
                raise RuntimeError(
                    f"Failed to wake up outdoor camera {self.name} for streaming"
                )

        # Check if this camera supports standard streaming
        if not self.supports_standard_streaming:
            raise RuntimeError(
                f"Camera {self.name} uses {self.streaming_provider}/{self.recording_provider} "
                f"providers which are not yet supported for streaming. "
                f"Only SimpliSafe-hosted cameras support streaming currently."
            )

        url = self.stream_url(
            format_type=format_type,
            width=width,
            audio_encoding=audio_encoding,
            **kwargs
        )

        try:
            async with self._system._api.session.get(
                url,
                headers={
                    "Authorization": f"Bearer {self._system._api.access_token}",
                },
            ) as resp:
                resp.raise_for_status()
                async for chunk in resp.content.iter_chunked(chunk_size):
                    yield chunk
        except Exception as err:
            LOGGER.error("Failed to stream data for camera %s: %s", self.name, err)
            raise

    async def async_save_stream_to_file(
        self,
        file_path: str,
        format_type: StreamFormat = StreamFormat.FLV,
        width: int = DEFAULT_VIDEO_WIDTH,
        audio_encoding: str = DEFAULT_AUDIO_ENCODING,
        duration_seconds: float | None = None,
        chunk_size: int = DEFAULT_STREAM_CHUNK_SIZE,
        **kwargs: Any,
    ) -> None:
        """Save camera stream to a file.

        Args:
            file_path: The path where to save the stream.
            format_type: The stream format (FLV or MJPEG).
            width: The video width.
            audio_encoding: The audio encoding (for FLV streams).
            duration_seconds: How long to record (None for indefinite).
            chunk_size: The size of each data chunk.
            kwargs: Additional parameters.
        """
        # Wake up outdoor camera if needed
        if self.is_outdoor_camera:
            wake_up_success = await self.async_wake_up()
            if not wake_up_success:
                raise RuntimeError(
                    f"Failed to wake up outdoor camera {self.name} for saving stream"
                )

        # Check if this camera supports standard streaming
        if not self.supports_standard_streaming:
            raise RuntimeError(
                f"Camera {self.name} uses {self.streaming_provider}/{self.recording_provider} "
                f"providers which are not yet supported for streaming. "
                f"Only SimpliSafe-hosted cameras support streaming currently."
            )

        start_time = asyncio.get_event_loop().time()

        try:
            with open(file_path, "wb") as file:
                async for chunk in self.async_stream_data(
                    format_type=format_type,
                    width=width,
                    audio_encoding=audio_encoding,
                    chunk_size=chunk_size,
                    **kwargs
                ):
                    file.write(chunk)

                    # Check if we should stop recording
                    if duration_seconds is not None:
                        elapsed = asyncio.get_event_loop().time() - start_time
                        if elapsed >= duration_seconds:
                            break

        except Exception as err:
            LOGGER.error("Failed to save stream for camera %s: %s", self.name, err)
            raise

    async def _read_complete_jpeg(self, response) -> bytes:
        """Read data from response until we have a complete JPEG image.

        This solves the issue where SimpliSafe camera endpoints send the JPEG data
        but never close the connection, causing resp.read() to hang indefinitely.

        Args:
            response: The aiohttp response object

        Returns:
            Complete JPEG image data as bytes
        """
        JPEG_START = b'\xff\xd8'  # JPEG file start marker
        JPEG_END = b'\xff\xd9'    # JPEG file end marker

        data = b''
        chunk_size = 8192  # 8KB chunks

        try:
            # Read data in chunks
            async for chunk in response.content.iter_chunked(chunk_size):
                data += chunk

                # Check if we have a complete JPEG
                if data.startswith(JPEG_START) and data.endswith(JPEG_END):
                    LOGGER.debug(
                        "Camera %s: Complete JPEG detected (%d bytes)",
                        self.name, len(data)
                    )
                    break

                # Safety check: if data is getting too large, something is wrong
                if len(data) > 10 * 1024 * 1024:  # 10MB max
                    raise RuntimeError(
                        f"Camera {self.name}: Snapshot data exceeded 10MB, aborting"
                    )

        except Exception as err:
            LOGGER.error(
                "Camera %s: Error reading chunked data: %s",
                self.name, str(err)
            )
            raise

        # Validate we got a proper JPEG
        if not data.startswith(JPEG_START):
            raise RuntimeError(
                f"Camera {self.name}: Response doesn't start with JPEG marker"
            )

        if not data.endswith(JPEG_END):
            LOGGER.warning(
                "Camera %s: Response doesn't end with JPEG marker, may be incomplete",
                self.name
            )

        return data

    async def async_get_webrtc_stream_info(self) -> LiveViewResponse:
        """Get WebRTC stream information for outdoor cameras.

        This method retrieves the LiveKit streaming information needed
        to establish a WebRTC connection for outdoor cameras.

        Returns:
            LiveViewResponse containing LiveKit URL, user token, and camera status.

        Raises:
            RuntimeError: If the camera doesn't support WebRTC streaming.
        """
        if not self.is_outdoor_camera:
            raise RuntimeError(
                f"Camera {self.name} is not an outdoor camera. "
                f"WebRTC streaming is only supported for outdoor cameras."
            )

        if self.streaming_provider not in ("kvs", "mist"):
            raise RuntimeError(
                f"Camera {self.name} uses {self.streaming_provider} provider "
                f"which doesn't support WebRTC streaming."
            )

        # Wake up the camera first (like SimpliSafe app does)
        wake_success = await self.async_ensure_awake()
        if not wake_success:
            raise RuntimeError(
                f"Failed to wake up outdoor camera {self.name} for streaming. "
                f"Camera may be offline or have connectivity issues."
            )

        try:
            # Call the WebRTC live view API
            url = f"cameras/{self.serial}/{self._system.system_id}/live-view"
            resp = await self._system._api.async_request(
                "get",
                url,
                url_base=DEFAULT_WEBRTC_URL_BASE
            )

            LOGGER.debug(
                "WebRTC API response for camera %s: %s",
                self.name,
                resp
            )

            # Check for LiveKit format (newer cameras)
            if "liveKitDetails" in resp:
                live_kit_details = resp["liveKitDetails"]
                required_fields = ["liveKitURL", "userToken"]
                missing_fields = [field for field in required_fields if field not in live_kit_details]

                if missing_fields:
                    raise RuntimeError(
                        f"LiveKit details missing required fields: {missing_fields}. "
                        f"Available fields: {list(live_kit_details.keys())}"
                    )

                LOGGER.info(
                    "Retrieved LiveKit WebRTC stream info for camera %s: liveKitURL=%s, status=%s",
                    self.name,
                    live_kit_details["liveKitURL"],
                    resp.get("cameraStatus", "unknown")
                )

                return LiveViewResponse(
                    liveKitURL=live_kit_details["liveKitURL"],
                    userToken=live_kit_details["userToken"],
                    cameraStatus=resp.get("cameraStatus", "unknown")
                )

            # Check for legacy Kinesis format (older cameras)
            elif all(field in resp for field in ["signedChannelEndpoint", "clientId", "iceServers"]):
                LOGGER.warning(
                    "Camera %s uses legacy Kinesis WebRTC format. "
                    "This is not yet fully supported. Consider upgrading camera firmware.",
                    self.name
                )

                # For now, we'll raise an error with helpful information
                raise RuntimeError(
                    f"Camera {self.name} uses legacy Kinesis WebRTC format which is not yet supported. "
                    f"Found Kinesis fields: channelEndpoint={resp.get('channelEndpoint', 'N/A')}, "
                    f"clientId={resp.get('clientId', 'N/A')}. "
                    f"Consider updating camera firmware to enable LiveKit streaming."
                )

            else:
                raise RuntimeError(
                    f"Unknown WebRTC response format for camera {self.name}. "
                    f"Available fields: {list(resp.keys())}"
                )

        except Exception as err:
            LOGGER.error(
                "Failed to get WebRTC stream info for camera %s: %s",
                self.name, str(err)
            )
            raise

    def get_webrtc_uri(self, stream_info: LiveViewResponse) -> str:
        """Generate a WebRTC URI for use with LiveKit-compatible tools.

        Args:
            stream_info: The LiveViewResponse from async_get_webrtc_stream_info()

        Returns:
            A LiveKit WebRTC URL that can be used for streaming
        """
        # For LiveKit, we return the WebSocket URL with the token
        # This can be used directly with LiveKit client libraries
        uri = f"{stream_info.liveKitURL}?token={stream_info.userToken}"

        LOGGER.debug("Generated LiveKit WebRTC URI for camera %s", self.name)
        return uri

    def get_livekit_connection_info(self, stream_info: LiveViewResponse) -> dict[str, str]:
        """Get LiveKit connection information as a dictionary.

        Args:
            stream_info: The LiveViewResponse from async_get_webrtc_stream_info()

        Returns:
            Dictionary with LiveKit connection details
        """
        return {
            "url": stream_info.liveKitURL,
            "token": stream_info.userToken,
            "camera_status": stream_info.cameraStatus
        }

    async def async_get_webrtc_uri(self) -> str:
        """Get a WebRTC URI for outdoor camera streaming.

        This is a convenience method that combines getting stream info
        and generating the URI in one call.

        Returns:
            A LiveKit WebRTC URL for streaming
        """
        stream_info = await self.async_get_webrtc_stream_info()
        return self.get_webrtc_uri(stream_info)

    async def async_get_livekit_connection_info(self) -> dict[str, str]:
        """Get LiveKit connection information for outdoor camera streaming.

        This is a convenience method for getting LiveKit connection details
        in a format suitable for LiveKit client libraries.

        Returns:
            Dictionary with LiveKit connection details
        """
        stream_info = await self.async_get_webrtc_stream_info()
        return self.get_livekit_connection_info(stream_info)

    async def async_stream_url(
        self,
        format_type: StreamFormat = StreamFormat.FLV,
        width: int = DEFAULT_VIDEO_WIDTH,
        audio_encoding: str = DEFAULT_AUDIO_ENCODING,
        auto_wake: bool = True,
        **kwargs: Any,
    ) -> str:
        """Return the camera stream URL with automatic wake-up (like SimpliSafe app).

        Args:
            format_type: The stream format (FLV or MJPEG).
            width: The video width.
            audio_encoding: The audio encoding (for FLV streams).
            auto_wake: Whether to automatically wake up outdoor cameras.
            kwargs: Additional parameters.

        Returns:
            The camera stream URL.
            
        Raises:
            RuntimeError: If auto_wake is True and wake-up fails for outdoor camera.
        """
        # Wake up camera if needed (like SimpliSafe app does)
        if auto_wake and self.is_outdoor_camera:
            wake_success = await self.async_ensure_awake()
            if not wake_success:
                raise RuntimeError(
                    f"Failed to wake up outdoor camera {self.name} for streaming. "
                    f"Camera may be offline or have connectivity issues."
                )

        return self.stream_url(format_type, width, audio_encoding, **kwargs)

    async def async_snapshot_url(
        self,
        width: int = DEFAULT_SNAPSHOT_WIDTH,
        auto_wake: bool = True,
        **kwargs: Any,
    ) -> str:
        """Return the camera snapshot URL with automatic wake-up (like SimpliSafe app).

        Args:
            width: The snapshot width.
            auto_wake: Whether to automatically wake up outdoor cameras.
            kwargs: Additional parameters.

        Returns:
            The camera snapshot URL.
            
        Raises:
            RuntimeError: If auto_wake is True and wake-up fails for outdoor camera.
        """
        # Wake up camera if needed (like SimpliSafe app does)
        if auto_wake and self.is_outdoor_camera:
            wake_success = await self.async_ensure_awake()
            if not wake_success:
                raise RuntimeError(
                    f"Failed to wake up outdoor camera {self.name} for snapshot. "
                    f"Camera may be offline or have connectivity issues."
                )

        return self.snapshot_url(width, **kwargs)
