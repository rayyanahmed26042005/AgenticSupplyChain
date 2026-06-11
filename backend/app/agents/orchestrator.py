"""
Agent Orchestrator - Manages agent lifecycle, coordinates decisions, aggregates results.
Runs 4 agents: Demand → Inventory → Supplier → Coordinator
"""

from typing import Dict, Any, List
import logging
from datetime import datetime

from app.agents.demand_agent import DemandAgent
from app.agents.inventory_agent import InventoryAgent
from app.agents.supplier_agent import SupplierAgent
from app.agents.coordinator_agent import CoordinatorAgent

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Manages all agents and coordinates their execution."""

    def __init__(self):
        self.demand_agent = DemandAgent()
        self.inventory_agent = InventoryAgent()
        self.supplier_agent = SupplierAgent()
        self.coordinator_agent = CoordinatorAgent()
        self.agents = {
            "demand": self.demand_agent,
            "inventory": self.inventory_agent,
            "supplier": self.supplier_agent,
            "coordinator": self.coordinator_agent,
        }
        self.orchestration_history: List[Dict[str, Any]] = []

    async def run_all_agents(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """Run all agents in sequence and coordinate their outputs."""
        timestamp = datetime.now().isoformat()

        # 1. Demand agent perceives and decides
        demand_result = await self.demand_agent.run_cycle(environment)

        # 2. Inventory agent uses demand decision for forecast-driven optimization
        inv_env = {
            **environment,
            "demand_decision": demand_result.get("decision", {}),
        }
        inventory_result = await self.inventory_agent.run_cycle(inv_env)

        # 3. Supplier agent perceives and decides
        supplier_result = await self.supplier_agent.run_cycle(environment)

        # 4. Coordinator takes all three decisions and resolves conflicts
        coord_env = {
            **environment,
            "demand_decision": demand_result.get("decision", {}),
            "inventory_decision": inventory_result.get("decision", {}),
            "supplier_decision": supplier_result.get("decision", {}),
        }
        coordinator_result = await self.coordinator_agent.run_cycle(coord_env)

        # Aggregate
        result = {
            "timestamp": timestamp,
            "agents": {
                "demand": demand_result,
                "inventory": inventory_result,
                "supplier": supplier_result,
                "coordinator": coordinator_result,
            },
            "summary": {
                "demand_action": demand_result.get("decision", {}).get("action", "unknown"),
                "inventory_action": inventory_result.get("decision", {}).get("action", "unknown"),
                "inventory_coverage": inventory_result.get("decision", {}).get("coverage_status", "unknown"),
                "supplier_risk": supplier_result.get("decision", {}).get("risk_level", "unknown"),
                "coordinated_action": coordinator_result.get("decision", {}).get("action", "unknown"),
                "conflict_resolved": coordinator_result.get("decision", {}).get("conflict_resolved", False),
            },
        }

        self.orchestration_history.append(result)
        return result

    def get_all_states(self) -> Dict[str, Any]:
        """Get state of all agents."""
        return {name: agent.get_state() for name, agent in self.agents.items()}

    def get_agent_state(self, agent_name: str) -> Dict[str, Any]:
        """Get state of a specific agent."""
        agent = self.agents.get(agent_name)
        if not agent:
            return {"error": f"Agent '{agent_name}' not found"}
        return agent.get_state()

    def get_recent_decisions(self, count: int = 10) -> List[Dict]:
        """Get recent orchestration results."""
        return self.orchestration_history[-count:]

    def get_agent_decisions(self, agent_name: str, count: int = 10) -> List[Dict]:
        """Get recent decisions from a specific agent."""
        agent = self.agents.get(agent_name)
        if not agent:
            return []
        return agent.get_recent_decisions(count)

    def reset_all(self):
        """Reset all agents."""
        for agent in self.agents.values():
            agent.reset()
        self.orchestration_history.clear()
        logger.info("All agents reset")

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary across all agents."""
        return {
            name: {
                "status": agent.status.value,
                "decisions_made": len(agent.decision_history),
                "metrics": agent.performance_metrics,
            }
            for name, agent in self.agents.items()
        }


# Global orchestrator instance
agent_orchestrator = AgentOrchestrator()

# User/Guest isolated orchestrators registry
_orchestrators: Dict[str, AgentOrchestrator] = {}


def get_agent_orchestrator(owner_id: str) -> AgentOrchestrator:
    """Retrieve an AgentOrchestrator instance scoped to a specific owner_id."""
    if owner_id not in _orchestrators:
        _orchestrators[owner_id] = AgentOrchestrator()
    return _orchestrators[owner_id]
