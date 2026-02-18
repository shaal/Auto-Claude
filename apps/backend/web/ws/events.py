"""WebSocket endpoint for real-time event streaming."""

import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .event_bus import get_event_bus

router = APIRouter()


@router.websocket("/events")
async def websocket_events(websocket: WebSocket):
    """Stream all events to connected clients via WebSocket."""
    await websocket.accept()

    queue: asyncio.Queue[dict] = asyncio.Queue()

    def on_event(event: dict):
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            pass  # Drop events if client is too slow

    bus = get_event_bus()
    unsubscribe = bus.subscribe(on_event)

    try:
        while True:
            event = await queue.get()
            await websocket.send_text(json.dumps(event))
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        unsubscribe()
