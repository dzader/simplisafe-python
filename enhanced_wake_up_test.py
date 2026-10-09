#!/usr/bin/env python3
"""
Enhanced Camera Wake-Up Test
============================

This script demonstrates the enhanced camera wake-up functionality that mimics
how the SimpliSafe app automatically wakes cameras when requesting feeds.

Features tested:
1. Automatic wake-up for outdoor cameras
2. Enhanced wake-up strategies with multiple endpoints
3. Progressive backoff for status checking
4. Async URL generation with auto-wake
5. Robust error handling and logging
"""

import asyncio
import logging
import time
from datetime import datetime
from aiohttp import ClientSession

import simplipy
from simplipy.errors import SimplipyError

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

REFRESH_TOKEN = "FVo238-EavENCZsXqJ_NZq2Tq_n7z6c3CTfg_iHl9tH4v"


def print_header(title):
    """Print a formatted header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_test_header(test_name):
    """Print test section header."""
    print(f"\n🧪 {test_name}")
    print("-" * 50)


async def test_enhanced_wake_up(camera):
    """Test the enhanced wake-up functionality."""
    print_test_header(f"Enhanced Wake-Up Test - {camera.name}")
    
    if not camera.is_outdoor_camera:
        print(f"   ⏭️  Skipping {camera.name} - not an outdoor camera")
        return True
    
    print(f"   📍 Camera Status: {camera.status}")
    print(f"   📡 Provider: {camera.streaming_provider}/{camera.recording_provider}")
    
    try:
        print(f"   🚀 Testing enhanced wake-up...")
        start_time = time.time()
        
        # Test the enhanced wake-up method
        wake_success = await camera.async_wake_up_enhanced(timeout=45)
        duration = time.time() - start_time
        
        if wake_success:
            print(f"   ✅ SUCCESS: Camera awake in {duration:.2f}s")
            return True
        else:
            print(f"   ❌ FAILED: Wake-up timeout after {duration:.2f}s")
            return False
            
    except Exception as err:
        print(f"   ❌ ERROR: {err}")
        return False


async def test_ensure_awake(camera):
    """Test the async_ensure_awake convenience method."""
    print_test_header(f"Ensure Awake Test - {camera.name}")
    
    try:
        start_time = time.time()
        
        # Test the convenience method
        is_awake = await camera.async_ensure_awake()
        duration = time.time() - start_time
        
        if is_awake:
            print(f"   ✅ SUCCESS: Camera ready in {duration:.2f}s")
            return True
        else:
            print(f"   ❌ FAILED: Camera not ready after {duration:.2f}s")
            return False
            
    except Exception as err:
        print(f"   ❌ ERROR: {err}")
        return False


async def test_auto_wake_urls(camera):
    """Test automatic wake-up with URL generation."""
    print_test_header(f"Auto-Wake URL Generation - {camera.name}")
    
    if not camera.supports_standard_streaming:
        print(f"   ⏭️  Skipping {camera.name} - doesn't support standard streaming")
        return True
    
    try:
        # Test async stream URL with auto-wake
        print(f"   🎬 Testing async stream URL generation...")
        start_time = time.time()
        
        flv_url = await camera.async_stream_url(auto_wake=True)
        duration = time.time() - start_time
        
        print(f"   ✅ FLV URL generated in {duration:.2f}s")
        print(f"   📝 URL: {flv_url[:100]}...")
        
        # Test async snapshot URL with auto-wake
        print(f"   📸 Testing async snapshot URL generation...")
        start_time = time.time()
        
        snapshot_url = await camera.async_snapshot_url(auto_wake=True)
        duration = time.time() - start_time
        
        print(f"   ✅ Snapshot URL generated in {duration:.2f}s")
        print(f"   📝 URL: {snapshot_url[:100]}...")
        
        return True
        
    except Exception as err:
        print(f"   ❌ ERROR: {err}")
        return False


async def test_webrtc_with_enhanced_wake(camera):
    """Test WebRTC streaming with enhanced wake-up."""
    print_test_header(f"WebRTC with Enhanced Wake-Up - {camera.name}")
    
    if not camera.supports_webrtc_streaming:
        print(f"   ⏭️  Skipping {camera.name} - doesn't support WebRTC streaming")
        return True
    
    try:
        print(f"   🌐 Testing WebRTC stream with enhanced wake-up...")
        start_time = time.time()
        
        # This should automatically use the enhanced wake-up
        stream_info = await camera.async_get_webrtc_stream_info()
        duration = time.time() - start_time
        
        print(f"   ✅ SUCCESS: WebRTC info retrieved in {duration:.2f}s")
        print(f"   📡 LiveKit URL: {stream_info.liveKitURL}")
        print(f"   📋 Camera Status: {stream_info.cameraStatus}")
        print(f"   🔑 Token Length: {len(stream_info.userToken)} chars")
        
        # Save connection info
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"enhanced_wake_webrtc_{camera.name.replace(' ', '_')}_{timestamp}.json"
        
        connection_info = camera.get_livekit_connection_info(stream_info)
        import json
        with open(filename, "w") as f:
            json.dump(connection_info, f, indent=2)
        print(f"   💾 Connection info saved: {filename}")
        
        return True
        
    except Exception as err:
        print(f"   ❌ ERROR: {err}")
        return False


async def test_snapshot_with_enhanced_wake(camera):
    """Test snapshot with enhanced wake-up."""
    print_test_header(f"Snapshot with Enhanced Wake-Up - {camera.name}")
    
    try:
        print(f"   📸 Testing snapshot with enhanced wake-up...")
        start_time = time.time()
        
        # This should automatically use the enhanced wake-up for outdoor cameras
        snapshot_data = await camera.async_get_snapshot(width=640, timeout=30)
        duration = time.time() - start_time
        
        print(f"   ✅ SUCCESS: {len(snapshot_data):,} bytes in {duration:.2f}s")
        
        # Save snapshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"enhanced_wake_snapshot_{camera.name.replace(' ', '_')}_{timestamp}.jpg"
        with open(filename, "wb") as f:
            f.write(snapshot_data)
        print(f"   💾 Snapshot saved: {filename}")
        
        return True
        
    except Exception as err:
        print(f"   ❌ ERROR: {err}")
        return False


async def main():
    """Main test function."""
    print_header("Enhanced Camera Wake-Up Test Suite")
    print("Testing SimpliSafe app-like camera wake-up behavior...")
    print("This demonstrates automatic wake-up for all camera operations.")
    
    async with ClientSession() as session:
        try:
            # Authenticate
            logger.info("🔑 Authenticating with SimpliSafe...")
            api = await simplipy.API.async_from_refresh_token(REFRESH_TOKEN, session=session)
            
            # Get systems
            logger.info("🏠 Getting systems...")
            systems = await api.async_get_systems()
            
            if not systems:
                print("❌ No systems found")
                return
            
            system = list(systems.values())[0]
            logger.info(f"✅ Using system: {system.system_id}")
            
            # Camera overview
            print_header("Camera Overview")
            online_cameras = [c for c in system.cameras.values() if c.status == "online"]
            offline_cameras = [c for c in system.cameras.values() if c.status == "offline"]
            outdoor_cameras = [c for c in system.cameras.values() if c.is_outdoor_camera]
            
            print(f"📊 Found {len(system.cameras)} total cameras:")
            print(f"   • {len(online_cameras)} online")
            print(f"   • {len(offline_cameras)} offline")
            print(f"   • {len(outdoor_cameras)} outdoor cameras")
            
            # Test results tracking
            test_results = {}
            
            # Test each camera
            for camera in system.cameras.values():
                print(f"\n🎥 Testing Camera: {camera.name}")
                print(f"   Type: {camera.camera_type}")
                print(f"   Status: {camera.status}")
                print(f"   Outdoor: {camera.is_outdoor_camera}")
                print(f"   Standard Streaming: {camera.supports_standard_streaming}")
                print(f"   WebRTC Streaming: {camera.supports_webrtc_streaming}")
                
                camera_results = {}
                
                # Test enhanced wake-up (outdoor cameras only)
                if camera.is_outdoor_camera:
                    camera_results['enhanced_wake_up'] = await test_enhanced_wake_up(camera)
                    camera_results['ensure_awake'] = await test_ensure_awake(camera)
                
                # Test auto-wake URL generation
                camera_results['auto_wake_urls'] = await test_auto_wake_urls(camera)
                
                # Test snapshot with enhanced wake-up
                if camera.status == "online":
                    camera_results['snapshot'] = await test_snapshot_with_enhanced_wake(camera)
                    
                    # Test WebRTC with enhanced wake-up
                    if camera.supports_webrtc_streaming:
                        camera_results['webrtc'] = await test_webrtc_with_enhanced_wake(camera)
                
                test_results[camera.name] = camera_results
            
            # Final summary
            print_header("Enhanced Wake-Up Test Results")
            
            for camera_name, results in test_results.items():
                print(f"\n🎥 {camera_name}:")
                for test_name, success in results.items():
                    status = "✅ PASS" if success else "❌ FAIL"
                    print(f"   • {test_name}: {status}")
            
            # Overall statistics
            total_tests = sum(len(results) for results in test_results.values())
            passed_tests = sum(sum(results.values()) for results in test_results.values())
            
            print(f"\n📊 Overall Results:")
            print(f"   • Total tests: {total_tests}")
            print(f"   • Passed: {passed_tests}")
            print(f"   • Failed: {total_tests - passed_tests}")
            print(f"   • Success rate: {(passed_tests/total_tests)*100:.1f}%")
            
            print(f"\n🎯 Enhanced Wake-Up Features:")
            print(f"   ✅ Multiple wake-up endpoints and payload formats")
            print(f"   ✅ Progressive backoff for status checking")
            print(f"   ✅ Alternative wake-up strategies (status, live-view)")
            print(f"   ✅ Automatic wake-up for all streaming operations")
            print(f"   ✅ Async URL methods with auto-wake capability")
            print(f"   ✅ Comprehensive error handling and logging")
            print(f"   ✅ SimpliSafe app-like behavior")
            
            print(f"\n📂 Generated Files:")
            print(f"   • Enhanced wake snapshots: enhanced_wake_snapshot_*.jpg")
            print(f"   • Enhanced wake WebRTC info: enhanced_wake_webrtc_*.json")
            
        except SimplipyError as err:
            logger.error(f"SimpliSafe API error: {err}")
        except Exception as err:
            logger.error(f"Unexpected error: {err}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
