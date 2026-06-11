"""
Agent Memory System - Short-term working memory and long-term decision history.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import deque
import logging

logger = logging.getLogger(__name__)


class AgentMemory:
    """Memory system for agents with short-term and long-term storage."""

    def __init__(self, short_term_capacity: int = 50, long_term_capacity: int = 500):
        self.short_term: deque = deque(maxlen=short_term_capacity)
        self.long_term: List[Dict[str, Any]] = []
        self.long_term_capacity = long_term_capacity
        self.patterns: Dict[str, Any] = {}

    def remember(self, event: Dict[str, Any], importance: float = 0.5):
        """Store an event in memory."""
        memory_entry = {
            "event": event,
            "importance": importance,
            "timestamp": datetime.now().isoformat(),
        }

        self.short_term.append(memory_entry)

        # Move important memories to long-term
        if importance > 0.7:
            self.long_term.append(memory_entry)
            if len(self.long_term) > self.long_term_capacity:
                # Evict least important
                self.long_term.sort(key=lambda x: x["importance"])
                self.long_term = self.long_term[1:]

    def recall_recent(self, count: int = 10) -> List[Dict]:
        """Recall recent short-term memories."""
        return list(self.short_term)[-count:]

    def recall_important(self, count: int = 10) -> List[Dict]:
        """Recall most important long-term memories."""
        sorted_mem = sorted(self.long_term, key=lambda x: x["importance"], reverse=True)
        return sorted_mem[:count]

    def search(self, keyword: str) -> List[Dict]:
        """Search memories by keyword."""
        results = []
        for mem in list(self.short_term) + self.long_term:
            event_str = str(mem.get("event", "")).lower()
            if keyword.lower() in event_str:
                results.append(mem)
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return {
            "short_term_count": len(self.short_term),
            "long_term_count": len(self.long_term),
            "avg_importance": (
                sum(m["importance"] for m in self.long_term) / len(self.long_term)
                if self.long_term else 0
            ),
        }

    def clear(self):
        """Clear all memory."""
        self.short_term.clear()
        self.long_term.clear()
        self.patterns.clear()
