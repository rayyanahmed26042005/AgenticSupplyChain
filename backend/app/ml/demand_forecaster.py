"""
Demand Forecaster - Time-series demand forecasting with exponential smoothing.
"""

import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DemandForecaster:
    """Forecast demand using exponential smoothing and trend analysis."""

    def __init__(self, alpha: float = 0.3, beta: float = 0.1):
        self.alpha = alpha  # Level smoothing
        self.beta = beta    # Trend smoothing
        self.history: List[float] = []
        self.forecasts: List[Dict[str, Any]] = []

    def fit(self, demand_data: List[float]):
        """Fit the model on historical demand data."""
        self.history = list(demand_data)
        logger.info(f"Fitted demand forecaster on {len(demand_data)} data points")

    def forecast(self, horizon: int = 7) -> Dict[str, Any]:
        """Generate demand forecast for given horizon."""
        if len(self.history) < 3:
            return {
                "forecast": [0] * horizon,
                "confidence_lower": [0] * horizon,
                "confidence_upper": [0] * horizon,
                "error": "Insufficient data for forecasting (need >= 3 points)",
            }

        # Double exponential smoothing (Holt's method)
        level, trend = self._holt_smoothing()

        # Generate forecasts
        forecast_values = []
        for h in range(1, horizon + 1):
            forecast_values.append(round(max(0, level + h * trend), 2))

        # Confidence intervals (widening with horizon)
        residuals = self._calculate_residuals()
        std_error = np.std(residuals) if residuals else np.std(self.history) * 0.1

        lower = [round(max(0, f - 1.96 * std_error * np.sqrt(h)), 2) for h, f in enumerate(forecast_values, 1)]
        upper = [round(f + 1.96 * std_error * np.sqrt(h), 2) for h, f in enumerate(forecast_values, 1)]

        result = {
            "forecast": forecast_values,
            "confidence_lower": lower,
            "confidence_upper": upper,
            "horizon": horizon,
            "method": "holt_exponential_smoothing",
            "current_level": round(level, 2),
            "current_trend": round(trend, 2),
            "trend_direction": "increasing" if trend > 0 else "decreasing" if trend < 0 else "flat",
            "data_points_used": len(self.history),
            "timestamp": datetime.now().isoformat(),
        }

        self.forecasts.append(result)
        return result

    def _holt_smoothing(self):
        """Apply Holt's double exponential smoothing."""
        data = self.history
        level = data[0]
        trend = data[1] - data[0]

        for val in data[1:]:
            new_level = self.alpha * val + (1 - self.alpha) * (level + trend)
            new_trend = self.beta * (new_level - level) + (1 - self.beta) * trend
            level = new_level
            trend = new_trend

        return level, trend

    def _calculate_residuals(self) -> List[float]:
        """Calculate one-step-ahead forecast residuals."""
        if len(self.history) < 4:
            return []

        data = self.history
        level = data[0]
        trend = data[1] - data[0]
        residuals = []

        for i in range(2, len(data)):
            forecast = level + trend
            residuals.append(data[i] - forecast)
            new_level = self.alpha * data[i] + (1 - self.alpha) * (level + trend)
            new_trend = self.beta * (new_level - level) + (1 - self.beta) * trend
            level = new_level
            trend = new_trend

        return residuals

    def get_accuracy_metrics(self) -> Dict[str, float]:
        """Calculate forecast accuracy metrics."""
        residuals = self._calculate_residuals()
        if not residuals:
            return {}

        residuals = np.array(residuals)
        return {
            "mae": round(np.mean(np.abs(residuals)), 2),
            "rmse": round(np.sqrt(np.mean(residuals ** 2)), 2),
            "mape": round(np.mean(np.abs(residuals / (np.array(self.history[2:]) + 1))) * 100, 2),
        }
