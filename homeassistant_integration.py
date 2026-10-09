#!/usr/bin/env python3
"""
SimpliSafe Home Assistant Integration
====================================

This script provides a Home Assistant integration for SimpliSafe cameras with WebRTC support.
It creates MQTT discovery messages and provides camera entities for Home Assistant.

Features:
- Automatic MQTT discovery
- Camera entities with snapshots and streaming
- Real-time status updates
- WebRTC streaming support via go2rtc
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import paho.mqtt.client as mqtt
from aiohttp import ClientSession

import simplipy
from simplipy.errors import SimplipyError

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SimpliSafeHomeAssistant:
    """Home Assistant integration for SimpliSafe cameras."""
    
    def __init__(self, refresh_token: str, mqtt_host: str = "localhost", mqtt_port: int = 1883,
                 mqtt_user: Optional[str] = None, mqtt_password: Optional[str] = None,
                 go2rtc_host: str = "localhost", go2rtc_port: int = 1984):
        self.refresh_token = refresh_token
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.mqtt_user = mqtt_user
        self.mqtt_password = mqtt_password
        self.go2rtc_host = go2rtc_host
        self.go2rtc_port = go2rtc_port
        
        self.api: Optional[simplipy.API] = None
        self.mqtt_client: Optional[mqtt.Client] = None
        self.device_id = "simplisafe_cameras"
        
    async def connect_mqtt(self) -> bool:
        """Connect to MQTT broker."""
        try:
            self.mqtt_client = mqtt.Client()
            
            if self.mqtt_user and self.mqtt_password:
                self.mqtt_client.username_pw_set(self.mqtt_user, self.mqtt_password)
            
            self.mqtt_client.connect(self.mqtt_host, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            
            logger.info(f"✅ Connected to MQTT broker at {self.mqtt_host}:{self.mqtt_port}")
            return True
            
        except Exception as err:
            logger.error(f"❌ MQTT connection failed: {err}")
            return False
    
    async def discover_cameras(self) -> List[dict]:
        """Discover SimpliSafe cameras."""
        async with ClientSession() as session:
            try:
                self.api = await simplipy.API.async_from_refresh_token(
                    self.refresh_token, session=session
                )
                systems = await self.api.async_get_systems()
                
                if not systems:
                    return []
                
                system = list(systems.values())[0]
                cameras = []
                
                for camera in system.cameras.values():
                    camera_info = {
                        'name': camera.name,
                        'serial': camera.serial,
                        'status': camera.status,
                        'type': str(camera.camera_type),
                        'is_outdoor': camera.is_outdoor_camera,
                        'supports_webrtc': camera.supports_webrtc_streaming,
                        'supports_standard': camera.supports_standard_streaming,
                        'streaming_provider': camera.streaming_provider,
                        'recording_provider': camera.recording_provider,
                        'camera_object': camera
                    }
                    cameras.append(camera_info)
                
                return cameras
                
            except Exception as err:
                logger.error(f"❌ Error discovering cameras: {err}")
                return []
    
    def publish_camera_discovery(self, camera: dict):
        """Publish MQTT discovery message for a camera."""
        if not self.mqtt_client:
            return
        
        camera_id = f"simplisafe_{camera['serial']}"
        device_name = f"SimpliSafe {camera['name']}"
        
        # Base device info
        device_info = {
            "identifiers": [camera_id],
            "name": device_name,
            "manufacturer": "SimpliSafe",
            "model": camera['type'],
            "serial_number": camera['serial']
        }
        
        # Camera discovery payload
        camera_config = {
            "name": device_name,
            "unique_id": camera_id,
            "device": device_info,
            "availability_topic": f"simplisafe/camera/{camera_id}/availability",
            "state_topic": f"simplisafe/camera/{camera_id}/state",
            "json_attributes_topic": f"simplisafe/camera/{camera_id}/attributes"
        }
        
        # Add streaming configuration based on camera type
        if camera['supports_webrtc']:
            # WebRTC camera (outdoor)
            stream_name = camera['name'].replace(' ', '_').lower()
            camera_config.update({
                "stream_source": f"http://{self.go2rtc_host}:{self.go2rtc_port}/api/stream.m3u8?src={stream_name}",
                "still_image_url": f"http://{self.go2rtc_host}:{self.go2rtc_port}/api/frame.jpeg?src={stream_name}"
            })
        elif camera['supports_standard']:
            # HTTP camera (indoor/doorbell) - placeholder URLs
            camera_config.update({
                "still_image_url": f"simplisafe/camera/{camera_id}/snapshot.jpg"
            })
        
        # Publish discovery message
        discovery_topic = f"homeassistant/camera/{camera_id}/config"
        self.mqtt_client.publish(
            discovery_topic,
            json.dumps(camera_config),
            retain=True
        )
        
        # Publish availability
        availability_topic = f"simplisafe/camera/{camera_id}/availability"
        availability = "online" if camera['status'] == 'online' else "offline"
        self.mqtt_client.publish(availability_topic, availability, retain=True)
        
        # Publish state
        state_topic = f"simplisafe/camera/{camera_id}/state"
        state = {
            "status": camera['status'],
            "last_updated": datetime.now().isoformat()
        }
        self.mqtt_client.publish(state_topic, json.dumps(state), retain=True)
        
        # Publish attributes
        attributes_topic = f"simplisafe/camera/{camera_id}/attributes"
        attributes = {
            "camera_type": camera['type'],
            "is_outdoor": camera['is_outdoor'],
            "supports_webrtc": camera['supports_webrtc'],
            "supports_standard": camera['supports_standard'],
            "streaming_provider": camera['streaming_provider'],
            "recording_provider": camera['recording_provider']
        }
        self.mqtt_client.publish(attributes_topic, json.dumps(attributes), retain=True)
        
        logger.info(f"✅ Published discovery for {device_name}")
    
    async def update_camera_snapshots(self, cameras: List[dict]):
        """Update snapshots for HTTP cameras."""
        for camera in cameras:
            if not camera['supports_standard'] or camera['status'] != 'online':
                continue
                
            try:
                camera_obj = camera['camera_object']
                snapshot_data = await camera_obj.async_get_snapshot(width=640, timeout=10)
                
                # Publish snapshot
                camera_id = f"simplisafe_{camera['serial']}"
                snapshot_topic = f"simplisafe/camera/{camera_id}/snapshot.jpg"
                self.mqtt_client.publish(snapshot_topic, snapshot_data)
                
                logger.info(f"📸 Updated snapshot for {camera['name']}")
                
            except Exception as err:
                logger.error(f"❌ Failed to update snapshot for {camera['name']}: {err}")
    
    async def run_integration(self):
        """Run the Home Assistant integration."""
        logger.info("🏠 Starting SimpliSafe Home Assistant Integration")
        
        # Connect to MQTT
        if not await self.connect_mqtt():
            return
        
        # Discover cameras
        cameras = await self.discover_cameras()
        if not cameras:
            logger.error("❌ No cameras found")
            return
        
        logger.info(f"📷 Found {len(cameras)} cameras")
        
        # Publish discovery messages
        for camera in cameras:
            self.publish_camera_discovery(camera)
        
        logger.info("✅ Home Assistant discovery published")
        logger.info("💡 Check Home Assistant for new camera entities")
        
        # Start update loop
        try:
            while True:
                # Update camera status and snapshots
                cameras = await self.discover_cameras()
                
                # Update availability and snapshots
                for camera in cameras:
                    camera_id = f"simplisafe_{camera['serial']}"
                    availability = "online" if camera['status'] == 'online' else "offline"
                    availability_topic = f"simplisafe/camera/{camera_id}/availability"
                    self.mqtt_client.publish(availability_topic, availability, retain=True)
                
                # Update snapshots for HTTP cameras
                await self.update_camera_snapshots(cameras)
                
                # Wait before next update
                await asyncio.sleep(30)  # Update every 30 seconds
                
        except KeyboardInterrupt:
            logger.info("🛑 Integration stopped")
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()


def generate_home_assistant_config():
    """Generate Home Assistant configuration examples."""
    config = """
