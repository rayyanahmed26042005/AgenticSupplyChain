"""
Supply Chain Simulation Engine.
Generates synthetic supply chain scenarios with realistic demand patterns,
supplier disruptions, inventory dynamics, and cost calculations.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class SimulationState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class SimulationMetrics:
    timestamp: str
    day: int
    demand: float
    inventory: float
    supplier_risk: float
    on_time_delivery: float
    cost: float
    revenue: float
    stockout: bool
    demand_baseline: float
    demand_trend: float
    demand_seasonality: float
    demand_noise: float
    demand_spike: float


class SimulationEngine:
    """Main simulation engine for generating synthetic supply chain scenarios."""

    def __init__(self):
        self.state = SimulationState.IDLE
        self.current_day = 0
        self.simulation_days = 0
        self.metrics_history: List[SimulationMetrics] = []
        self.disruptions: List[Dict] = []
        self.agents_state: Dict[str, Any] = {}
        self._pause_event = asyncio.Event()
        self._pause_event.set()

    async def run_simulation(
        self,
        simulation_days: int = 90,
        num_disruptions: int = 3,
        base_demand: float = 1000,
        seed: int = 42,
    ) -> Dict[str, Any]:
        """Run full supply chain simulation."""
        np.random.seed(seed)
        self.state = SimulationState.RUNNING
        self.simulation_days = simulation_days
        self.metrics_history = []
        self.disruptions = []
        self.current_day = 0

        logger.info(
            f"Starting simulation: {simulation_days} days, "
            f"{num_disruptions} disruptions, base_demand={base_demand}"
        )

        try:
            inventory = base_demand * 0.5
            supplier_health = 1.0
            total_revenue = 0.0

            # Generate disruption schedule
            disruption_days = set(
                np.random.choice(
                    range(5, simulation_days),
                    min(num_disruptions, simulation_days - 5),
                    replace=False,
                )
            )

            for day in range(simulation_days):
                # Handle pause
                await self._pause_event.wait()
                if self.state == SimulationState.IDLE:
                    break

                await asyncio.sleep(0.005)  # Prevent blocking

                # Generate demand with realistic patterns
                demand_components = self._generate_daily_demand(
                    base_demand, day, simulation_days
                )
                daily_demand = demand_components["demand"]

                # Process disruptions
                if day in disruption_days:
                    disruption = self._create_disruption(day, supplier_health)
                    self.disruptions.append(disruption)
                    supplier_health = max(0.2, supplier_health - disruption["impact"])
                else:
                    # Natural recovery
                    supplier_health = min(1.0, supplier_health + 0.03)

                # Inventory dynamics
                fulfilled = min(daily_demand, inventory)
                stockout = fulfilled < daily_demand
                inventory -= fulfilled

                # Replenishment (affected by supplier health)
                if inventory < base_demand * 0.3:
                    replenishment = base_demand * np.random.uniform(0.3, 0.6) * supplier_health
                    inventory += replenishment

                # Revenue & cost
                unit_price = 100
                revenue = fulfilled * unit_price
                total_revenue += revenue
                cost = self._calculate_daily_cost(daily_demand, inventory, supplier_health)
                on_time = self._calculate_on_time_delivery(supplier_health)

                metric = SimulationMetrics(
                    timestamp=(datetime.now() + timedelta(days=day)).isoformat(),
                    day=int(day),
                    demand=float(round(daily_demand, 2)),
                    inventory=float(round(max(0, inventory), 2)),
                    supplier_risk=float(round(1.0 - supplier_health, 3)),
                    on_time_delivery=float(round(on_time, 3)),
                    cost=float(round(cost, 2)),
                    revenue=float(round(revenue, 2)),
                    stockout=bool(stockout),
                    demand_baseline=float(round(demand_components["baseline"], 2)),
                    demand_trend=float(round(demand_components["trend"], 2)),
                    demand_seasonality=float(round(demand_components["seasonality"], 2)),
                    demand_noise=float(round(demand_components["noise"], 2)),
                    demand_spike=float(round(demand_components["spike"], 2)),
                )
                self.metrics_history.append(metric)
                self.current_day = day

            self.state = SimulationState.COMPLETED
            return self._compile_results()

        except Exception as e:
            logger.error(f"Simulation error: {e}")
            self.state = SimulationState.ERROR
            raise

    def _generate_daily_demand(
        self, base: float, day: int, total_days: int
    ) -> Dict[str, float]:
        """Generate realistic daily demand with trend, seasonality, and spikes."""
        trend = base * 0.2 * (day / total_days)
        weekly_seasonality = base * 0.15 * np.sin(day * 2 * np.pi / 7)
        monthly_seasonality = base * 0.1 * np.sin(day * 2 * np.pi / 30)
        noise = np.random.normal(0, base * 0.05)
        spike = base * np.random.uniform(0.2, 0.5) if np.random.random() < 0.08 else 0
        demand = base + trend + weekly_seasonality + monthly_seasonality + noise + spike
        actual_demand = max(50, demand)
        return {
            "demand": float(actual_demand),
            "baseline": float(base),
            "trend": float(trend),
            "seasonality": float(weekly_seasonality + monthly_seasonality),
            "noise": float(noise),
            "spike": float(spike),
        }

    def _create_disruption(self, day: int, current_health: float) -> Dict:
        """Create a supply chain disruption event."""
        types = [
            {"type": "supplier_failure", "impact": 0.3, "desc": "Key supplier production halt"},
            {"type": "transportation_delay", "impact": 0.2, "desc": "Shipping route disruption"},
            {"type": "quality_issue", "impact": 0.15, "desc": "Batch quality recall"},
            {"type": "demand_spike", "impact": 0.1, "desc": "Unexpected demand surge"},
            {"type": "natural_disaster", "impact": 0.4, "desc": "Natural disaster affecting supply"},
            {"type": "port_congestion", "impact": 0.25, "desc": "Port congestion delays"},
        ]
        disruption = types[np.random.randint(0, len(types))]
        severity = np.random.uniform(0.3, 0.9)

        return {
            "day": int(day),
            "type": disruption["type"],
            "description": disruption["desc"],
            "severity": float(round(severity, 2)),
            "impact": float(round(disruption["impact"] * severity, 3)),
            "resolved": False,
        }

    def _calculate_on_time_delivery(self, supplier_health: float) -> float:
        """Calculate on-time delivery rate."""
        base_rate = 0.95
        degradation = (1.0 - supplier_health) * 0.3
        randomness = np.random.uniform(-0.03, 0.03)
        return max(0.5, min(1.0, base_rate - degradation + randomness))

    def _calculate_daily_cost(
        self, demand: float, inventory: float, supplier_health: float
    ) -> float:
        """Calculate daily supply chain cost."""
        procurement = demand * 50
        holding = inventory * 2
        risk_premium = (1.0 - supplier_health) * demand * 20
        expediting = demand * 15 if supplier_health < 0.5 else 0
        return procurement + holding + risk_premium + expediting

    def _compile_results(self) -> Dict[str, Any]:
        """Compile simulation results into summary."""
        records = [asdict(m) for m in self.metrics_history]
        df = pd.DataFrame(records)

        return {
            "status": "completed",
            "days": int(self.simulation_days),
            "disruptions": self.disruptions,
            "disruption_count": int(len(self.disruptions)),
            "metrics": records,
            "statistics": {
                "avg_demand": float(round(df["demand"].mean(), 2)),
                "max_demand": float(round(df["demand"].max(), 2)),
                "avg_inventory": float(round(df["inventory"].mean(), 2)),
                "min_inventory": float(round(df["inventory"].min(), 2)),
                "avg_supplier_risk": float(round(df["supplier_risk"].mean(), 3)),
                "max_supplier_risk": float(round(df["supplier_risk"].max(), 3)),
                "avg_on_time": float(round(df["on_time_delivery"].mean(), 3)),
                "min_on_time": float(round(df["on_time_delivery"].min(), 3)),
                "total_cost": float(round(df["cost"].sum(), 2)),
                "total_revenue": float(round(df["revenue"].sum(), 2)),
                "profit": float(round(df["revenue"].sum() - df["cost"].sum(), 2)),
                "stockout_days": int(df["stockout"].sum()),
                "stockout_rate": float(round(df["stockout"].mean() * 100, 1)),
            },
        }

    def pause(self):
        """Pause simulation."""
        if self.state == SimulationState.RUNNING:
            self._pause_event.clear()
            self.state = SimulationState.PAUSED
            logger.info("Simulation paused")

    def resume(self):
        """Resume simulation."""
        if self.state == SimulationState.PAUSED:
            self.state = SimulationState.RUNNING
            self._pause_event.set()
            logger.info("Simulation resumed")

    def stop(self):
        """Stop simulation."""
        self.state = SimulationState.IDLE
        self._pause_event.set()
        logger.info("Simulation stopped")

    def get_state(self) -> Dict[str, Any]:
        """Get current simulation state."""
        return {
            "state": self.state.value,
            "current_day": self.current_day,
            "total_days": self.simulation_days,
            "progress": round(
                (self.current_day / max(1, self.simulation_days)) * 100, 1
            ),
            "disruptions_count": len(self.disruptions),
            "metrics_collected": len(self.metrics_history),
        }


# User/Guest isolated simulation engines registry
_engines: Dict[str, SimulationEngine] = {}


def get_simulation_engine(owner_id: str) -> SimulationEngine:
    """Retrieve a SimulationEngine instance scoped to a specific owner_id."""
    if owner_id not in _engines:
        _engines[owner_id] = SimulationEngine()
    return _engines[owner_id]
