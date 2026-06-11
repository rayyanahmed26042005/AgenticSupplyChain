"""
Event Bus - In-process pub/sub event system with async handlers.
"""

from typing import Dict, Any, Callable, List
from collections import defaultdict
import asyncio
import logging

from app.events.event_models import Event, EventType

logger = logging.getLogger(__name__)


class EventBus:
    """In-process pub/sub event bus."""

    def __init__(self):
        self._handlers: Dict[EventType, List[Callable]] = defaultdict(list)
        self._global_handlers: List[Callable] = []
        self.event_history: List[Dict[str, Any]] = []
        self.max_history = 1000

    def subscribe(self, event_type: EventType, handler: Callable):
        """Subscribe to events of a specific type."""
        self._handlers[event_type].append(handler)
        logger.debug(f"Handler subscribed to {event_type.value}")

    def subscribe_all(self, handler: Callable):
        """Subscribe to all events."""
        self._global_handlers.append(handler)

    async def publish(self, event: Event):
        """Publish an event to all subscribers."""
        event_dict = event.to_dict()
        self.event_history.append(event_dict)

        # Trim history
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]

        # Notify type-specific handlers
        for handler in self._handlers.get(event.event_type, []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")

        # Notify global handlers
        for handler in self._global_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Global handler error: {e}")

    def get_recent_events(self, count: int = 50, event_type: str = None) -> List[Dict]:
        """Get recent events, optionally filtered by type."""
        events = self.event_history
        if event_type:
            events = [e for e in events if e["event_type"] == event_type]
        return events[-count:]

    def clear_history(self):
        """Clear event history."""
        self.event_history.clear()


# Global event bus instance
event_bus = EventBus()
