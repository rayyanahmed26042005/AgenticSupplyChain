"""
Event Dispatcher - Convenience methods for dispatching common events.
"""

from app.events.event_bus import event_bus
from app.events.event_models import Event, EventType, EventPriority


async def dispatch_disruption(disruption_type: str, severity: float, details: dict = None):
    """Dispatch a disruption event."""
    await event_bus.publish(Event(
        event_type=EventType.DISRUPTION,
        source="simulation",
        data={"type": disruption_type, "severity": severity, **(details or {})},
        priority=EventPriority.HIGH if severity > 0.5 else EventPriority.MEDIUM,
    ))


async def dispatch_agent_decision(agent_name: str, action: str, details: dict = None):
    """Dispatch an agent decision event."""
    await event_bus.publish(Event(
        event_type=EventType.AGENT_DECISION,
        source=agent_name,
        data={"agent": agent_name, "action": action, **(details or {})},
    ))


async def dispatch_system_event(message: str, details: dict = None):
    """Dispatch a system event."""
    await event_bus.publish(Event(
        event_type=EventType.SYSTEM,
        source="system",
        data={"message": message, **(details or {})},
    ))
