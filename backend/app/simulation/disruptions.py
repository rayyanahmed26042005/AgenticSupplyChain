"""
Disruption Generator.
Creates supply chain disruptions with configurable severity, duration, and cascading effects.
"""

import numpy as np
from typing import Dict, List, Any
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DisruptionType(str, Enum):
    SUPPLIER_FAILURE = "supplier_failure"
    TRANSPORTATION_DELAY = "transportation_delay"
    QUALITY_ISSUE = "quality_issue"
    DEMAND_SPIKE = "demand_spike"
    NATURAL_DISASTER = "natural_disaster"
    PORT_CONGESTION = "port_congestion"
    RAW_MATERIAL_SHORTAGE = "raw_material_shortage"
    GEOPOLITICAL = "geopolitical"


DISRUPTION_PROFILES = {
    DisruptionType.SUPPLIER_FAILURE: {
        "name": "Supplier Failure",
        "description": "Key supplier halts production unexpectedly",
        "avg_duration_days": 14,
        "impact_range": (0.3, 0.7),
        "cascading": True,
        "affected_metrics": ["supplier_risk", "inventory", "on_time_delivery"],
    },
    DisruptionType.TRANSPORTATION_DELAY: {
        "name": "Transportation Delay",
        "description": "Shipping route disruption or carrier issues",
        "avg_duration_days": 7,
        "impact_range": (0.15, 0.4),
        "cascading": False,
        "affected_metrics": ["on_time_delivery", "cost"],
    },
    DisruptionType.QUALITY_ISSUE: {
        "name": "Quality Issue",
        "description": "Batch quality failure requiring recall",
        "avg_duration_days": 10,
        "impact_range": (0.1, 0.35),
        "cascading": False,
        "affected_metrics": ["inventory", "cost", "supplier_risk"],
    },
    DisruptionType.DEMAND_SPIKE: {
        "name": "Demand Spike",
        "description": "Unexpected surge in customer demand",
        "avg_duration_days": 5,
        "impact_range": (0.1, 0.3),
        "cascading": False,
        "affected_metrics": ["demand", "inventory"],
    },
    DisruptionType.NATURAL_DISASTER: {
        "name": "Natural Disaster",
        "description": "Natural disaster affecting supply chain infrastructure",
        "avg_duration_days": 21,
        "impact_range": (0.5, 0.9),
        "cascading": True,
        "affected_metrics": ["supplier_risk", "inventory", "on_time_delivery", "cost"],
    },
    DisruptionType.PORT_CONGESTION: {
        "name": "Port Congestion",
        "description": "Major port experiencing severe congestion",
        "avg_duration_days": 12,
        "impact_range": (0.2, 0.5),
        "cascading": True,
        "affected_metrics": ["on_time_delivery", "cost"],
    },
    DisruptionType.RAW_MATERIAL_SHORTAGE: {
        "name": "Raw Material Shortage",
        "description": "Critical raw material supply constraint",
        "avg_duration_days": 18,
        "impact_range": (0.25, 0.6),
        "cascading": True,
        "affected_metrics": ["inventory", "cost", "supplier_risk"],
    },
    DisruptionType.GEOPOLITICAL: {
        "name": "Geopolitical Event",
        "description": "Trade restrictions or sanctions affecting supply routes",
        "avg_duration_days": 30,
        "impact_range": (0.3, 0.8),
        "cascading": True,
        "affected_metrics": ["supplier_risk", "cost", "on_time_delivery"],
    },
}


class DisruptionGenerator:
    """Generate supply chain disruptions with realistic characteristics."""

    def __init__(self, seed: int = 42):
        self.rng = np.random.RandomState(seed)

    def generate_random(self, count: int = 1) -> List[Dict[str, Any]]:
        """Generate random disruptions."""
        disruptions = []
        types = list(DisruptionType)

        for _ in range(count):
            dtype = types[self.rng.randint(0, len(types))]
            disruptions.append(self.generate(dtype))

        return disruptions

    def generate(
        self,
        disruption_type: DisruptionType,
        severity: float = None,
        day: int = 0,
    ) -> Dict[str, Any]:
        """Generate a specific type of disruption."""
        profile = DISRUPTION_PROFILES[disruption_type]
        low, high = profile["impact_range"]

        if severity is None:
            severity = self.rng.uniform(low, high)
        severity = max(low, min(high, severity))

        duration = max(
            1, int(profile["avg_duration_days"] * self.rng.uniform(0.5, 1.5))
        )

        return {
            "id": f"DIS-{self.rng.randint(10000, 99999)}",
            "type": disruption_type.value,
            "name": profile["name"],
            "description": profile["description"],
            "severity": round(severity, 2),
            "duration_days": duration,
            "day": day,
            "cascading": profile["cascading"],
            "affected_metrics": profile["affected_metrics"],
            "status": "active",
            "created_at": datetime.now().isoformat(),
        }

    def get_disruption_types(self) -> List[Dict[str, Any]]:
        """Get all available disruption types with profiles."""
        return [
            {
                "type": dtype.value,
                "name": profile["name"],
                "description": profile["description"],
                "avg_duration": profile["avg_duration_days"],
                "impact_range": profile["impact_range"],
                "cascading": profile["cascading"],
            }
            for dtype, profile in DISRUPTION_PROFILES.items()
        ]
