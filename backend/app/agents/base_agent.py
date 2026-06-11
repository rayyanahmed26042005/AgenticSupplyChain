"""
Base Agent - Abstract agent with perceive/decide/act/learn lifecycle.
All supply chain agents inherit from this base.
Integrates AgentMemory for short-term and long-term decision memory.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import logging

from app.agents.memory import AgentMemory

logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    IDLE = "idle"
    OBSERVING = "observing"
    DECIDING = "deciding"
    ACTING = "acting"
    LEARNING = "learning"
    ERROR = "error"


class BaseAgent(ABC):
    """Abstract base class for autonomous supply chain agents."""

    def __init__(self, agent_id: str, name: str, role: str):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.status = AgentStatus.IDLE
        self.decision_history: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, float] = {}
        self.memory = AgentMemory(short_term_capacity=50, long_term_capacity=200)
        self.created_at = datetime.now().isoformat()

    @abstractmethod
    async def perceive(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """Observe the environment and extract relevant state."""
        pass

    @abstractmethod
    async def decide(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """Make a decision based on perception."""
        pass

    @abstractmethod
    async def act(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the decision and return action result."""
        pass

    async def learn(self, outcome: Dict[str, Any]):
        """Learn from the outcome of an action — stores in long-term memory if important."""
        importance = self._assess_importance(outcome)
        self.memory.remember(
            event={
                "type": "outcome",
                "outcome": outcome,
                "agent": self.agent_id,
            },
            importance=importance,
        )

    def _assess_importance(self, outcome: Dict[str, Any]) -> float:
        """Assess the importance of an outcome for memory storage."""
        importance = 0.5
        # High importance for error states, critical actions, or conflict resolutions
        result = outcome.get("result", {})
        if result.get("status") == "error":
            importance = 0.9
        if result.get("action_taken") in ("emergency_restock", "diversify_suppliers", "split_order"):
            importance = 0.85
        if result.get("conflict_resolved"):
            importance = 0.8
        return importance

    async def run_cycle(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """Execute one full perceive-decide-act cycle with memory integration."""
        try:
            self.status = AgentStatus.OBSERVING
            perception = await self.perceive(environment)

            self.status = AgentStatus.DECIDING
            decision = await self.decide(perception)

            self.status = AgentStatus.ACTING
            result = await self.act(decision)

            # Record decision
            entry = {
                "timestamp": datetime.now().isoformat(),
                "agent": self.agent_id,
                "perception_summary": self._summarize(perception),
                "decision": decision,
                "result": result,
            }
            self.decision_history.append(entry)

            # Learn from this cycle — store in memory
            self.status = AgentStatus.LEARNING
            await self.learn(entry)

            self.status = AgentStatus.IDLE
            return entry

        except Exception as e:
            self.status = AgentStatus.ERROR
            logger.error(f"Agent {self.agent_id} cycle error: {e}")
            # Record error in memory as high-importance event
            self.memory.remember(
                event={"type": "error", "error": str(e), "agent": self.agent_id},
                importance=0.95,
            )
            return {"error": str(e), "agent": self.agent_id}

    def _summarize(self, data: Dict) -> Dict:
        """Create a brief summary of data for logging."""
        return {k: v for k, v in list(data.items())[:5]}

    def get_state(self) -> Dict[str, Any]:
        """Get agent state for monitoring."""
        memory_stats = self.memory.get_stats()
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role,
            "status": self.status.value,
            "decisions_made": len(self.decision_history),
            "memory_short_term": memory_stats["short_term_count"],
            "memory_long_term": memory_stats["long_term_count"],
            "performance": self.performance_metrics,
            "created_at": self.created_at,
        }

    def get_recent_decisions(self, count: int = 10) -> List[Dict]:
        """Get recent decisions."""
        return self.decision_history[-count:]

    def reset(self):
        """Reset agent state."""
        self.status = AgentStatus.IDLE
        self.decision_history.clear()
        self.memory.clear()
        self.performance_metrics.clear()
