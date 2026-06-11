"""
Model Registry - Model versioning, loading, and performance tracking.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Track and manage ML models."""

    def __init__(self):
        self.models: Dict[str, Dict[str, Any]] = {}

    def register(
        self, model_name: str, model_type: str, version: str = "1.0.0",
        metrics: Dict[str, float] = None, metadata: Dict = None,
    ) -> Dict[str, Any]:
        """Register a model."""
        entry = {
            "name": model_name,
            "type": model_type,
            "version": version,
            "metrics": metrics or {},
            "metadata": metadata or {},
            "registered_at": datetime.now().isoformat(),
            "status": "active",
        }
        self.models[model_name] = entry
        logger.info(f"Registered model: {model_name} v{version}")
        return entry

    def get_model(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get model info."""
        return self.models.get(model_name)

    def list_models(self) -> List[Dict[str, Any]]:
        """List all registered models."""
        return list(self.models.values())

    def update_metrics(self, model_name: str, metrics: Dict[str, float]):
        """Update model performance metrics."""
        if model_name in self.models:
            self.models[model_name]["metrics"].update(metrics)
            self.models[model_name]["last_updated"] = datetime.now().isoformat()


# Global instance
model_registry = ModelRegistry()

# Register default models
model_registry.register(
    "demand_forecaster", "time_series", "1.0.0",
    metrics={"method": "holt_exponential_smoothing"},
)
model_registry.register(
    "risk_predictor", "classification", "1.0.0",
    metrics={"method": "weighted_multi_factor"},
)
