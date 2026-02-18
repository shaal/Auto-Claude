"""In-process pub/sub event bus for real-time updates."""

from typing import Callable

EventCallback = Callable[[dict], None]


class EventBus:
    """Simple pub/sub for broadcasting events to WebSocket clients."""

    def __init__(self):
        self._subscribers: list[EventCallback] = []

    def subscribe(self, callback: EventCallback) -> Callable[[], None]:
        """Subscribe to all events. Returns an unsubscribe function."""
        self._subscribers.append(callback)
        def unsubscribe():
            if callback in self._subscribers:
                self._subscribers.remove(callback)
        return unsubscribe

    def publish(self, event: dict) -> None:
        """Publish an event to all subscribers."""
        for cb in self._subscribers[:]:  # Copy to allow modification during iteration
            try:
                cb(event)
            except Exception:
                pass  # Don't let one subscriber break others


# Singleton
_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus
