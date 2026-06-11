"""
Inventory Agent - Manages inventory optimization, reorder logic, safety stock, and days-of-supply.
Uses Economic Order Quantity (EOQ) model and integrates with ML demand forecasting.
"""

from typing import Dict, Any
import numpy as np
import logging

from app.agents.base_agent import BaseAgent
from app.config import settings
from app.utils.llm_helper import call_groq_llm

logger = logging.getLogger(__name__)


class InventoryAgent(BaseAgent):
    """Agent responsible for inventory optimization and replenishment planning."""

    def __init__(self):
        super().__init__(
            agent_id="inventory-agent-001",
            name="Inventory Optimizer",
            role="inventory_optimization",
        )
        self.holding_cost_pct = 0.02  # 2% of unit cost per day
        self.ordering_cost = 500.0  # Fixed cost per order
        self.service_level_z = 1.65  # Z-score for 95% service level
        self.lead_time_days = 7  # Default lead time

    async def perceive(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """Extract inventory-relevant data from environment."""
        import math
        def safe_val(v, default=0.0):
            if v is None or (isinstance(v, float) and math.isnan(v)):
                return default
            try:
                f_val = float(v)
                return default if math.isnan(f_val) else f_val
            except Exception:
                return default

        metrics = environment.get("metrics", [])
        recent = metrics[-14:] if len(metrics) >= 14 else metrics

        demands = [safe_val(m.get("demand"), 1000.0) for m in recent]
        inventories = [safe_val(m.get("inventory"), 500.0) for m in recent]
        costs = [safe_val(m.get("cost"), 50.0) for m in recent]
        stockouts = [bool(m.get("stockout", False)) for m in recent]

        # Extract lead time from metrics if present, otherwise default to self.lead_time_days
        lead_times = [safe_val(m.get("lead_time_days", m.get("lead_time")), None) for m in recent]
        lead_times = [l for l in lead_times if l is not None]
        lead_time = float(lead_times[-1]) if lead_times else self.lead_time_days

        # Get demand forecast from demand agent if available
        demand_decision = environment.get("demand_decision", {})
        forecast_demand = demand_decision.get("forecast_demand", 0)
        demand_confidence = demand_decision.get("confidence", 0.5)
        demand_safety_stock = demand_decision.get("safety_stock", 0)
        demand_reorder_point = demand_decision.get("reorder_point", 0)

        # Use ML forecaster if available
        ml_forecast = None
        try:
            from app.ml.demand_forecaster import DemandForecaster
            if demands and len(demands) >= 3:
                forecaster = DemandForecaster()
                forecaster.fit(demands)
                ml_result = forecaster.forecast(horizon=7)
                if "error" not in ml_result:
                    ml_forecast = ml_result
        except Exception as e:
            logger.debug(f"ML forecast not available: {e}")

        avg_demand = float(np.mean(demands)) if demands else 0
        demand_std = float(np.std(demands)) if len(demands) > 1 else 0
        current_inventory = float(inventories[-1]) if inventories else 0
        avg_cost = float(np.mean(costs)) if costs else 50.0
        stockout_count = sum(1 for s in stockouts if s)
        stockout_rate = stockout_count / max(1, len(stockouts))

        # Days of supply calculation
        days_of_supply = current_inventory / avg_demand if avg_demand > 0 else 999

        # Inventory turnover (annualized)
        total_demand = sum(demands)
        avg_inv = float(np.mean(inventories)) if inventories else 1
        turnover = (total_demand / max(1, len(demands)) * 365) / max(1, avg_inv)

        return {
            "current_inventory": current_inventory,
            "avg_demand": avg_demand,
            "demand_std": demand_std,
            "avg_unit_cost": avg_cost,
            "days_of_supply": round(days_of_supply, 1),
            "stockout_rate": round(stockout_rate, 3),
            "stockout_count": stockout_count,
            "inventory_turnover": round(turnover, 1),
            "forecast_demand": forecast_demand if forecast_demand > 0 else avg_demand,
            "demand_confidence": demand_confidence,
            "demand_safety_stock": demand_safety_stock,
            "demand_reorder_point": demand_reorder_point,
            "lead_time": lead_time,
            "ml_forecast": ml_forecast,
            "recent_inventories": inventories,
            "recent_demands": demands,
        }

    async def decide(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """Make inventory optimization decisions using EOQ, safety stock, and coverage analysis."""
        avg_demand = perception["avg_demand"]
        demand_std = perception["demand_std"]
        current_inventory = perception["current_inventory"]
        avg_cost = perception["avg_unit_cost"]
        days_of_supply = perception["days_of_supply"]
        stockout_rate = perception["stockout_rate"]
        forecast_demand = perception["forecast_demand"]
        ml_forecast = perception.get("ml_forecast")

        # --- 1. EOQ Calculation ---
        annual_demand = avg_demand * 365
        holding_cost = avg_cost * self.holding_cost_pct
        if annual_demand > 0 and holding_cost > 0:
            eoq = round(np.sqrt(
                (2 * annual_demand * self.ordering_cost) / holding_cost
            ), 0)
        else:
            eoq = round(avg_demand * 7, 0)  # Fallback: 1 week of demand

        lead_time = perception.get("lead_time", self.lead_time_days)

        # --- 2. Safety Stock (with lead time) ---
        demand_safety_stock = perception.get("demand_safety_stock", 0)
        if demand_safety_stock > 0:
            safety_stock = round(demand_safety_stock, 2)
        else:
            safety_stock = round(
                self.service_level_z * demand_std * np.sqrt(lead_time), 2
            )

        # --- 3. Reorder Point ---
        demand_reorder_point = perception.get("demand_reorder_point", 0)
        if demand_reorder_point > 0:
            reorder_point = round(demand_reorder_point, 2)
        else:
            reorder_point = round(
                (avg_demand * lead_time) + safety_stock, 2
            )

        # --- 4. ML-Enhanced Forecast Adjustment ---
        ml_adjusted_demand = avg_demand
        forecast_method = "historical_average"
        if ml_forecast and "forecast" in ml_forecast:
            ml_avg = float(np.mean(ml_forecast["forecast"]))
            if ml_avg > 0:
                ml_adjusted_demand = ml_avg
                forecast_method = ml_forecast.get("method", "holt_exponential_smoothing")

        # --- 5. Coverage Assessment ---
        coverage_status = "ADEQUATE"
        if days_of_supply < 3:
            coverage_status = "CRITICAL"
        elif days_of_supply < 7:
            coverage_status = "LOW"
        elif days_of_supply > 45:
            coverage_status = "EXCESS"

        # --- 6. Decision Logic ---
        should_restock = current_inventory < reorder_point
        
        # Target Stock Level (Order-Up-To Level using Lead Time + EOQ coverage)
        target_stock = (forecast_demand * lead_time) + safety_stock + eoq
        deficit = target_stock - current_inventory
        
        if coverage_status == "CRITICAL":
            should_restock = True
            restock_quantity = max(0, round(deficit, 0))
            action = "emergency_restock"
        elif should_restock:
            if coverage_status == "LOW":
                restock_quantity = max(0, round(deficit, 0))
            else:
                restock_quantity = max(0, round(eoq, 0))
            action = "restock"
        else:
            restock_quantity = 0
            action = "maintain"

        # Excess inventory alert
        should_reduce = coverage_status == "EXCESS"
        excess_quantity = round(current_inventory - (avg_demand * 30 + safety_stock), 0) if should_reduce else 0
        if should_reduce:
            action = "reduce_inventory"

        # Confidence based on data quality
        data_points = len(perception.get("recent_demands", []))
        confidence = round(min(0.95, 0.5 + (data_points / 28) * 0.4 + (0.05 if ml_forecast else 0)), 2)

        # Generate reasoning
        rule_reasoning = self._generate_reasoning(
            perception, action, coverage_status, eoq, restock_quantity,
            target_stock, lead_time, safety_stock, forecast_demand
        )
        reasoning = rule_reasoning

        if settings.use_llm_agents:
            prompt = (
                f"As an Inventory Optimization Agent in a supply chain, analyze this state:\n"
                f"- Current Inventory: {current_inventory:.0f} units\n"
                f"- Days of Supply: {days_of_supply:.1f} days\n"
                f"- Average Daily Demand: {avg_demand:.0f} units/day\n"
                f"- Forecast Daily Demand: {forecast_demand:.0f} units/day\n"
                f"- Lead Time: {lead_time:.1f} days\n"
                f"- Safety Stock Buffer Level: {safety_stock:.0f} units\n"
                f"- Reorder Point: {reorder_point:.0f} units\n"
                f"- Economic Order Quantity (EOQ): {eoq:.0f} units\n"
                f"- Coverage Status: {coverage_status}\n"
                f"- Target Stock Level (Lead Time Demand + Safety Stock + EOQ): {target_stock:.0f} units\n"
                f"- Recommended Order Quantity: {restock_quantity:.0f} units\n"
                f"- Decision: {action.upper()}\n"
            )
            if coverage_status in ("CRITICAL", "LOW") and restock_quantity > eoq:
                prompt += (
                    f"Note: Recommended order quantity ({restock_quantity:.0f}) is scaled up from the base mathematical EOQ ({eoq:.0f}) "
                    f"because current inventory ({current_inventory:.0f}) is below safety stock target ({safety_stock:.0f}) + lead time demand ({forecast_demand * lead_time:.0f}). "
                    f"Ordering {restock_quantity:.0f} units will restore the target stock level of {target_stock:.0f} units.\n"
                )
            
            prompt += "Explain the rationale behind this inventory decision, including the target stock and quantities, in one short, professional sentence."
            
            llm_reasoning = await call_groq_llm(
                prompt,
                system_prompt="You are an AI Inventory Optimization Agent in a supply chain system."
            )
            if llm_reasoning:
                reasoning = llm_reasoning

        decision = {
            "action": action,
            "eoq": float(eoq),
            "safety_stock": float(safety_stock),
            "reorder_point": float(reorder_point),
            "restock_quantity": float(restock_quantity),
            "excess_quantity": float(max(0, excess_quantity)) if should_reduce else 0,
            "days_of_supply": float(days_of_supply),
            "coverage_status": coverage_status,
            "inventory_turnover": float(perception["inventory_turnover"]),
            "forecast_demand": float(ml_adjusted_demand),
            "forecast_method": forecast_method,
            "stockout_rate": float(stockout_rate),
            "confidence": confidence,
            "reasoning": reasoning,
        }

        # Update performance metrics
        import math
        def safe_int(v, default=0):
            if v is None or (isinstance(v, float) and math.isnan(v)):
                return default
            try:
                return int(v)
            except Exception:
                return default

        self.performance_metrics["days_of_supply"] = f"{days_of_supply:.1f} days" if not math.isnan(days_of_supply) else "0.0 days"
        self.performance_metrics["coverage_status"] = coverage_status
        self.performance_metrics["current_inventory"] = f"{safe_int(current_inventory)} units"
        self.performance_metrics["safety_stock"] = f"{safe_int(safety_stock)} units"
        self.performance_metrics["reorder_point"] = f"{safe_int(reorder_point)} units"
        self.performance_metrics["recommended_order_quantity"] = f"{safe_int(restock_quantity)} units"

        return decision

    async def act(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Execute inventory decision."""
        return {
            "action_taken": decision["action"],
            "details": {
                "eoq": decision["eoq"],
                "safety_stock": decision["safety_stock"],
                "reorder_point": decision["reorder_point"],
                "restock_quantity": decision["restock_quantity"],
                "days_of_supply": decision["days_of_supply"],
                "coverage_status": decision["coverage_status"],
            },
            "status": "executed",
        }

    def _generate_reasoning(
        self, perception: Dict, action: str, coverage: str, eoq: float, restock_quantity: float,
        target_stock: float, lead_time: float, safety_stock: float, forecast_demand: float
    ) -> str:
        """Generate human-readable reasoning for inventory decisions."""
        dos = perception["days_of_supply"]
        current_inventory = perception["current_inventory"]

        if action == "emergency_restock":
            if restock_quantity > eoq:
                return (
                    f"CRITICAL: Current inventory is {current_inventory:.0f} units (below safety stock of {safety_stock:.0f} units). "
                    f"Order quantity scaled up to {restock_quantity:.0f} units to restore target stock level of {target_stock:.0f} units "
                    f"(Lead Time Demand: {forecast_demand * lead_time:.0f} + Safety Stock: {safety_stock:.0f} + EOQ: {eoq:.0f})."
                )
            return (
                f"CRITICAL: Only {dos:.1f} days of supply remaining. "
                f"Emergency replenishment of {restock_quantity:.0f} units required immediately to restore inventory safety levels."
            )
        elif action == "restock":
            if restock_quantity > eoq:
                return (
                    f"Low stock detected ({dos:.1f} days of supply). "
                    f"Order quantity scaled up to {restock_quantity:.0f} units to restore target stock level of {target_stock:.0f} units "
                    f"(Lead Time Demand: {forecast_demand * lead_time:.0f} + Safety Stock: {safety_stock:.0f} + EOQ: {eoq:.0f})."
                )
            return (
                f"Inventory below reorder point. Initiating standard economic replenishment order of {restock_quantity:.0f} units "
                f"to restore safety stock buffer."
            )
        elif action == "reduce_inventory":
            return (
                f"Excess inventory detected ({dos:.1f} days of supply). "
                f"Postponing further procurement to reduce holding costs and optimize working capital."
            )
        else:
            return (
                f"Inventory levels adequate with {dos:.1f} days of supply. "
                f"Safety stock target of {safety_stock:.0f} units is intact. No replenishment action needed."
            )
