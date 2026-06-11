"""
Event Models - Supply chain event types.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict, field


class EventType(str, Enum):
    DEMAND = "demand"
    SUPPLY = "supply"
    DISRUPTION = "disruption"
    AGENT_DECISION = "agent_decision"
    INVENTORY = "inventory"
    SYSTEM = "system"
    SIMULATION = "simulation"


class EventPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Event:
    event_type: EventType
    source: str
    data: Dict[str, Any]
    priority: EventPriority = EventPriority.MEDIUM
    event_id: str = ""
    timestamp: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if not self.event_id:
            import uuid
            self.event_id = str(uuid.uuid4())[:8]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "source": self.source,
            "data": self.data,
            "priority": self.priority.value,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }
