#!/usr/bin/env python3
"""
Python LiveKit WebRTC test for SimpliSafe cameras.
This doesn't show video but tests the connection.
"""

import asyncio
import logging
from aiohttp import ClientSession
from simplipy import API

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REFRESH_TOKEN = "FVo238-EavENCZsXqJ_NZq2Tq_n7z6c3CTfg_iHl9tH4v"

async def test_python_webrtc():
    """Test WebRTC connection using Python (no video display)."""
    
    try:
        # Try to import livekit
        import livekit
        from livekit import api, rtc
        logger.info("✅ LiveKit Python SDK available")
    except ImportError:
        logger.error("❌ LiveKit Python SDK not installed")
        logger.error("Install with: pip install livekit")
        return

    async with ClientSession() as session:
        try:
            # Get connection info
            api_client = await API.async_from_refresh_token(REFRESH_TOKEN, session=session)
            systems = await api_client.async_get_systems()
            system = list(systems.values())[0]
            
            # Find outdoor camera
            outdoor_camera = None
            for camera in system.cameras.values():
                if camera.supports_webrtc_streaming and camera.status == "online":
                    outdoor_camera = camera
                    break
            
            if not outdoor_camera:
                logger.error("No online outdoor cameras found")
                return
            
            logger.info(f"Testing camera: {outdoor_camera.name}")
            
            # Get connection info
            connection_info = await outdoor_camera.async_get_livekit_connection_info()
            
            logger.info(f"URL: {connection_info['url']}")
            logger.info(f"Token length: {len(connection_info['token'])}")
            
            # Create room and connect
            room = rtc.Room()
            
            @room.on("participant_connected")
            def on_participant_connected(participant: rtc.RemoteParticipant):
                logger.info(f"Participant connected: {participant.identity}")
            
            @room.on("track_subscribed")
            def on_track_subscribed(track: rtc.Track, publication: rtc.TrackPublication, participant: rtc.RemoteParticipant):
                logger.info(f"Track subscribed: {track.kind} from {participant.identity}")
                
            logger.info("Connecting to LiveKit room...")
            await room.connect(connection_info['url'], connection_info['token'])
            
            logger.info("✅ Successfully connected to WebRTC room!")
            logger.info(f"Room state: {room.connection_state}")
            
            # Wait a bit to see if we get any tracks
            await asyncio.sleep(10)
            
            logger.info(f"Remote participants: {len(room.remote_participants)}")
            for participant in room.remote_participants.values():
                logger.info(f"  - {participant.identity}: {len(participant.track_publications)} tracks")
            
            await room.disconnect()
            logger.info("Disconnected from room")
            
        except Exception as e:
            logger.error(f"Python WebRTC test failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_python_webrtc())