# Home Assistant Configuration for SimpliSafe Cameras
# Add this to your configuration.yaml

# MQTT Broker (if not already configured)
mqtt:
  broker: localhost
  port: 1883
  # username: your_mqtt_user
  # password: your_mqtt_password

# Camera configuration (alternative to MQTT discovery)
camera:
  # WebRTC cameras (outdoor) via go2rtc
  - platform: generic
    name: SimpliSafe Driveway
    stream_source: http://localhost:1984/api/stream.m3u8?src=driveway
    still_image_url: http://localhost:1984/api/frame.jpeg?src=driveway
    verify_ssl: false
  
  # HTTP cameras (indoor/doorbell) - manual configuration
  - platform: simplisafe
    # This would require a custom SimpliSafe integration
    # Or use snapshots via automation

# Automation examples
automation:
  # Take snapshot when motion detected
  - alias: SimpliSafe Camera Snapshot
    trigger:
      platform: mqtt
      topic: simplisafe/camera/+/motion
    action:
      service: camera.snapshot
      target:
        entity_id: "{{ 'camera.simplisafe_' + trigger.topic.split('/')[-2] }}"
      data:
        filename: "/config/www/snapshots/{{ now().strftime('%Y%m%d_%H%M%S') }}.jpg"

# Lovelace dashboard card
# Add this to your dashboard:
type: picture-glance
title: SimpliSafe Cameras
camera_image: camera.simplisafe_garage
entities:
  - camera.simplisafe_garage
  - camera.simplisafe_front_door
  - camera.simplisafe_driveway
camera_view: live
"""
    
    return config


async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='SimpliSafe Home Assistant Integration')
    parser.add_argument('--refresh-token', default="FVo238-EavENCZsXqJ_NZq2Tq_n7z6c3CTfg_iHl9tH4v", help='SimpliSafe refresh token')
    parser.add_argument('--mqtt-host', default='localhost', help='MQTT broker host')
    parser.add_argument('--mqtt-port', type=int, default=1883, help='MQTT broker port')
    parser.add_argument('--mqtt-user', help='MQTT username')
    parser.add_argument('--mqtt-password', help='MQTT password')
    parser.add_argument('--go2rtc-host', default='localhost', help='go2rtc host')
    parser.add_argument('--go2rtc-port', type=int, default=1984, help='go2rtc port')
    parser.add_argument('--generate-config', action='store_true', help='Generate Home Assistant config')
    
    args = parser.parse_args()
    
    if args.generate_config:
        print("📋 Home Assistant Configuration Example:")
        print("=" * 50)
        print(generate_home_assistant_config())
        return
    
    integration = SimpliSafeHomeAssistant(
        refresh_token=args.refresh_token,
        mqtt_host=args.mqtt_host,
        mqtt_port=args.mqtt_port,
        mqtt_user=args.mqtt_user,
        mqtt_password=args.mqtt_password,
        go2rtc_host=args.go2rtc_host,
        go2rtc_port=args.go2rtc_port
    )
    
    await integration.run_integration()


if __name__ == "__main__":
    asyncio.run(main())
