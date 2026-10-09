# Change Log

_NOTE:_ this file is here for posterity; going forward, release info can be found here:
https://github.com/bachya/simplisafe-python/releases

## Unreleased

### Added
- **Camera streaming support**: Added comprehensive camera streaming functionality
  - `async_get_snapshot()`: Take snapshots from cameras
  - `async_stream_data()`: Stream live video data (FLV or MJPEG formats)
  - `async_save_stream_to_file()`: Record streams directly to files
  - `snapshot_url()`: Generate snapshot URLs
  - `stream_url()`: Generate streaming URLs with format support
  - `StreamFormat` enum for FLV and MJPEG formats
  - Support for different video resolutions and audio encodings
  - Comprehensive error handling and retry logic
- Added example scripts for camera streaming usage
- Added documentation for camera streaming features

### Enhanced
- Extended `Camera` class with streaming methods and properties
- Updated documentation to include camera streaming capabilities
- Added comprehensive tests for camera streaming functionality

## 3.0.0

- Convert library to use `asyncio`
- Added full test sweet (with 100% coverage)
- Complete overhaul of documentation
- Added Makefile with common tasks
- Added Pipfile for dependency management
- Added CodeClimate and CodeCov badging/tracking
- Updated `setup.py` to common standard
- Added contribution instructions
- Added author recognition

## 2.0.2

- Raise exception when setup doesn't complete

## 2.0.1

- Allow users without monthly monitoring to get system status

## 2.0.0

- Moving to the new API

## 1.0.5

- Get status from "Dashboard" request instead of "Locations" request because simplisafe was returning 'error'

## 1.0.4

- Don't log error when user doesn't have a freeze sensor

## 1.0.3

- Added protection against incorrect data from SimpliSafe back-end

## 1.0.2

- Return status of login corrected spelling of credentials

## 1.0.1

- Fixed logging in system

## 1.0.0

- Complete re-write

## 0.0.1

- Initial support
