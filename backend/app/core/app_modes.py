"""
Mode Manager - Controls application operating modes.
Manages switching between SIMULATION, REALTIME, and HYBRID modes,
validates data source compatibility, and triggers lifecycle callbacks.
"""

from typing import Dict, Any, Callable, List
import logging

from app.config import AppMode, DataSourceType, settings

logger = logging.getLogger(__name__)


class ModeManager:
    """
    Manages application modes and switches between them.
    Ensures correct initialization based on selected mode.
    """

    def __init__(self):
        self.current_mode: AppMode = settings.app_mode
        self.data_source: DataSourceType = settings.data_source
        self.mode_config: Dict[AppMode, Dict[str, Any]] = (
            self._initialize_mode_config()
        )
        self.mode_callbacks: Dict[str, List[Callable]] = {
            "on_mode_change": [],
            "on_data_source_change": [],
        }

    def _initialize_mode_config(self) -> Dict[AppMode, Dict[str, Any]]:
        """Initialize configuration for each mode."""
        return {
            AppMode.SIMULATION: {
                "name": "Simulation Mode",
                "description": "Generate synthetic data and test agent capabilities",
                "features": [
                    "Demand forecasting",
                    "Supplier risk simulation",
                    "Disruption injection",
                    "Agent testing",
                    "Scenario analysis",
                ],
                "data_sources": [
                    DataSourceType.KAGGLE,
                    DataSourceType.MANUAL,
                    DataSourceType.CSV,
                ],
                "auto_simulation": True,
                "event_replay": True,
                "time_acceleration": True,
            },
            AppMode.REALTIME: {
                "name": "Real-Time Mode",
                "description": "Connect to live data sources and make real-time decisions",
                "features": [
                    "Live data ingestion",
                    "Real-time forecasting",
                    "Live risk assessment",
                    "Immediate agent responses",
                    "Production monitoring",
                ],
                "data_sources": [
                    DataSourceType.KAFKA,
                    DataSourceType.API,
                    DataSourceType.DATABASE,
                    DataSourceType.CSV,
                ],
                "auto_simulation": False,
                "event_replay": False,
                "time_acceleration": False,
            },
            AppMode.HYBRID: {
                "name": "Hybrid Mode",
                "description": "Combine historical data with real-time inputs",
                "features": [
                    "Historical + live data",
                    "Predictive + reactive",
                    "Simulation with live updates",
                    "Agent learning from real data",
                    "Backtesting on real events",
                ],
                "data_sources": [
                    DataSourceType.KAGGLE,
                    DataSourceType.KAFKA,
                    DataSourceType.API,
                    DataSourceType.CSV,
                    DataSourceType.MANUAL,
                ],
                "auto_simulation": False,
                "event_replay": True,
                "time_acceleration": True,
            },
        }

    def get_mode_info(self) -> Dict[str, Any]:
        """Get current mode configuration."""
        mode_config = self.mode_config[self.current_mode]
        return {
            "current_mode": self.current_mode.value,
            "data_source": self.data_source.value,
            **mode_config,
            "data_sources": [ds.value for ds in mode_config["data_sources"]],
            "settings": {
                "simulation_enabled": settings.simulation_enabled,
                "auto_validate_data": settings.auto_validate_data,
                "preload_kaggle_data": settings.preload_kaggle_data,
            },
        }

    def can_use_data_source(self, data_source: DataSourceType) -> bool:
        """Check if data source is compatible with current mode."""
        valid_sources = self.mode_config[self.current_mode]["data_sources"]
        return data_source in valid_sources

    def get_available_data_sources(self) -> List[str]:
        """Get list of available data sources for current mode."""
        return [
            ds.value
            for ds in self.mode_config[self.current_mode]["data_sources"]
        ]

    def switch_mode(self, new_mode: AppMode) -> Dict[str, Any]:
        """Switch application mode."""
        if new_mode == self.current_mode:
            return {
                "changed": False,
                "message": f"Already in {new_mode.value} mode",
                "mode": self.get_mode_info(),
            }

        old_mode = self.current_mode
        logger.info(f"Switching from {old_mode.value} to {new_mode.value} mode")

        # Cleanup old mode
        self._cleanup_mode(old_mode)

        # Set new mode
        self.current_mode = new_mode

        # Check if current data source is compatible
        if not self.can_use_data_source(self.data_source):
            # Auto-switch to first compatible source
            new_source = self.mode_config[new_mode]["data_sources"][0]
            logger.info(
                f"Auto-switching data source to {new_source.value} "
                f"(previous {self.data_source.value} incompatible)"
            )
            self.data_source = new_source

        # Initialize new mode
        self._initialize_mode(new_mode)

        # Trigger callbacks
        self._trigger_callbacks("on_mode_change", new_mode)

        return {
            "changed": True,
            "previous_mode": old_mode.value,
            "mode": self.get_mode_info(),
        }

    def switch_data_source(self, new_source: DataSourceType) -> Dict[str, Any]:
        """Switch data source."""
        if not self.can_use_data_source(new_source):
            return {
                "changed": False,
                "error": (
                    f"Data source {new_source.value} not compatible "
                    f"with {self.current_mode.value} mode"
                ),
                "available_sources": self.get_available_data_sources(),
            }

        if new_source == self.data_source:
            return {
                "changed": False,
                "message": f"Already using {new_source.value} data source",
            }

        old_source = self.data_source
        self.data_source = new_source
        logger.info(f"Switched data source from {old_source.value} to {new_source.value}")

        self._trigger_callbacks("on_data_source_change", new_source)

        return {
            "changed": True,
            "previous_source": old_source.value,
            "current_source": new_source.value,
        }

    def _initialize_mode(self, mode: AppMode):
        """Initialize mode-specific components."""
        logger.info(f"Initializing {mode.value} mode...")

    def _cleanup_mode(self, mode: AppMode):
        """Cleanup mode-specific components."""
        logger.info(f"Cleaning up {mode.value} mode...")

    def register_callback(self, event: str, callback: Callable):
        """Register callback for mode events."""
        if event in self.mode_callbacks:
            self.mode_callbacks[event].append(callback)

    def _trigger_callbacks(self, event: str, *args):
        """Trigger registered callbacks."""
        for callback in self.mode_callbacks.get(event, []):
            try:
                callback(*args)
            except Exception as e:
                logger.error(f"Error in mode callback: {e}")


# Global mode manager instance
mode_manager = ModeManager()
