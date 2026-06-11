"""
Coordinator Agent - Orchestrates between demand, inventory, and supplier agents, resolves conflicts.
"""

from typing import Dict, Any, List
import logging

from app.agents.base_agent import BaseAgent
from app.config import settings
from app.utils.llm_helper import call_groq_llm

logger = logging.getLogger(__name__)


class CoordinatorAgent(BaseAgent):
    """Agent that coordinates between demand, inventory, and supplier agents."""

    def __init__(self):
        super().__init__(
            agent_id="coordinator-agent-001",
            name="Supply Chain Coordinator",
            role="coordination",
        )
        self.priority_weights = {
            "stockout_prevention": 0.35,
            "cost_optimization": 0.25,
            "risk_mitigation": 0.25,
            "service_level": 0.15,
        }

    async def perceive(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """Gather inputs from all agents and environment."""
        import math
        def safe_val(v, default=0.0):
            if v is None or (isinstance(v, float) and math.isnan(v)):
                return default
            try:
                f_val = float(v)
                return default if math.isnan(f_val) else f_val
            except Exception:
                return default

        demand_decision = environment.get("demand_decision", {})
        inventory_decision = environment.get("inventory_decision", {})
        supplier_decision = environment.get("supplier_decision", {})
        metrics = environment.get("metrics", [])
        recent = metrics[-7:] if metrics else []

        return {
            # Demand inputs
            "demand_action": demand_decision.get("action", "unknown"),
            "demand_forecast": safe_val(demand_decision.get("forecast_demand"), 1000.0),
            "demand_confidence": safe_val(demand_decision.get("confidence"), 0.5),
            # Inventory inputs
            "inventory_action": inventory_decision.get("action", "unknown"),
            "inventory_coverage": inventory_decision.get("coverage_status", "ADEQUATE"),
            "inventory_restock_qty": safe_val(inventory_decision.get("restock_quantity"), 0.0),
            "inventory_eoq": safe_val(inventory_decision.get("eoq"), 0.0),
            "inventory_safety_stock": safe_val(inventory_decision.get("safety_stock"), 0.0),
            "inventory_days_of_supply": safe_val(inventory_decision.get("days_of_supply"), 0.0),
            "inventory_confidence": safe_val(inventory_decision.get("confidence"), 0.5),
            "inventory_stockout_rate": safe_val(inventory_decision.get("stockout_rate"), 0.0),
            # Supplier inputs
            "supplier_risk_level": supplier_decision.get("risk_level", "LOW"),
            "supplier_risk_score": safe_val(supplier_decision.get("current_risk_score"), 0.0),
            "supplier_otd": safe_val(supplier_decision.get("on_time_delivery_avg"), 1.0),
            "supplier_recommendations": supplier_decision.get("recommendations", []),
            "supplier_disruption_predicted": bool(supplier_decision.get("disruption_predicted", False)),
            "supplier_disruption_probability": safe_val(supplier_decision.get("disruption_probability"), 0.0),
            # Environment
            "current_cost_trend": self._get_cost_trend(recent),
            "current_otd": safe_val(recent[-1].get("on_time_delivery") if recent else 1.0, 1.0),
        }

    async def decide(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """Make coordinated decisions resolving potential multi-agent conflicts."""
        actions = []
        priority = "NORMAL"
        conflicts = []

        demand_action = perception["demand_action"]
        inv_action = perception["inventory_action"]
        inv_coverage = perception["inventory_coverage"]
        risk_level = perception["supplier_risk_level"]
        disruption_predicted = perception.get("supplier_disruption_predicted", False)

        # Determine the best reorder quantity from inventory agent replenishment planning
        reorder_qty = perception["inventory_restock_qty"]
        eoq = perception["inventory_eoq"]

        # --- Conflict Resolution ---

        # Conflict 1: Reorder needed but supplier risk is HIGH/CRITICAL
        needs_reorder = (demand_action == "reorder" or inv_action in ("restock", "emergency_restock"))
        high_risk = risk_level in ("HIGH", "CRITICAL")

        if needs_reorder and high_risk:
            conflicts.append("reorder_vs_supplier_risk")
            # Split order across suppliers to reduce risk exposure
            actions.append({
                "type": "split_order",
                "description": "Split reorder across multiple suppliers to mitigate concentrated risk",
                "quantity": reorder_qty,
                "split_ratio": [0.5, 0.3, 0.2],
            })
            priority = "HIGH"

        # Conflict 2: Inventory says restock but demand says hold
        elif inv_action in ("restock", "emergency_restock") and demand_action == "hold":
            conflicts.append("inventory_vs_demand_forecast")
            # Trust inventory agent for immediate needs, but use conservative quantity
            conservative_qty = max(reorder_qty * 0.7, perception["inventory_safety_stock"])
            actions.append({
                "type": "conservative_restock",
                "description": "Inventory below threshold despite stable demand — conservative restock to safety level",
                "quantity": round(conservative_qty, 0),
            })

        # Conflict 3: Emergency restock with predicted disruption
        elif inv_coverage == "CRITICAL" and disruption_predicted:
            conflicts.append("emergency_with_predicted_disruption")
            actions.append({
                "type": "emergency_multi_source",
                "description": "Critical inventory with predicted disruption — emergency procurement from all available sources",
                "quantity": reorder_qty,
                "urgency": "CRITICAL",
            })
            priority = "CRITICAL"

        # Conflict 4: Emergency restock requested, but supplier risk is low/medium
        elif inv_action == "emergency_restock" and not high_risk:
            conflicts.append("emergency_restock_vs_low_risk")
            actions.append({
                "type": "priority_reorder",
                "description": "Inventory Agent recommended EMERGENCY_RESTOCK. However, Supplier Risk remains LOW/MEDIUM and expedited procurement would increase costs. Selected PRIORITY_REORDER to balance service levels and procurement costs.",
                "quantity": reorder_qty,
            })
            priority = "HIGH"

        # Conflict 2: Inventory says restock (low coverage) but demand says hold
        elif inv_action == "restock" and demand_action == "hold":
            conflicts.append("inventory_vs_demand_forecast")
            # Trust inventory agent for immediate needs, but use conservative quantity
            conservative_qty = max(reorder_qty * 0.7, perception["inventory_safety_stock"])
            actions.append({
                "type": "conservative_restock",
                "description": "Inventory below threshold despite stable demand — conservative restock to safety level",
                "quantity": round(conservative_qty, 0),
            })

        # No conflict — standard processing
        elif needs_reorder:
            actions.append({
                "type": "standard_reorder",
                "description": "Proceed with EOQ-based reorder from primary supplier",
                "quantity": reorder_qty,
            })
        elif high_risk:
            # Pre-emptive safety stock build
            actions.append({
                "type": "preventive_stock",
                "description": "Build preventive safety stock due to high supplier risk",
                "quantity": round(reorder_qty * 0.5, 0) if reorder_qty > 0 else round(eoq * 0.3, 0),
            })
            priority = "HIGH"
        elif inv_action == "reduce_inventory":
            actions.append({
                "type": "inventory_reduction",
                "description": "Excess inventory detected — reduce to optimize working capital",
                "quantity": perception.get("inventory_restock_qty", 0),
            })

        # Add supplier recommendations as coordinated actions
        for rec in perception.get("supplier_recommendations", []):
            if rec.get("priority") in ("HIGH", "MEDIUM"):
                actions.append({
                    "type": rec["action"],
                    "description": rec["description"],
                    "source": "supplier_agent",
                })

        # If disruption is predicted, always add a monitoring action
        if disruption_predicted and not any(a["type"].startswith("emergency") for a in actions):
            actions.append({
                "type": "proactive_disruption_prep",
                "description": "Predicted supply disruption — activating contingency planning and backup supplier readiness",
                "source": "supplier_agent_prediction",
            })
            if priority == "NORMAL":
                priority = "ELEVATED"

        if not actions:
            actions.append({
                "type": "monitor",
                "description": "All supply chain parameters nominal. No intervention required.",
            })

        conflict_resolved = len(conflicts) > 0

        # Coordinated confidence — weighted average of agent confidences
        avg_confidence = round(np.mean([
            perception.get("demand_confidence", 0.5),
            perception.get("inventory_confidence", 0.5),
        ]), 2)

        # Determine supplier allocation percentages
        primary_allocation = 100
        backup_allocation = 0
        primary_action = actions[0] if actions else {}
        action_type = primary_action.get("type", "monitor")

        if action_type == "split_order":
            split_ratio = primary_action.get("split_ratio", [0.5, 0.3, 0.2])
            primary_allocation = int(split_ratio[0] * 100)
            backup_allocation = 100 - primary_allocation
        elif action_type == "emergency_multi_source":
            primary_allocation = 40
            backup_allocation = 60
        elif action_type in ("conservative_restock", "priority_reorder"):
            primary_allocation = 70
            backup_allocation = 30
        elif risk_level in ("HIGH", "CRITICAL"):
            primary_allocation = 60
            backup_allocation = 40
        # else standard_reorder / monitor = 100/0 (single source)

        # Expected service level — data-driven from OTD, risk, stockout
        otd_base = perception.get("supplier_otd", perception.get("current_otd", 1.0))
        risk_penalty = perception.get("supplier_risk_score", 0) * 8.0
        stockout_penalty = perception.get("inventory_stockout_rate", 0) * 15.0
        expected_service_level = round(max(50.0, min(99.9,
            otd_base * 100.0 - risk_penalty - stockout_penalty
        )), 1)

        # Final order quantity for the coordinator output
        final_order_qty = primary_action.get("quantity", reorder_qty)

        # Generate reasoning
        rule_reasoning = self._generate_reasoning(perception, actions, conflicts)
        reasoning = rule_reasoning

        if settings.use_llm_agents:
            prompt = (
                f"As a Supply Chain Coordinator Agent, analyze this multi-agent coordination state:\n"
                f"- Demand Agent: {demand_action} (forecast: {perception.get('demand_forecast', 0):.0f})\n"
                f"- Inventory Agent: {inv_action} (coverage: {inv_coverage}, DOS: {perception.get('inventory_days_of_supply', 0):.1f}d)\n"
                f"- Supplier Risk Agent: {risk_level} (disruption predicted: {disruption_predicted})\n"
                f"- Coordinated Actions: {[a['type'] for a in actions]}\n"
                f"- Conflicts Resolved: {conflicts if conflicts else 'None'}\n"
                f"- Priority: {priority}\n"
            )
            if "emergency_restock_vs_low_risk" in conflicts:
                supplier_risk_pct = perception.get("supplier_risk_score", 0.0) * 100.0
                prompt += (
                    f"- Note: Inventory Agent requested EMERGENCY_RESTOCK. However, Supplier Risk is only {supplier_risk_pct:.1f}%. "
                    f"To balance service level and high expedited shipping costs (saving 32%), you overrode this to PRIORITY_REORDER.\n"
                )
            
            prompt += "Explain the coordination rationale and override in one short, professional sentence."
            
            llm_reasoning = await call_groq_llm(
                prompt,
                system_prompt="You are an AI Supply Chain Coordinator Agent resolving conflicts in a multi-agent system."
            )
            if llm_reasoning:
                reasoning = llm_reasoning

        decision = {
            "coordinated_actions": actions,
            "priority": priority,
            "conflict_resolved": conflict_resolved,
            "conflicts_detected": conflicts,
            "action": actions[0]["type"] if actions else "monitor",
            "order_quantity": float(final_order_qty),
            "primary_supplier_allocation": primary_allocation,
            "backup_supplier_allocation": backup_allocation,
            "expected_service_level": expected_service_level,
            "coordinated_confidence": avg_confidence,
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

        self.performance_metrics["final_action"] = decision["action"].replace('_', ' ').upper()
        self.performance_metrics["order_quantity"] = f"{safe_int(final_order_qty)} units"
        self.performance_metrics["primary_supplier_allocation"] = f"{primary_allocation}%"
        self.performance_metrics["backup_supplier_allocation"] = f"{backup_allocation}%"
        self.performance_metrics["conflict_resolution"] = "Resolved" if conflict_resolved else "None"

        return decision

    async def act(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Execute coordinated decision."""
        return {
            "actions_dispatched": len(decision["coordinated_actions"]),
            "priority": decision["priority"],
            "conflict_resolved": decision["conflict_resolved"],
            "conflicts_detected": decision.get("conflicts_detected", []),
            "status": "executed",
        }

    def _get_cost_trend(self, metrics: list) -> str:
        if len(metrics) < 3:
            return "stable"
        costs = [m.get("cost", 0) for m in metrics]
        avg_first = sum(costs[:len(costs)//2]) / max(1, len(costs)//2)
        avg_second = sum(costs[len(costs)//2:]) / max(1, len(costs) - len(costs)//2)
        if avg_second > avg_first * 1.1:
            return "increasing"
        elif avg_second < avg_first * 0.9:
            return "decreasing"
        return "stable"

    def _generate_reasoning(self, perception: Dict, actions: list, conflicts: list) -> str:
        risk = perception["supplier_risk_level"]
        demand = perception["demand_action"]
        inv = perception["inventory_action"]
        inv_coverage = perception["inventory_coverage"]

        if "emergency_with_predicted_disruption" in conflicts:
            return (
                f"CRITICAL: Inventory at {inv_coverage} coverage with predicted supplier disruption. "
                f"Emergency multi-source procurement activated to prevent service outage."
            )
        elif "emergency_restock_vs_low_risk" in conflicts:
            supplier_risk_pct = perception.get("supplier_risk_score", 0.0) * 100.0
            return (
                f"Inventory Agent recommended EMERGENCY_RESTOCK. "
                f"However, Supplier Risk remains LOW ({supplier_risk_pct:.1f}%) and expedited procurement would increase costs by 32%. "
                f"Coordinator selected PRIORITY_REORDER to balance service levels and procurement costs."
            )
        elif "reorder_vs_supplier_risk" in conflicts:
            return (
                f"Conflict detected: {'Demand' if demand == 'reorder' else 'Inventory'} agent requested reorder "
                f"but supplier risk is {risk}. Resolved by splitting order across multiple suppliers."
            )
        elif "inventory_vs_demand_forecast" in conflicts:
            return (
                f"Inventory agent flagged low stock ({inv_coverage}) while demand agent sees stable demand. "
                f"Conservative restock to safety level to balance service risk and cost."
            )
        elif risk in ("HIGH", "CRITICAL"):
            return f"High supplier risk ({risk}) detected. Coordinating preventive measures across agents."
        elif inv_coverage == "CRITICAL":
            return f"Critical inventory coverage. Prioritizing emergency replenishment."
        elif demand == "reorder" or inv in ("restock", "emergency_restock"):
            return "Standard reorder approved. Supplier risk acceptable for single-source procurement."
        else:
            return "All systems nominal. No immediate coordinated action required."


# numpy needed for confidence calc
import numpy as np
