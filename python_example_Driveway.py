# Python LiveKit Client Example
import asyncio
from livekit import Room, RoomOptions

async def stream_camera():
    room = Room()
    await room.connect(
        "wss://livestream.services.simplisafe.com:7880", 
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTA3ODc2MTUsImlzcyI6IkRSYWh1RlFQdzIyN0ZGMjNWV29qZ0d0WkNQZUw2c3VRdkF4amN5YkoiLCJtZXRhZGF0YSI6IntcInR5cGVcIjpcIlVTRVJcIixcImlkZW50aXR5XCI6XCI0Mjg3NjE2XzhmODkyYzk2ZWM5NDI1OWJkMGFiMjk2N2RiOGNiN2NmXCJ9IiwibmJmIjoxNzUwNzg3MDE1LCJzdWIiOiI0Mjg3NjE2XzhmODkyYzk2ZWM5NDI1OWJkMGFiMjk2N2RiOGNiN2NmIiwidmlkZW8iOnsiY2FuUHVibGlzaCI6dHJ1ZSwiY2FuUHVibGlzaERhdGEiOnRydWUsImNhblN1YnNjcmliZSI6dHJ1ZSwicm9vbSI6ImUwYWU0NDIzMjdkYjRkM2JhODRjNzkzZmYxMTBhNTM5XzQ1MzgwMjAiLCJyb29tSm9pbiI6dHJ1ZX19.TW_XtECn7Pz7zg8Jdas64pjIZ_5DNsuwc9AXjJYhA8k"
    )
    
    @room.on("track_subscribed")
    def on_track_subscribed(track, publication, participant):
        print(f"Subscribed to {track.kind} track")
        if track.kind == "video":
            # Handle video track
            pass
    
    # Keep connection alive
    await asyncio.sleep(60)
    await room.disconnect()

asyncio.run(stream_camera())