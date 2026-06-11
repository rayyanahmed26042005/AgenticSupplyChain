"""
Simulation State Manager.
Handles simulation state persistence and replay capability in MongoDB.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from app.core.mongodb import mongodb

logger = logging.getLogger(__name__)


class SimulationStateManager:
    """Manage simulation states: save, load, and replay."""

    def __init__(self):
        self.saved_states: Dict[str, Dict[str, Any]] = {}
        self.state_history: List[Dict[str, Any]] = []

    async def save_state(
        self, simulation_id: str, state: Dict[str, Any], label: str = "", owner_id: str = "guest"
    ) -> str:
        """Save simulation state for later replay."""
        state_entry = {
            "simulation_id": simulation_id,
            "owner_id": owner_id,
            "label": label or f"State at {datetime.now().isoformat()}",
            "state": state,
            "saved_at": datetime.now().isoformat(),
        }

        # Save to local cache first
        self.saved_states[simulation_id] = state_entry
        self.state_history.append(state_entry)

        # Save to MongoDB if active
        if mongodb.db is not None:
            try:
                # Remove _id if it already exists or prevent errors
                mongo_entry = state_entry.copy()
                await mongodb.db["simulations"].update_one(
                    {"simulation_id": simulation_id, "owner_id": owner_id},
                    {"$set": mongo_entry},
                    upsert=True,
                )
                logger.info(f"Saved simulation state to MongoDB: {simulation_id} (owner: {owner_id})")
            except Exception as e:
                logger.error(f"Failed to save simulation state to MongoDB: {e}")
        else:
            logger.info(f"Saved simulation state to memory cache: {simulation_id}")

        return simulation_id

    async def load_state(self, simulation_id: str, owner_id: str = "guest") -> Optional[Dict[str, Any]]:
        """Load a saved simulation state."""
        # Try loading from MongoDB if active
        if mongodb.db is not None:
            try:
                doc = await mongodb.db["simulations"].find_one({"simulation_id": simulation_id, "owner_id": owner_id})
                if doc:
                    doc.pop("_id", None)
                    return doc
            except Exception as e:
                logger.error(f"Failed to load simulation state from MongoDB: {e}")

        # Fallback to local memory cache (verify owner_id)
        cached = self.saved_states.get(simulation_id)
        if cached and cached.get("owner_id") == owner_id:
            return cached
        return None

    async def list_saved_states(self, owner_id: str = "guest") -> List[Dict[str, Any]]:
        """List all saved simulation states."""
        if mongodb.db is not None:
            try:
                cursor = mongodb.db["simulations"].find(
                    {"owner_id": owner_id}, {"simulation_id": 1, "label": 1, "saved_at": 1}
                )
                states = []
                async for doc in cursor:
                    states.append(
                        {
                            "simulation_id": doc["simulation_id"],
                            "label": doc["label"],
                            "saved_at": doc["saved_at"],
                        }
                    )
                return states
            except Exception as e:
                logger.error(f"Failed to list simulation states from MongoDB: {e}")

        # Fallback to local memory cache
        return [
            {
                "simulation_id": sid,
                "label": s["label"],
                "saved_at": s["saved_at"],
            }
            for sid, s in self.saved_states.items()
            if s.get("owner_id") == owner_id
        ]

    async def delete_state(self, simulation_id: str, owner_id: str = "guest") -> bool:
        """Delete a saved state."""
        deleted = False

        # Delete from MongoDB if active
        if mongodb.db is not None:
            try:
                res = await mongodb.db["simulations"].delete_one({"simulation_id": simulation_id, "owner_id": owner_id})
                deleted = res.deleted_count > 0
            except Exception as e:
                logger.error(f"Failed to delete simulation state from MongoDB: {e}")

        # Always delete from local memory cache
        cached = self.saved_states.get(simulation_id)
        if cached and cached.get("owner_id") == owner_id:
            del self.saved_states[simulation_id]
            # Remove from history list
            self.state_history = [
                s for s in self.state_history if s["simulation_id"] != simulation_id
            ]
            deleted = True

        return deleted

    async def compare_states(self, id_a: str, id_b: str) -> Optional[Dict[str, Any]]:
        """Compare two simulation states."""
        state_a = await self.load_state(id_a)
        state_b = await self.load_state(id_b)

        if not state_a or not state_b:
            return None

        stats_a = state_a["state"].get("statistics", {})
        stats_b = state_b["state"].get("statistics", {})

        comparison = {}
        for key in stats_a:
            if key in stats_b:
                val_a = stats_a[key]
                val_b = stats_b[key]
                if isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)):
                    comparison[key] = {
                        "state_a": val_a,
                        "state_b": val_b,
                        "diff": round(val_b - val_a, 2),
                        "pct_change": round(
                            ((val_b - val_a) / val_a * 100) if val_a != 0 else 0,
                            1,
                        ),
                    }

        return {
            "state_a": id_a,
            "state_b": id_b,
            "comparison": comparison,
        }


# Global instance
state_manager = SimulationStateManager()
