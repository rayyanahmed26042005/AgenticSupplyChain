"""
Event Handlers - Route events to appropriate agents and systems.
"""

import logging
from app.events.event_models import Event, EventType

logger = logging.getLogger(__name__)


async def handle_disruption_event(event: Event):
    """Handle disruption events."""
    logger.info(f"🚨 Disruption: {event.data.get('type', 'unknown')} - severity: {event.data.get('severity', 0)}")


async def handle_demand_event(event: Event):
    """Handle demand events."""
    logger.info(f"📊 Demand event: {event.data.get('type', 'update')}")


async def handle_agent_decision_event(event: Event):
    """Handle agent decision events."""
    logger.info(f"🤖 Agent decision: {event.data.get('agent', 'unknown')} -> {event.data.get('action', 'unknown')}")


async def handle_system_event(event: Event):
    """Handle system events."""
    logger.info(f"⚙️ System: {event.data.get('message', '')}")


def register_default_handlers(event_bus):
    """Register default event handlers."""
    event_bus.subscribe(EventType.DISRUPTION, handle_disruption_event)
    event_bus.subscribe(EventType.DEMAND, handle_demand_event)
    event_bus.subscribe(EventType.AGENT_DECISION, handle_agent_decision_event)
    event_bus.subscribe(EventType.SYSTEM, handle_system_event)
    logger.info("Default event handlers registered")
