"""
Scenario Manager.
Predefined and custom simulation scenarios.
"""

from typing import Dict, List, Any
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class Scenario:
    id: str
    name: str
    description: str
    simulation_days: int
    base_demand: float
    num_disruptions: int
    seed: int
    tags: List[str]


PREDEFINED_SCENARIOS: Dict[str, Scenario] = {
    "normal": Scenario(
        id="normal",
        name="Normal Operations",
        description="Standard supply chain with typical demand and minimal disruptions",
        simulation_days=90,
        base_demand=1000,
        num_disruptions=1,
        seed=42,
        tags=["baseline", "low-risk"],
    ),
    "high_demand": Scenario(
        id="high_demand",
        name="High Demand Season",
        description="Peak season with elevated demand and moderate disruptions",
        simulation_days=60,
        base_demand=2000,
        num_disruptions=2,
        seed=123,
        tags=["peak", "stress-test"],
    ),
    "supply_crisis": Scenario(
        id="supply_crisis",
        name="Supply Crisis",
        description="Multiple supplier failures causing severe supply constraints",
        simulation_days=120,
        base_demand=1000,
        num_disruptions=6,
        seed=456,
        tags=["crisis", "high-risk", "resilience"],
    ),
    "global_disruption": Scenario(
        id="global_disruption",
        name="Global Disruption",
        description="Major global event causing widespread supply chain disruption",
        simulation_days=180,
        base_demand=1200,
        num_disruptions=10,
        seed=789,
        tags=["global", "extreme", "pandemic"],
    ),
    "lean_operations": Scenario(
        id="lean_operations",
        name="Lean Operations",
        description="Minimal inventory with just-in-time delivery, testing efficiency",
        simulation_days=90,
        base_demand=800,
        num_disruptions=2,
        seed=321,
        tags=["lean", "efficiency", "jit"],
    ),
}


class ScenarioManager:
    """Manage simulation scenarios."""

    def __init__(self):
        self.scenarios = dict(PREDEFINED_SCENARIOS)
        self.custom_scenarios: Dict[str, Scenario] = {}

    def get_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """Get scenario by ID."""
        scenario = self.scenarios.get(scenario_id) or self.custom_scenarios.get(
            scenario_id
        )
        if not scenario:
            raise ValueError(f"Scenario not found: {scenario_id}")
        return asdict(scenario)

    def list_scenarios(self) -> List[Dict[str, Any]]:
        """List all available scenarios."""
        all_scenarios = {**self.scenarios, **self.custom_scenarios}
        return [asdict(s) for s in all_scenarios.values()]

    def create_custom_scenario(
        self,
        name: str,
        description: str,
        simulation_days: int = 90,
        base_demand: float = 1000,
        num_disruptions: int = 3,
        seed: int = 42,
        tags: List[str] = None,
    ) -> Dict[str, Any]:
        """Create a custom scenario."""
        scenario_id = name.lower().replace(" ", "_")
        scenario = Scenario(
            id=scenario_id,
            name=name,
            description=description,
            simulation_days=simulation_days,
            base_demand=base_demand,
            num_disruptions=num_disruptions,
            seed=seed,
            tags=tags or ["custom"],
        )
        self.custom_scenarios[scenario_id] = scenario
        logger.info(f"Created custom scenario: {name}")
        return asdict(scenario)

    def delete_custom_scenario(self, scenario_id: str) -> bool:
        """Delete a custom scenario."""
        if scenario_id in self.custom_scenarios:
            del self.custom_scenarios[scenario_id]
            return True
        return False
