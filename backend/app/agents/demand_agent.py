"""
Demand Agent - Forecasts demand, triggers reorder alerts, adjusts safety stock.
Integrates with DemandForecaster ML model for Holt's exponential smoothing.
"""

from typing import Dict, Any
import numpy as np
import logging

from app.agents.base_agent import BaseAgent
from app.config import settings
from app.utils.llm_helper import call_groq_llm

logger = logging.getLogger(__name__)


class DemandAgent(BaseAgent):
    """Agent responsible for demand forecasting and inventory optimization."""

    def __init__(self):
        super().__init__(
            agent_id="demand-agent-001",
            name="Demand Forecaster",
            role="demand_forecasting",
        )
        self.forecast_horizon = 7
        self.safety_stock_multiplier = 1.5
        self.reorder_threshold = 0.3
        self._forecaster = None

    def _get_forecaster(self):
        """Lazy-load the ML DemandForecaster."""
        if self._forecaster is None:
            try:
                from app.ml.demand_forecaster import DemandForecaster
                self._forecaster = DemandForecaster()
            except Exception as e:
                logger.warning(f"Could not load DemandForecaster: {e}")
        return self._forecaster

    async def perceive(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """Extract demand-relevant data from environment."""
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

        # Attempt ML-based forecasting
        ml_forecast_result = None
        forecaster = self._get_forecaster()
        if forecaster and len(demands) >= 3:
            try:
                forecaster.fit(demands)
                ml_forecast_result = forecaster.forecast(horizon=self.forecast_horizon)
                if "error" in ml_forecast_result:
                    ml_forecast_result = None
            except Exception as e:
                logger.debug(f"ML forecast failed: {e}")

        # Extract lead time from metrics if present, otherwise default to 7 days
        lead_times = [safe_val(m.get("lead_time_days", m.get("lead_time")), None) for m in recent]
        lead_times = [l for l in lead_times if l is not None]
        lead_time = float(lead_times[-1]) if lead_times else 7.0

        return {
            "recent_demands": demands,
            "recent_inventories": inventories,
            "avg_demand": np.mean(demands) if demands else 0,
            "demand_trend": self._calculate_trend(demands),
            "current_inventory": inventories[-1] if inventories else 0,
            "demand_volatility": np.std(demands) if len(demands) > 1 else 0,
            "ml_forecast": ml_forecast_result,
            "lead_time": lead_time,
        }

    async def decide(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """Make demand-related decisions using ML forecast when available."""
        avg_demand = perception["avg_demand"]
        trend = perception["demand_trend"]
        volatility = perception["demand_volatility"]
        current_inventory = perception["current_inventory"]
        ml_forecast = perception.get("ml_forecast")
        lead_time = perception.get("lead_time", 7.0)

        # Use ML forecast if available, otherwise fall back to trend-adjusted average
        forecast_method = "trend_adjusted_average"
        forecast_lower = 0.0
        forecast_upper = 0.0
        if ml_forecast and "forecast" in ml_forecast:
            forecast_values = ml_forecast["forecast"]
            forecast = float(np.mean(forecast_values))
            forecast_method = ml_forecast.get("method", "holt_exponential_smoothing")
            # Get confidence from ML model's prediction interval width
            if ml_forecast.get("confidence_lower") and ml_forecast.get("confidence_upper"):
                forecast_lower = float(np.mean(ml_forecast["confidence_lower"]))
                forecast_upper = float(np.mean(ml_forecast["confidence_upper"]))
                interval_width = np.mean([
                    u - l for u, l in zip(ml_forecast["confidence_upper"], ml_forecast["confidence_lower"])
                ])
                ml_confidence = max(0.4, 1.0 - (interval_width / (forecast + 1)))
            else:
                ml_confidence = 0.7
                forecast_lower = forecast * 0.85
                forecast_upper = forecast * 1.15
        else:
            forecast = avg_demand * (1 + trend * 0.1)
            ml_confidence = None
            forecast_lower = forecast * 0.8
            forecast_upper = forecast * 1.2

        # Calculate recommended safety stock
        safety_stock = volatility * self.safety_stock_multiplier

        # Determine reorder point: ROP = (Forecast * Lead Time) + Safety Stock
        reorder_point = (forecast * lead_time) + safety_stock

        # Decision
        should_reorder = current_inventory < reorder_point

        # Confidence — ML-based or rule-based
        if ml_confidence is not None:
            confidence = round(min(0.95, ml_confidence), 2)
        else:
            confidence = round(max(0.5, 1.0 - volatility / (avg_demand + 1)), 2)

        # Confidence label for business users
        if confidence >= 0.8:
            confidence_label = "High"
        elif confidence >= 0.6:
            confidence_label = "Medium"
        else:
            confidence_label = "Low"

        # Trend description
        trend_desc = "increasing" if trend > 0.05 else "decreasing" if trend < -0.05 else "stable"

        # Generate reasoning
        rule_reasoning = self._generate_reasoning(perception, should_reorder, forecast_method, forecast, lead_time, safety_stock, reorder_point)
        reasoning = rule_reasoning
        
        if settings.use_llm_agents:
            prompt = (
                f"As a Demand Forecasting Agent in a supply chain, analyze this state:\n"
                f"- Average Demand: {avg_demand:.2f} units/day\n"
                f"- Demand Trend: {trend_desc}\n"
                f"- Current Inventory: {current_inventory:.2f} units\n"
                f"- Lead Time: {lead_time:.1f} days\n"
                f"- Forecasted Demand during Lead Time: {forecast * lead_time:.2f} units\n"
                f"- Safety Stock Buffer target: {safety_stock:.2f} units\n"
                f"- Reorder Point (ROP = Lead Time Demand + Safety Stock): {reorder_point:.2f} units\n"
                f"Note: Since Current Inventory ({current_inventory:.2f}) is {'below' if should_reorder else 'above'} the Reorder Point ({reorder_point:.2f}), we decided to: {'REORDER' if should_reorder else 'HOLD'}.\n"
                f"Explain the rationale behind this decision in one short, professional sentence. Do NOT generate contradictory claims about Safety Stock vs Reorder Point."
            )
            llm_reasoning = await call_groq_llm(prompt, system_prompt="You are an AI Demand Forecaster Agent in a supply chain system.")
            if llm_reasoning:
                reasoning = llm_reasoning

        decision = {
            "action": "reorder" if should_reorder else "hold",
            "forecast_demand": round(forecast, 2),
            "safety_stock": round(safety_stock, 2),
            "reorder_point": round(reorder_point, 2),
            "confidence": confidence,
            "confidence_label": confidence_label,
            "trend": trend_desc,
            "forecast_method": forecast_method,
            "forecast_range_lower": round(forecast_lower, 2),
            "forecast_range_upper": round(forecast_upper, 2),
            "reasoning": reasoning,
        }

        import math
        def safe_int(v, default=0):
            if v is None or (isinstance(v, float) and math.isnan(v)):
                return default
            try:
                return int(v)
            except Exception:
                return default

        self.performance_metrics["forecast_demand"] = f"{safe_int(forecast)} units"
        self.performance_metrics["trend"] = trend_desc.capitalize()
        self.performance_metrics["forecast_confidence"] = f"{safe_int(confidence * 100)}%"
        self.performance_metrics["forecast_range"] = f"{safe_int(forecast_lower)} - {safe_int(forecast_upper)} units"
        self.performance_metrics["forecast_method"] = "Holt Double Exponential Smoothing" if "holt" in forecast_method else forecast_method.replace('_', ' ').title()

        return decision

    async def act(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Execute demand decision."""
        return {
            "action_taken": decision["action"],
            "details": decision,
            "status": "executed",
        }

    def _calculate_trend(self, values: list) -> float:
        """Calculate linear trend from time series."""
        if len(values) < 3:
            return 0.0
        x = np.arange(len(values))
        try:
            coeffs = np.polyfit(x, values, 1)
            return coeffs[0] / (np.mean(values) + 1)
        except Exception:
            return 0.0

    def _generate_reasoning(self, perception: Dict, should_reorder: bool, method: str, forecast: float, lead_time: float, safety_stock: float, reorder_point: float) -> str:
        """Generate human-readable reasoning."""
        current_inventory = perception["current_inventory"]
        method_label = "ML-based (Holt's smoothing)" if "holt" in method else "trend-adjusted average"
        if should_reorder:
            return (
                f"Current inventory ({current_inventory:.0f} units) has fallen below the Reorder Point ({reorder_point:.0f} units). "
                f"Initiating replenishment based on {method_label} forecast of {forecast:.0f} units/day over a {lead_time:.0f}-day lead time (Safety Stock: {safety_stock:.0f} units)."
            )
        else:
            return (
                f"Current inventory ({current_inventory:.0f} units) is healthy and remains above the Reorder Point ({reorder_point:.0f} units). "
                f"No replenishment action required under stable {method_label} forecast."
            )
